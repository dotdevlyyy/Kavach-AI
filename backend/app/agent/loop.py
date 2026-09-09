"""
Kavach AI — ReAct Agent Master Execution Loop
Orchestrates Plan -> Act -> Observe -> Reflect agent workflow with SSE streaming.
"""

import uuid
import asyncio
import time
from datetime import datetime, timezone
from typing import AsyncGenerator, List, Optional, Dict, Any
from loguru import logger

from app.core.sse import sse
from app.router.router import route_request
from app.agent.planner import planner
from app.agent.executor import executor
from app.agent.observer import observer
from app.core.ollama_client import ollama_client
from app.models.conversation import Conversation
from app.models.agent_task import AgentTask
from app.models.agent_step import AgentStep
from app.models.tool_call import ToolCall, ToolCallStatus
from app.schemas.common import AgentTaskStatus, StepType


class AgentLoop:
    """Master ReAct Agent execution engine."""

    async def run_agent_stream(
        self,
        task_description: str,
        conversation_id: Optional[str] = None,
        model_override: Optional[str] = None,
        system_prompt: Optional[str] = None,
        file_ids: Optional[List[str]] = None,
        max_steps: int = 10,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Runs autonomous ReAct loop and streams SSE events:
          - event: metadata
          - event: step (Plan, Act, Observe, Reflect)
          - event: tool_result
          - event: token (final response tokens)
          - event: done
        """

        def cancelled() -> bool:
            return cancel_event is not None and cancel_event.is_set()
        task_id = str(uuid.uuid4())
        conv_id = conversation_id or str(uuid.uuid4())

        # Risk-3 caps: per-step 60s, per-task 5min (docs/14_RISK_MITIGATION).
        PER_STEP_SECONDS = 60
        PER_TASK_SECONDS = 300
        task_deadline = time.monotonic() + PER_TASK_SECONDS

        # Step 1: Model Routing (attachments flow through to classifier)
        selected_model, route_metadata = await route_request(
            message=task_description,
            file_ids=file_ids,
            model_override=model_override,
        )

        # Emit metadata event
        meta_data = {
            "task_id": task_id,
            "conversation_id": conv_id,
            "model": selected_model,
            "task_type": route_metadata.task_type,
            "confidence": route_metadata.confidence,
            "reasoning": route_metadata.reasoning
        }
        yield sse("metadata", meta_data)

        # Initialize DB task record if DB is accessible
        db_task = None
        conversation = None
        try:
            conversation, _ = await Conversation.get_or_create(
                id=conv_id,
                defaults={
                    "title": task_description[:80],
                    "model_override": model_override,
                    "system_prompt": system_prompt,
                },
            )
            db_task = await AgentTask.create(
                id=task_id,
                conversation=conversation,
                description=task_description,
                max_steps=max_steps,
                status=AgentTaskStatus.PLANNING,
            )
        except Exception as e:
            logger.warning(f"DB task record initialization skipped: {e}")

        # Step 2: Planning Phase
        yield sse("step", {'type': 'plan', 'step_number': 0, 'step': 0, 'content': 'Generating strategic execution plan...'})

        plan_data = await planner.create_plan(
            task_description=task_description,
            model_name=selected_model,
            file_ids=file_ids
        )

        steps = plan_data.get("steps", [])
        goal_text = plan_data.get("goal", task_description)
        yield sse("step", {'type': 'plan', 'step_number': 0, 'step': 0, 'content': f'Plan created with {len(steps)} steps: {goal_text}'})

        if db_task:
            try:
                db_task.status = AgentTaskStatus.EXECUTING
                await db_task.save()
            except Exception as e:
                logger.warning(f"Could not mark task executing in DB: {e}")

        total_steps = 0
        final_context = ""
        output_deliverables = []

        # Step 3: Execution Loop (Plan -> Act -> Observe -> Reflect)
        step_idx = 1
        while step_idx <= min(len(steps), max_steps):
            if cancelled():
                yield sse("step", {'type': 'reflect', 'content': 'Task cancelled by user.'})
                break
            if time.monotonic() > task_deadline:
                yield sse("step", {'type': 'reflect', 'content': 'Task exceeded 5-minute cap.'})
                break
            step = steps[step_idx - 1]
            tool_name = step.get("suggested_tool", "none")
            title = step.get("title", f"Step {step_idx}")

            # Act
            act_content = f"Executing #{step_idx}: {title} (using {tool_name})"
            yield sse("step", {'type': 'act', 'step_number': step_idx, 'step': step_idx, 'tool': tool_name, 'content': act_content})

            tool_input = {"task": task_description, "step_title": title}
            step_start = datetime.now(timezone.utc)
            try:
                exec_result = await asyncio.wait_for(
                    executor.execute_step(
                        step_number=step_idx,
                        tool_name=tool_name,
                        tool_input=tool_input,
                    ),
                    timeout=PER_STEP_SECONDS,
                )
            except asyncio.TimeoutError:
                exec_result = {"success": False, "output": f"Step timed out ({PER_STEP_SECONDS}s)", "tool": tool_name}
            step_duration_ms = int((datetime.now(timezone.utc) - step_start).total_seconds() * 1000)

            # Observe
            obs = observer.observe(step_number=step_idx, result=exec_result)
            yield sse("step", {'type': 'observe', 'step_number': step_idx, 'step': step_idx, 'content': obs['observation']})

            # Tool result event (signals step completion to frontend and conveys deliverables)
            tool_res_payload = {
                "step_number": step_idx,
                "step": step_idx,
                "tool_name": tool_name,
                "tool_output": obs['observation'],
                "status": "success" if exec_result.get("success") else "error",
            }
            if exec_result.get("file_id"):
                tool_res_payload["file_id"] = exec_result["file_id"]
                output_deliverables.append(exec_result["file_id"])

            yield sse("tool_result", tool_res_payload)

            # Reflect
            yield sse("step", {'type': 'reflect', 'step_number': step_idx, 'step': step_idx, 'content': obs['reflection']})

            # Record step in DB
            if db_task:
                try:
                    await AgentStep.create(
                        agent_task=db_task,
                        step_number=step_idx,
                        type=StepType.ACT,
                        content=f"Act: {act_content}\nObserve: {obs['observation']}\nReflect: {obs['reflection']}",
                        model_used=selected_model,
                        duration_ms=step_duration_ms,
                    )
                    if effective_tool_name := exec_result.get("tool"):
                        await ToolCall.create(
                            agent_task=db_task,
                            tool_name=effective_tool_name,
                            tool_input=tool_input,
                            tool_output=str(exec_result.get("output", ""))[:4000],
                            status=ToolCallStatus.SUCCESS if exec_result.get("success") else ToolCallStatus.ERROR,
                            duration_ms=step_duration_ms,
                        )
                except Exception as e:
                    logger.warning(f"Could not save step #{step_idx} to DB: {e}")

            total_steps += 1
            final_context += f"\n- Step {step_idx} ({title}): {obs['observation']}"

            step_idx += 1

        # Step 4: Final Synthesis & Token Streaming
        base_system = (
            conversation.system_prompt
            if conversation and getattr(conversation, "system_prompt", None)
            else "You are Kavach AI, sovereign on-premise AI workbench. Summarize the final solution clearly based on step observations."
        )
        system_prompt = f"{base_system}\n\nExecution Results:\n{final_context}\n\nCRITICAL INSTRUCTION: If the execution results above indicate that a file or document was successfully generated, YOU MUST acknowledge it. DO NOT apologize or claim you cannot fulfill the request. Simply state that the requested file has been generated and is attached to the chat."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_description}
        ]

        full_final_text = ""
        try:
            async for chunk in ollama_client.chat_stream(
                model=selected_model,
                messages=messages,
                keep_alive=-1,
                options={"temperature": 0.3}
            ):
                if cancelled():
                    break
                token_text = chunk.message.content if hasattr(chunk, 'message') else chunk.get("message", {}).get("content", "")
                if token_text:
                    full_final_text += token_text
                    yield sse("token", {'content': token_text, 'token': token_text})
        except Exception as e:
            logger.warning(f"Streaming final synthesis from Ollama failed (offline): {e}")
            fallback_summary = f"\n\n**Task Completed.**\nExecuted {total_steps} agent steps.{final_context}"
            full_final_text = fallback_summary
            yield sse("token", {'content': fallback_summary, 'token': fallback_summary})

        # Update final task status in DB
        if db_task:
            try:
                db_task.status = AgentTaskStatus.CANCELLED if cancelled() else AgentTaskStatus.COMPLETED
                db_task.total_steps = total_steps
                db_task.result_summary = full_final_text
                db_task.output_files = output_deliverables
                db_task.completed_at = datetime.now(timezone.utc)
                await db_task.save()
            except Exception as e:
                logger.warning(f"Could not mark task completed in DB: {e}")

        # Done event
        done_event = {
            "task_id": task_id,
            "status": "cancelled" if cancelled() else "completed",
            "total_steps": total_steps,
            "output_files": output_deliverables
        }
        yield sse("done", done_event)


agent_loop = AgentLoop()

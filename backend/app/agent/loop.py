"""
Kavach AI — ReAct Agent Master Execution Loop
Orchestrates Plan -> Act -> Observe -> Reflect agent workflow with SSE streaming.
"""

import json
import uuid
import asyncio
from typing import AsyncGenerator, List, Optional, Dict, Any
from loguru import logger

from app.router.router import route_request
from app.agent.planner import planner
from app.agent.executor import executor
from app.agent.observer import observer
from app.core.ollama_client import ollama_client
from app.models.conversation import Conversation
from app.models.agent_task import AgentTask
from app.models.agent_step import AgentStep
from app.schemas.common import AgentTaskStatus, StepType


class AgentLoop:
    """Master ReAct Agent execution engine."""

    async def run_agent_stream(
        self,
        task_description: str,
        conversation_id: Optional[str] = None,
        model_override: Optional[str] = None,
        file_ids: Optional[List[str]] = None,
        max_steps: int = 10
    ) -> AsyncGenerator[str, None]:
        """
        Runs autonomous ReAct loop and streams SSE events:
          - event: metadata
          - event: step (Plan, Act, Observe, Reflect)
          - event: tool_result
          - event: token (final response tokens)
          - event: done
        """
        task_id = str(uuid.uuid4())
        conv_id = conversation_id or str(uuid.uuid4())

        # Step 1: Model Routing
        selected_model, route_metadata = route_request(
            message=task_description,
            model_override=model_override
        )

        # Emit metadata event
        meta_data = {
            "task_id": task_id,
            "conversation_id": conv_id,
            "model": selected_model,
            "task_type": route_metadata.task_type,
            "reasoning": route_metadata.reasoning
        }
        yield f"event: metadata\ndata: {json.dumps(meta_data)}\n\n"

        # Initialize DB task record if DB is accessible
        db_task = None
        try:
            conversation, _ = await Conversation.get_or_create(
                id=conv_id,
                defaults={"title": task_description[:80], "is_agent_mode": True}
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
        yield f"event: step\ndata: {json.dumps({'type': 'plan', 'step_number': 0, 'step': 0, 'content': 'Generating strategic execution plan...'})}\n\n"

        plan_data = await planner.create_plan(
            task_description=task_description,
            model_name=selected_model,
            file_ids=file_ids
        )

        steps = plan_data.get("steps", [])
        goal_text = plan_data.get("goal", task_description)
        yield f"event: step\ndata: {json.dumps({'type': 'plan', 'step_number': 0, 'step': 0, 'content': f'Plan created with {len(steps)} steps: {goal_text}'})}\n\n"

        if db_task:
            try:
                db_task.plan = steps
                db_task.status = AgentTaskStatus.EXECUTING
                await db_task.save()
            except Exception as e:
                logger.warning(f"Could not update task plan in DB: {e}")

        step_history = []
        final_context = ""
        output_deliverables = []

        # Step 3: Execution Loop (Plan -> Act -> Observe -> Reflect)
        step_idx = 1
        while step_idx <= min(len(steps), max_steps):
            step = steps[step_idx - 1]
            tool_name = step.get("suggested_tool", "none")
            title = step.get("title", f"Step {step_idx}")

            # Act
            act_content = f"Executing #{step_idx}: {title} (using {tool_name})"
            yield f"event: step\ndata: {json.dumps({'type': 'act', 'step_number': step_idx, 'step': step_idx, 'tool': tool_name, 'content': act_content})}\n\n"

            tool_input = {"task": task_description, "step_title": title}
            exec_result = await executor.execute_step(
                step_number=step_idx,
                tool_name=tool_name,
                tool_input=tool_input
            )

            # Observe
            obs = observer.observe(step_number=step_idx, result=exec_result)
            yield f"event: step\ndata: {json.dumps({'type': 'observe', 'step_number': step_idx, 'step': step_idx, 'content': obs['observation']})}\n\n"

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

            yield f"event: tool_result\ndata: {json.dumps(tool_res_payload)}\n\n"

            # Reflect
            yield f"event: step\ndata: {json.dumps({'type': 'reflect', 'step_number': step_idx, 'step': step_idx, 'content': obs['reflection']})}\n\n"

            # Record step in DB
            if db_task:
                try:
                    await AgentStep.create(
                        agent_task=db_task,
                        step_number=step_idx,
                        type=StepType.ACT,
                        content=f"Act: {act_content}\nObserve: {obs['observation']}\nReflect: {obs['reflection']}",
                        model_used=selected_model
                    )
                except Exception as e:
                    logger.warning(f"Could not save step #{step_idx} to DB: {e}")

            step_history.append({
                "step": step_idx,
                "title": title,
                "tool": tool_name,
                "observation": obs['observation']
            })

            final_context += f"\n- Step {step_idx} ({title}): {obs['observation']}"

            # Self-correction logic if failed
            if obs.get("requires_self_correction", False):
                yield f"event: step\ndata: {json.dumps({'type': 'reflect', 'step_number': step_idx, 'step': step_idx, 'content': 'Self-correcting failed step before proceeding...'})}\n\n"

            step_idx += 1

        # Step 4: Final Synthesis & Token Streaming
        system_prompt = (
            "You are Kavach AI, sovereign on-premise AI workbench for MRPL Refinery.\n"
            "Summarize the final solution clearly based on step observations.\n"
            f"Step Results Context: {final_context}"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_description}
        ]

        full_final_text = ""
        try:
            async for chunk in ollama_client.chat_stream(
                model=selected_model,
                messages=messages,
                options={"temperature": 0.3}
            ):
                token_text = chunk.message.content if hasattr(chunk, 'message') else chunk.get("message", {}).get("content", "")
                if token_text:
                    full_final_text += token_text
                    yield f"event: token\ndata: {json.dumps({'content': token_text, 'token': token_text})}\n\n"
        except Exception as e:
            logger.warning(f"Streaming final synthesis from Ollama failed (offline): {e}")
            fallback_summary = f"\n\n**Task Completed.**\nExecuted {len(step_history)} agent steps.{final_context}"
            full_final_text = fallback_summary
            yield f"event: token\ndata: {json.dumps({'content': fallback_summary, 'token': fallback_summary})}\n\n"

        # Update final task status in DB
        if db_task:
            try:
                db_task.status = AgentTaskStatus.COMPLETED
                db_task.total_steps = len(step_history)
                db_task.result_summary = full_final_text
                db_task.output_files = output_deliverables
                await db_task.save()
            except Exception as e:
                logger.warning(f"Could not mark task completed in DB: {e}")

        # Done event
        done_event = {
            "task_id": task_id,
            "status": "completed",
            "total_steps": len(step_history),
            "output_files": output_deliverables
        }
        yield f"event: done\ndata: {json.dumps(done_event)}\n\n"


agent_loop = AgentLoop()

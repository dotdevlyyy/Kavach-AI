"""ReAct agent execution loop with bounded work and truthful status."""

import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

from loguru import logger

from app.agent.executor import executor
from app.agent.observer import observer
from app.agent.planner import get_fallback_plan, planner
from app.core.ollama_client import ollama_client
from app.core.sse import sse
from app.models.agent_step import AgentStep
from app.models.agent_task import AgentTask
from app.models.conversation import Conversation
from app.models.tool_call import ToolCall, ToolCallStatus
from app.router.router import route_request
from app.schemas.common import AgentTaskStatus, StepType

PER_STEP_SECONDS = 60
PER_TASK_SECONDS = 300
VISION_TOOLS = {"extract_text_from_image", "analyze_engineering_diagram"}


class AgentLoop:
    async def run_agent_stream(
        self,
        task_description: str,
        conversation_id: str | None = None,
        model_override: str | None = None,
        system_prompt: str | None = None,
        file_ids: list[str] | None = None,
        max_steps: int = 10,
        cancel_event: asyncio.Event | None = None,
        task_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        task_id = task_id or str(uuid.uuid4())
        conversation_id = conversation_id or str(uuid.uuid4())
        file_ids = file_ids or []
        max_steps = max(1, min(max_steps, 10))
        deadline = time.monotonic() + PER_TASK_SECONDS

        def cancelled() -> bool:
            return cancel_event is not None and cancel_event.is_set()

        def remaining() -> float:
            return max(0.0, deadline - time.monotonic())

        db_task = None
        conversation = None
        try:
            conversation, created = await Conversation.get_or_create(
                id=conversation_id,
                defaults={
                    "title": task_description[:80],
                    "model_override": model_override,
                    "system_prompt": system_prompt,
                    "is_agent_mode": True,
                },
            )
            effective_override = model_override if created else conversation.model_override
            effective_system_prompt = system_prompt if created else conversation.system_prompt
            db_task = await AgentTask.create(
                id=task_id,
                conversation=conversation,
                description=task_description,
                max_steps=max_steps,
                status=AgentTaskStatus.PLANNING,
            )
        except Exception as exc:
            logger.exception(f"Could not initialize agent task records: {exc}")
            effective_override = model_override
            effective_system_prompt = system_prompt

        try:
            selected_model, route_metadata = await asyncio.wait_for(
                route_request(
                    message=task_description,
                    file_ids=file_ids,
                    model_override=effective_override,
                ),
                timeout=min(PER_STEP_SECONDS, remaining()),
            )
        except Exception as exc:
            logger.exception(f"Agent routing failed: {exc}")
            if db_task:
                db_task.status = AgentTaskStatus.FAILED
                db_task.completed_at = datetime.now(timezone.utc)
                await db_task.save()
            yield sse("error", {"error": "Agent routing failed"})
            yield sse("done", {"task_id": task_id, "status": "failed", "total_steps": 0})
            return

        yield sse(
            "metadata",
            {
                "task_id": task_id,
                "conversation_id": conversation_id,
                "model": selected_model,
                "task_type": route_metadata.task_type,
                "confidence": route_metadata.confidence,
                "reasoning": route_metadata.reasoning,
            },
        )

        yield sse(
            "step",
            {"type": "plan", "step_number": 0, "step": 0, "content": "Generating plan..."},
        )
        try:
            plan_data = await asyncio.wait_for(
                planner.create_plan(task_description, selected_model, file_ids),
                timeout=min(PER_STEP_SECONDS, remaining()),
            )
        except (TimeoutError, asyncio.TimeoutError):
            plan_data = get_fallback_plan(task_description)
            logger.warning("Agent planner timed out; using fallback plan")

        steps = plan_data.get("steps", [])[:max_steps]
        yield sse(
            "step",
            {
                "type": "plan",
                "step_number": 0,
                "step": 0,
                "content": (
                    f"Plan created with {len(steps)} steps: "
                    f"{plan_data.get('goal', task_description)}"
                ),
            },
        )
        if db_task:
            db_task.plan = plan_data
            db_task.status = AgentTaskStatus.EXECUTING
            await db_task.save()

        total_steps = 0
        final_context = ""
        output_files: list[str] = []
        any_failed = False
        timed_out = False

        for step_number, step in enumerate(steps, start=1):
            if cancelled():
                yield sse("step", {"type": "reflect", "content": "Task cancelled by user."})
                break
            if remaining() <= 0:
                timed_out = True
                yield sse("step", {"type": "reflect", "content": "Task exceeded 5-minute cap."})
                break

            tool_name = str(step.get("suggested_tool") or "none")
            title = str(step.get("title") or f"Step {step_number}")
            tool_input = dict(step.get("tool_input") or {})
            tool_input.update({"task": task_description, "step_title": title})
            if tool_name in VISION_TOOLS and file_ids:
                tool_input.setdefault("file_id", file_ids[0])

            yield sse(
                "step",
                {
                    "type": "act",
                    "step_number": step_number,
                    "step": step_number,
                    "tool": tool_name,
                    "content": f"Executing #{step_number}: {title} (using {tool_name})",
                },
            )
            started = time.monotonic()
            try:
                result = await asyncio.wait_for(
                    executor.execute_step(step_number, tool_name, tool_input, selected_model),
                    timeout=min(PER_STEP_SECONDS, remaining()),
                )
            except (TimeoutError, asyncio.TimeoutError):
                result = {
                    "success": False,
                    "output": f"Step timed out ({PER_STEP_SECONDS}s)",
                    "tool": tool_name,
                }

            duration_ms = int((time.monotonic() - started) * 1000)
            observation = observer.observe(step_number, result)
            any_failed = any_failed or not result.get("success", False)
            yield sse(
                "step",
                {
                    "type": "observe",
                    "step_number": step_number,
                    "step": step_number,
                    "content": observation["observation"],
                },
            )

            tool_result = {
                "step_number": step_number,
                "step": step_number,
                "tool_name": tool_name,
                "tool_output": observation["observation"],
                "status": "success" if result.get("success") else "error",
            }
            if result.get("file_id"):
                tool_result["file_id"] = result["file_id"]
                output_files.append(result["file_id"])
            yield sse("tool_result", tool_result)
            yield sse(
                "step",
                {
                    "type": "reflect",
                    "step_number": step_number,
                    "step": step_number,
                    "content": observation["reflection"],
                },
            )

            if db_task:
                try:
                    await AgentStep.create(
                        agent_task=db_task,
                        step_number=step_number,
                        type=StepType.ACT,
                        content=(
                            f"Act: {title}\nObserve: {observation['observation']}\n"
                            f"Reflect: {observation['reflection']}"
                        ),
                        model_used=selected_model,
                        duration_ms=duration_ms,
                    )
                    if result.get("tool") not in {None, "none"}:
                        await ToolCall.create(
                            agent_task=db_task,
                            tool_name=result["tool"],
                            tool_input={
                                key: value
                                for key, value in tool_input.items()
                                if key not in {"task", "step_title"}
                            },
                            tool_output=str(result.get("output", ""))[:4000],
                            status=(
                                ToolCallStatus.SUCCESS
                                if result.get("success")
                                else ToolCallStatus.ERROR
                            ),
                            duration_ms=duration_ms,
                        )
                except Exception as exc:
                    logger.exception(f"Could not save agent step: {exc}")

            total_steps += 1
            final_context += f"\n- Step {step_number} ({title}): {observation['observation']}"

        if cancelled():
            final_text = "Task cancelled by user."
            status = AgentTaskStatus.CANCELLED
        elif timed_out or remaining() <= 0:
            final_text = "Task failed because it exceeded the 5-minute limit."
            status = AgentTaskStatus.FAILED
        else:
            base_prompt = effective_system_prompt or (
                "You are Kavach AI, a sovereign on-premise AI workbench. "
                "Summarize execution results accurately. Never claim failed work succeeded."
            )
            messages = [
                {
                    "role": "system",
                    "content": f"{base_prompt}\n\nExecution Results:{final_context}",
                },
                {"role": "user", "content": task_description},
            ]
            chunks = []
            try:
                async with asyncio.timeout(remaining()):
                    async for chunk in ollama_client.chat_stream(
                        model=selected_model,
                        messages=messages,
                        keep_alive=-1,
                        options={"temperature": 0.3},
                    ):
                        if cancelled():
                            break
                        token = (
                            chunk.message.content
                            if hasattr(chunk, "message")
                            else chunk.get("message", {}).get("content", "")
                        )
                        if token:
                            chunks.append(token)
                            yield sse("token", {"content": token, "token": token})
                final_text = "".join(chunks)
            except (TimeoutError, asyncio.TimeoutError):
                timed_out = True
                final_text = "Task failed because it exceeded the 5-minute limit."
                yield sse("token", {"content": final_text, "token": final_text})
            except Exception as exc:
                logger.warning(f"Final agent synthesis unavailable: {exc}")
                final_text = (
                    f"Task failed after {total_steps} steps.{final_context}"
                    if any_failed
                    else f"Task completed in {total_steps} steps.{final_context}"
                )
                yield sse("token", {"content": final_text, "token": final_text})
            status = (
                AgentTaskStatus.CANCELLED
                if cancelled()
                else (
                    AgentTaskStatus.FAILED if any_failed or timed_out else AgentTaskStatus.COMPLETED
                )
            )

        if db_task:
            try:
                db_task.status = status
                db_task.total_steps = total_steps
                db_task.result_summary = final_text
                db_task.output_files = output_files
                db_task.completed_at = datetime.now(timezone.utc)
                await db_task.save()
            except Exception as exc:
                logger.exception(f"Could not finalize agent task: {exc}")

        yield sse(
            "done",
            {
                "task_id": task_id,
                "status": status.value,
                "total_steps": total_steps,
                "output_files": output_files,
            },
        )


agent_loop = AgentLoop()

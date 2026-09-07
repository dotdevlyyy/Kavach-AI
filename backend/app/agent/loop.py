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
        meta_event = {
            "event": "metadata",
            "data": json.dumps({
                "task_id": task_id,
                "conversation_id": conv_id,
                "model": selected_model,
                "task_type": route_metadata.task_type,
                "reasoning": route_metadata.reasoning
            })
        }
        yield f"event: {meta_event['event']}\ndata: {meta_event['data']}\n\n"

        # Step 2: Planning Phase
        yield f"event: step\ndata: {json.dumps({'type': 'plan', 'content': 'Generating strategic execution plan...'})}\n\n"

        plan_data = await planner.create_plan(
            task_description=task_description,
            model_name=selected_model,
            file_ids=file_ids
        )

        steps = plan_data.get("steps", [])
        goal_text = plan_data.get("goal", task_description)
        yield f"event: step\ndata: {json.dumps({'type': 'plan', 'content': f'Plan created with {len(steps)} steps: {goal_text}'})}\n\n"

        step_history = []
        final_context = ""

        # Step 3: Execution Loop (Plan -> Act -> Observe -> Reflect)
        step_idx = 1
        while step_idx <= min(len(steps), max_steps):
            step = steps[step_idx - 1]
            tool_name = step.get("suggested_tool", "none")
            title = step.get("title", f"Step {step_idx}")

            # Act
            yield f"event: step\ndata: {json.dumps({'type': 'action', 'step': step_idx, 'tool': tool_name, 'content': f'Executing #{step_idx}: {title}'})}\n\n"

            tool_input = {"task": task_description, "step_title": title}
            exec_result = await executor.execute_step(
                step_number=step_idx,
                tool_name=tool_name,
                tool_input=tool_input
            )

            # Observe
            obs = observer.observe(step_number=step_idx, result=exec_result)
            yield f"event: step\ndata: {json.dumps({'type': 'observation', 'step': step_idx, 'content': obs['observation']})}\n\n"

            # Reflect
            yield f"event: step\ndata: {json.dumps({'type': 'reflection', 'step': step_idx, 'content': obs['reflection']})}\n\n"

            step_history.append({
                "step": step_idx,
                "title": title,
                "tool": tool_name,
                "observation": obs['observation']
            })

            final_context += f"\n- Step {step_idx} ({title}): {obs['observation']}"

            # Self-correction logic if failed
            if obs.get("requires_self_correction", False):
                yield f"event: step\ndata: {json.dumps({'type': 'reflection', 'step': step_idx, 'content': 'Self-correcting failed step before proceeding...'})}\n\n"

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

        async for token in ollama_client.chat_stream(
            model=selected_model,
            messages=messages,
            options={"temperature": 0.3}
        ):
            token_event = {
                "event": "token",
                "data": json.dumps({"token": token})
            }
            yield f"event: {token_event['event']}\ndata: {token_event['data']}\n\n"

        # Done event
        done_event = {
            "event": "done",
            "data": json.dumps({
                "task_id": task_id,
                "status": "completed",
                "total_steps": len(step_history)
            })
        }
        yield f"event: {done_event['event']}\ndata: {done_event['data']}\n\n"


agent_loop = AgentLoop()

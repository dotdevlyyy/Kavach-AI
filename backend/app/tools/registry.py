"""
Kavach AI — Tool Registry
Decorator-based registry for Agent tools.
"""
import inspect
from typing import Callable, Any, Dict

_TOOL_REGISTRY: Dict[str, Callable] = {}


def register_tool(name: str):
    """Register a callable as a named tool for the agent."""
    def decorator(func: Callable):
        _TOOL_REGISTRY[name] = func
        return func
    return decorator


async def execute_tool(name: str, kwargs: dict) -> Any:
    """Invoke a registered tool by name with kwargs."""
    if name not in _TOOL_REGISTRY:
        raise ValueError(f"Tool {name} not found in registry")
    func = _TOOL_REGISTRY[name]
    if inspect.iscoroutinefunction(func):
        return await func(**kwargs)
    return func(**kwargs)

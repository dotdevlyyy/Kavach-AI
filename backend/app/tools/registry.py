"""
Kavach AI — Tool Registry
Decorator-based registry for Agent tools, auto-generating OpenAI/Ollama compatible schemas.
"""
import inspect
from typing import Callable, Any, Dict, get_type_hints

_TOOL_REGISTRY: Dict[str, Callable] = {}
_TOOL_SCHEMAS: Dict[str, dict] = {}

def get_type_name(t: Any) -> str:
    if t == str: return "string"
    if t == int: return "integer"
    if t == float: return "number"
    if t == bool: return "boolean"
    if t == list or getattr(t, "__origin__", None) == list: return "array"
    if t == dict or getattr(t, "__origin__", None) == dict: return "object"
    return "string"

def parse_docstring(doc: str) -> tuple[str, dict[str, str]]:
    if not doc:
        return "", {}
    lines = doc.strip().split("\n")
    description = lines[0].strip()
    
    param_desc = {}
    in_args = False
    for line in lines[1:]:
        line = line.strip()
        if line.lower().startswith("args:"):
            in_args = True
            continue
        if in_args and ":" in line:
            parts = line.split(":", 1)
            param_desc[parts[0].strip()] = parts[1].strip()
            
    return description, param_desc

def register_tool(name: str):
    def decorator(func: Callable):
        _TOOL_REGISTRY[name] = func
        
        # Generate schema
        doc = func.__doc__ or ""
        desc, param_desc = parse_docstring(doc)
        
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name in ["self", "cls"]:
                continue
            
            p_type = type_hints.get(param_name, str)
            schema_type = get_type_name(p_type)
            
            p_schema = {"type": schema_type}
            if param_name in param_desc:
                p_schema["description"] = param_desc[param_name]
                
            properties[param_name] = p_schema
            
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
                
        schema = {
            "type": "function",
            "function": {
                "name": name,
                "description": desc,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
        
        _TOOL_SCHEMAS[name] = schema
        return func
    return decorator

def get_all_tool_schemas() -> list[dict]:
    return list(_TOOL_SCHEMAS.values())

async def execute_tool(name: str, kwargs: dict) -> Any:
    if name not in _TOOL_REGISTRY:
        raise ValueError(f"Tool {name} not found in registry")
        
    func = _TOOL_REGISTRY[name]
    if inspect.iscoroutinefunction(func):
        return await func(**kwargs)
    return func(**kwargs)

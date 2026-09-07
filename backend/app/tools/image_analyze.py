import base64
from pathlib import Path
from app.tools.registry import register_tool
from app.core.ollama_client import ollama_client

DATA_DIR = Path("backend/data").resolve()

@register_tool("analyze_engineering_diagram")
async def analyze_engineering_diagram(filepath: str, query: str) -> str:
    """Analyze P&ID diagrams or engineering drawings and answer questions about them.
    
    Args:
        filepath: Path to the image file, relative to backend/data/
        query: Specific question about the diagram (e.g., "What are the tag numbers for the valves?")
    """
    target = (DATA_DIR / filepath).resolve()
    if not target.exists() or not target.is_file():
        return f"Error: Image {filepath} not found."
        
    try:
        with open(target, "rb") as f:
            b64_image = base64.b64encode(f.read()).decode("utf-8")
            
        response = await ollama_client.client.chat(
            model="qwen2.5vl:3b",
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze this engineering diagram carefully and answer the following query: {query}",
                    "images": [b64_image]
                }
            ]
        )
        return response.message.content
    except Exception as e:
        return f"Error analyzing diagram: {str(e)}"

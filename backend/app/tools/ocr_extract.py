import base64
from pathlib import Path
from app.tools.registry import register_tool
from app.core.ollama_client import ollama_client

DATA_DIR = Path("data").resolve() if Path("data").exists() else Path("backend/data").resolve()

@register_tool("extract_text_from_image")
async def extract_text_from_image(filepath: str) -> str:
    """Extract text from a scanned document or image using Qwen2.5-VL.
    
    Args:
        filepath: Path to the image file, relative to backend/data/
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
                    "content": "Extract all text from this image exactly as written. Do not add any commentary.",
                    "images": [b64_image]
                }
            ]
        )
        return response.message.content
    except Exception as e:
        return f"Error extracting text: {str(e)}"

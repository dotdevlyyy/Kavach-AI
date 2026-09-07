from app.core.ollama_client import ollama_client

async def generate_embedding(text: str) -> list[float]:
    """Generate vector embeddings for a chunk of text using Ollama."""
    try:
        response = await ollama_client.client.embeddings(
            model="llama3.2:1b",
            prompt=text
        )
        return response.embedding
    except Exception as e:
        import loguru
        loguru.logger.error(f"Embedding error: {str(e)}")
        return []

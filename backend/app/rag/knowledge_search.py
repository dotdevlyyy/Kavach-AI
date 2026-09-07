from app.tools.registry import register_tool
from app.rag.retriever import hybrid_search

@register_tool("search_knowledge_base")
async def search_knowledge_base(query: str) -> str:
    """Search the MRPL on-premises knowledge base (SOPs, docs) for answers.
    
    Args:
        query: The search query to look up in the documents.
    """
    results = await hybrid_search(query, limit=3)
    if not results:
        return "No relevant information found in the knowledge base."
        
    formatted = "Knowledge Base Results:\n\n"
    for r in results:
        formatted += f"- {r['content']}\n"
    
    return formatted

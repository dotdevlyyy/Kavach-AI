from app.rag.retriever import hybrid_search
from app.tools.registry import register_tool


@register_tool("search_knowledge_base")
async def search_knowledge_base(query: str) -> str:
    """Search the MRPL on-premises knowledge base (SOPs, docs) for answers.

    Args:
        query: The search query to look up in the documents.
    """
    results = await hybrid_search(query, limit=3)
    if not results:
        return "No relevant information found in the knowledge base."

    lines = ["Knowledge Base Results:\n"]
    for r in results:
        name = r.get("document_name") or "unknown"
        score = r.get("score", 0)
        lines.append(f"- [{name}] (score={score:.4f}) {r['content']}")
    return "\n".join(lines)

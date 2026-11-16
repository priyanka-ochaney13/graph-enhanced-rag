from tavily import TavilyClient
from src.config import settings

_client = None


def _tavily() -> TavilyClient:
    global _client
    if _client is None:
        _client = TavilyClient(api_key=settings.tavily_api_key)
    return _client


def retrieve_web(query: str, user_roles: list[str], max_results: int = 3) -> list[dict]:
    if not settings.tavily_api_key:
        return []
    try:
        resp = _tavily().search(query=query, max_results=max_results, search_depth="basic")
    except Exception as e:
        return [{"text": f"Web search error: {e}", "source": "web", "doc_id": "web:error", "score": 0.0, "trust": "untrusted"}]

    docs = []
    for r in resp.get("results", []):
        docs.append({
            "text": r.get("content", "")[:1500],
            "source": r.get("url", "web"),
            "doc_id": r.get("url", "web"),
            "score": float(r.get("score", 0.5)),
            "trust": "untrusted",
        })
    return docs
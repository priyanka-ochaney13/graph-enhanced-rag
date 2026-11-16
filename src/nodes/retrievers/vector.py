from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny

from src.config import settings
from src.security.injection import screen_chunk

_client = None


def _qdrant() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=settings.qdrant_url)
    return _client


def _embed(text: str) -> list[float]:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return model.encode(text).tolist()


def retrieve_vector(query: str, user_roles: list[str], top_k: int = 5) -> list[dict]:
    acl_filter = Filter(
        must=[FieldCondition(key="allowed_roles", match=MatchAny(any=user_roles))]
    )
    hits = _qdrant().query_points(
        collection_name=settings.qdrant_collection,
        query=_embed(query),
        query_filter=acl_filter,
        limit=top_k,
        with_payload=True,
    ).points

    docs = []
    for hit in hits:
        payload = hit.payload or {}
        text = payload.get("text", "")
        safe, reason = screen_chunk(text)
        if not safe:
            continue
        docs.append({
            "text": text,
            "source": payload.get("source", "unknown"),
            "doc_id": payload.get("doc_id", ""),
            "score": float(hit.score),
            "trust": "untrusted",
        })
    return docs
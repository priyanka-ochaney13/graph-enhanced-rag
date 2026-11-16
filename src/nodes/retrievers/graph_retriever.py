import re
from neo4j import GraphDatabase, RoutingControl

from src.config import settings

_driver = None


def _neo4j():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )
    return _driver


def _extract_entity_hint(query: str) -> str:
    """Naive entity hint: use the longest capitalised span."""
    spans = re.findall(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b", query)
    return max(spans, key=len) if spans else query


def retrieve_graph(query: str, user_roles: list[str], limit: int = 10) -> list[dict]:
    entity_hint = _extract_entity_hint(query)
    records, _, _ = _neo4j().execute_query(
        """
        MATCH (e:Entity)
        WHERE toLower(e.name) CONTAINS toLower($hint)
        OPTIONAL MATCH (e)-[r:RELATED_TO]-(neighbor:Entity)
        OPTIONAL MATCH (d:Document)-[:MENTIONS]->(e)
        WHERE d.acl IS NULL OR any(role IN d.acl WHERE role IN $roles)
        RETURN e.name AS entity, e.type AS type,
               collect(DISTINCT neighbor.name)[..5] AS neighbors,
               collect(DISTINCT d.title)[..3] AS sources
        LIMIT $limit
        """,
        hint=entity_hint,
        roles=user_roles,
        limit=limit,
        routing_=RoutingControl.READ,
        database_="neo4j",
    )

    docs = []
    for rec in records:
        entity = rec["entity"]
        neighbors = rec["neighbors"] or []
        text = f"Entity: {entity} ({rec['type']}). Related to: {', '.join(neighbors)}." if neighbors else f"Entity: {entity} ({rec['type']})."
        docs.append({
            "text": text,
            "source": "knowledge_graph",
            "doc_id": f"graph:{entity}",
            "score": 0.7,
            "trust": "trusted_structured",
            "sources": rec["sources"] or [],
        })
    return docs
"""Run once to seed Qdrant + Neo4j with sample ACL-tagged documents."""
import json
import uuid
from pathlib import Path

from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, PayloadSchemaType

from src.config import settings
from src.ingestion.chunker import chunk_text
from src.ingestion.graph_extractor import extract_graph

# Sample docs with ACLs. Replace with your own corpus.
SAMPLE_DOCS = [
    {
        "id": "doc-001",
        "title": "Apple Inc. Company Overview",
        "text": "Apple Inc. was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne in 1976. "
                "Apple acquired Siri Inc. in 2010. Siri is a virtual assistant. "
                "Tim Cook is the CEO of Apple.",
        "allowed_roles": ["public", "employee"],
    },
    {
        "id": "doc-002",
        "title": "Siri Acquisition Details (Confidential)",
        "text": "Apple acquired Siri for approximately $200 million in 2010. "
                "The Siri team was integrated into Apple's iPhone division.",
        "allowed_roles": ["employee", "executive"],
    },
    {
        "id": "doc-003",
        "title": "Steve Jobs Biography",
        "text": "Steve Jobs co-founded Apple Computer in 1976. He was the CEO of Apple until 2011. "
                "Steve Jobs was also involved with Pixar and NeXT.",
        "allowed_roles": ["public"],
    },
]


def seed():
    qdrant = QdrantClient(url=settings.qdrant_url)
    try:
        qdrant.get_collection(settings.qdrant_collection)
    except Exception:
        qdrant.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

    qdrant.create_payload_index(
        collection_name=settings.qdrant_collection,
        field_name="allowed_roles",
        field_schema=PayloadSchemaType.KEYWORD,
    )

    from sentence_transformers import SentenceTransformer
    encoder = SentenceTransformer("all-MiniLM-L6-v2")

    neo4j = GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )

    points = []
    for doc in SAMPLE_DOCS:
        chunks = chunk_text(doc["text"])
        for i, chunk in enumerate(chunks):
            vec = encoder.encode(chunk).tolist()
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload={
                    "text": chunk,
                    "source": doc["title"],
                    "doc_id": doc["id"],
                    "chunk_index": i,
                    "allowed_roles": doc["allowed_roles"],
                },
            ))

        graph = extract_graph(doc["text"])
        with neo4j.session() as session:
            for ent in graph.get("entities", []):
                session.run(
                    "MERGE (e:Entity {name: $name}) SET e.type = $type "
                    "MERGE (d:Document {id: $doc_id}) "
                    "SET d.title = $title, d.acl = $acl "
                    "MERGE (d)-[:MENTIONS]->(e)",
                    name=ent["name"], type=ent.get("type", "OTHER"),
                    doc_id=doc["id"], title=doc["title"], acl=doc["allowed_roles"],
                )
            for rel in graph.get("relationships", []):
                session.run(
                    "MATCH (a:Entity {name: $source}), (b:Entity {name: $target}) "
                    "MERGE (a)-[:RELATED_TO {type: $type}]->(b)",
                    source=rel["source"], target=rel["target"], type=rel.get("type", "RELATED"),
                )

    if points:
        qdrant.upsert(collection_name=settings.qdrant_collection, points=points)
    neo4j.close()
    print(f"Seeded {len(points)} chunks and graph entities.")


if __name__ == "__main__":
    seed()
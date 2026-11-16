import re
from src.llm import chat_fast
from src.state import GraphState

GRADER_PROMPT = """You are a strict retrieval relevance grader.
Task: {task}
Chunk: <chunk>{chunk}</chunk>
Is this chunk relevant and sufficient to help answer the task? Answer only YES or NO."""


def grade_node(state: GraphState) -> GraphState:
    docs = state["retrieved_docs"]

    if docs and all(
        doc.get("source") == "knowledge_graph"
        for doc in docs
    ):
        for doc in docs:
            doc["grade"] = "relevant"

        state["relevant_docs"] = docs
        state["grade_score"] = 1.0
        return state

    relevant = []

    for doc in docs:
        answer = chat_fast([
            {"role": "system", "content": "You output only YES or NO."},
            {
                "role": "user",
                "content": GRADER_PROMPT.format(
                    task=state["query"],
                    chunk=doc["text"][:1200],
                ),
            },
        ]).strip().upper()

        if answer.startswith("YES"):
            doc["grade"] = "relevant"
            relevant.append(doc)
        else:
            doc["grade"] = "irrelevant"

    state["relevant_docs"] = relevant
    total = max(len(docs), 1)
    state["grade_score"] = len(relevant) / total
    return state
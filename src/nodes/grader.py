import re
from src.llm import chat_fast
from src.state import GraphState

GRADER_PROMPT = """You are a strict retrieval relevance grader.
Task: {task}
Chunk: <chunk>{chunk}</chunk>
Is this chunk relevant and sufficient to help answer the task? Answer only YES or NO."""


def grade_node(state: GraphState) -> GraphState:
    relevant = []
    for doc in state["retrieved_docs"]:
        answer = chat_fast([
            {"role": "system", "content": "You output only YES or NO."},
            {"role": "user", "content": GRADER_PROMPT.format(task=state["current_task"], chunk=doc["text"][:1200])},
        ]).strip().upper()
        if answer.startswith("YES"):
            doc["grade"] = "relevant"
            relevant.append(doc)
        else:
            doc["grade"] = "irrelevant"

    state["relevant_docs"] = relevant
    total = max(len(state["retrieved_docs"]), 1)
    state["grade_score"] = len(relevant) / total
    return state
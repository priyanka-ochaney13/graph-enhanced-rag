from src.llm import chat_fast
from src.state import GraphState
from src.config import settings


def rewrite_node(state: GraphState) -> GraphState:
    if state["rewrite_count"] >= settings.max_rewrites:
        state["current_task"] = state["current_task"] + " (latest information, web)"
        return state

    new_query = chat_fast([
        {"role": "system", "content": "Rewrite the query to improve retrieval. Output only the rewritten query."},
        {"role": "user", "content": f"Original query: {state['current_task']}\nReason: previous retrieval was not relevant."},
    ]).strip()

    if new_query:
        state["current_task"] = new_query
    state["rewrite_count"] += 1
    return state
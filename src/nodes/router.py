from typing import Literal
from src.state import GraphState


def route_tool(state: GraphState) -> Literal["vector", "graph", "sql", "web"]:
    task = state["current_task"].lower()

    if any(k in task for k in ["relationship", "connected", "related", "entity", "graph"]):
        return "graph"
    if any(k in task for k in ["count", "average", "sum", "table", "database", "acquisition", "how many"]):
        return "sql"
    if any(k in task for k in ["latest", "news", "current", "today", "web"]):
        return "web"
    return "vector"
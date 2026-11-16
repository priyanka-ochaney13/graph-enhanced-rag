from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    query: str
    user_roles: list[str]
    messages: Annotated[list, add_messages]

    sub_tasks: list[str]
    current_task: str
    task_index: int

    retrieved_docs: list[dict]
    relevant_docs: list[dict]
    grade_score: float
    rewrite_count: int

    final_answer: str
    verification_feedback: str
    verify_loops: int

    trace_id: str
    budget_used: dict
    error: str

def initial_state(query: str, user_roles: list[str], trace_id: str) -> GraphState:
    return GraphState(
        query=query,
        user_roles=user_roles,
        messages=[],
        sub_tasks=[],
        current_task="",
        task_index=0,
        retrieved_docs=[],
        relevant_docs=[],
        grade_score=0.0,
        rewrite_count=0,
        final_answer="",
        verification_feedback="",
        verify_loops=0,
        trace_id=trace_id,
        budget_used={"cost": 0.0, "latency_ms": 0},
        error="",
    )
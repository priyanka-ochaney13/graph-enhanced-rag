from langgraph.graph import StateGraph, START, END
from src.state import GraphState
from src.nodes.planner import planner_node
from src.nodes.router import route_tool
from src.nodes.grader import grade_node
from src.nodes.rewriter import rewrite_node
from src.nodes.generator import generator_node
from src.nodes.verifier import verifier_node
from src.nodes.retrievers.vector import retrieve_vector
from src.nodes.retrievers.graph_retriever import retrieve_graph
from src.nodes.retrievers.sql import retrieve_sql
from src.nodes.retrievers.web import retrieve_web
from src.config import settings
from src.observability.budget import BudgetTracker
from src.security.injection import sanitize_output


def _retrieve(state: GraphState, tool: str) -> GraphState:
    roles = state["user_roles"]
    task = state["current_task"]
    if tool == "vector":
        docs = retrieve_vector(task, roles)
    elif tool == "graph":
        docs = retrieve_graph(task, roles)
    elif tool == "sql":
        docs = retrieve_sql(task, roles)
    elif tool == "web":
        docs = retrieve_web(task, roles)
    else:
        docs = retrieve_vector(task, roles)

    state["retrieved_docs"] = docs
    state["relevant_docs"] = []
    state["grade_score"] = 0.0
    state["rewrite_count"] = 0
    return state


def vector_node(state: GraphState) -> GraphState:
    return _retrieve(state, "vector")


def graph_node(state: GraphState) -> GraphState:
    return _retrieve(state, "graph")


def sql_node(state: GraphState) -> GraphState:
    return _retrieve(state, "sql")


def web_node(state: GraphState) -> GraphState:
    return _retrieve(state, "web")


def route_after_grade(state: GraphState) -> str:
    if state["grade_score"] >= 0.5:
        return "generator"
    if state["rewrite_count"] < settings.max_rewrites:
        return "rewriter"
    return "web"


def route_after_verify(state: GraphState) -> str:
    if state["verification_feedback"] and state["verify_loops"] < settings.max_verify_loops:
        return "generator"
    return "finalize"


def finalize_node(state: GraphState) -> GraphState:
    state["final_answer"] = sanitize_output(state["final_answer"])
    if state["task_index"] + 1 < len(state["sub_tasks"]):
        state["task_index"] += 1
        state["current_task"] = state["sub_tasks"][state["task_index"]]
    return state


def build_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("vector", vector_node)
    workflow.add_node("graph", graph_node)
    workflow.add_node("sql", sql_node)
    workflow.add_node("web", web_node)
    workflow.add_node("grader", grade_node)
    workflow.add_node("rewriter", rewrite_node)
    workflow.add_node("generator", generator_node)
    workflow.add_node("verifier", verifier_node)
    workflow.add_node("finalize", finalize_node)

    workflow.add_edge(START, "planner")

    workflow.add_conditional_edges(
        "planner",
        route_tool,
        {"vector": "vector", "graph": "graph", "sql": "sql", "web": "web"},
    )

    for tool_node in ["vector", "graph", "sql", "web"]:
        workflow.add_edge(tool_node, "grader")

    workflow.add_conditional_edges(
        "grader",
        route_after_grade,
        {"generator": "generator", "rewriter": "rewriter", "web": "web"},
    )

    workflow.add_edge("rewriter", "grader")
    workflow.add_edge("generator", "verifier")

    workflow.add_conditional_edges(
        "verifier",
        route_after_verify,
        {"generator": "generator", "finalize": "finalize"},
    )

    workflow.add_edge("finalize", END)

    return workflow.compile()


rag_agent = build_graph()


def run_query(query: str, user_roles: list[str], trace_id: str) -> dict:
    budget = BudgetTracker(settings.max_cost_usd, settings.max_latency_ms)
    state = {
        "query": query,
        "user_roles": user_roles,
        "messages": [],
        "sub_tasks": [],
        "current_task": "",
        "task_index": 0,
        "retrieved_docs": [],
        "relevant_docs": [],
        "grade_score": 0.0,
        "rewrite_count": 0,
        "final_answer": "",
        "verification_feedback": "",
        "verify_loops": 0,
        "trace_id": trace_id,
        "budget_used": {"cost": 0.0, "latency_ms": 0},
        "error": "",
    }
    try:
        result = rag_agent.invoke(state, config={"recursion_limit": 25})
        budget.check()
        result["budget_used"] = budget.snapshot()
        return result
    except Exception as e:
        return {
            **state,
            "error": str(e),
            "final_answer": "I encountered an error while processing your request.",
            "budget_used": budget.snapshot(),
        }
import uuid
from fastapi import FastAPI, Depends
from pydantic import BaseModel

from src.graph import run_query
from src.api.auth import get_current_user, CurrentUser

app = FastAPI(title="Agentic Graph RAG", version="1.0.0")


class QueryRequest(BaseModel):
    query: str
    max_rewrites: int | None = None


class QueryResponse(BaseModel):
    answer: str
    trace_id: str
    sub_tasks: list[str]
    retrieved_count: int
    relevant_count: int
    grade_score: float
    verify_loops: int
    budget: dict
    error: str = ""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest, user: CurrentUser = Depends(get_current_user)):
    trace_id = str(uuid.uuid4())
    result = run_query(req.query, user.roles, trace_id)
    return QueryResponse(
        answer=result.get("final_answer", ""),
        trace_id=trace_id,
        sub_tasks=result.get("sub_tasks", []),
        retrieved_count=len(result.get("retrieved_docs", [])),
        relevant_count=len(result.get("relevant_docs", [])),
        grade_score=result.get("grade_score", 0.0),
        verify_loops=result.get("verify_loops", 0),
        budget=result.get("budget_used", {}),
        error=result.get("error", ""),
    )
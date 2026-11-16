import json
import re
from src.llm import chat_reasoning
from src.state import GraphState

PLANNER_PROMPT = """Decompose the user's question into 1-4 ordered sub-tasks.
Each sub-task should be a self-contained retrieval or reasoning step.
Return ONLY a JSON list of strings.
Question: {question}"""


def planner_node(state: GraphState) -> GraphState:
    raw = chat_reasoning([
        {"role": "system", "content": "You are a meticulous research planner. Output only JSON."},
        {"role": "user", "content": PLANNER_PROMPT.format(question=state["query"])},
    ])
    try:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        tasks = json.loads(match.group(0)) if match else [state["query"]]
        if not isinstance(tasks, list) or not tasks:
            tasks = [state["query"]]
    except Exception:
        tasks = [state["query"]]

    state["sub_tasks"] = [str(t).strip() for t in tasks if str(t).strip()]
    state["current_task"] = state["sub_tasks"][0]
    state["task_index"] = 0
    return state
from src.llm import chat_fast
from src.state import GraphState

VERIFIER_PROMPT = """Check whether the answer is fully supported by the context.
Context:
{context}

Answer:
{answer}

Reply with:
VERDICT: GROUNDED or NOT_GROUNDED
REASON: <one sentence>"""


def verifier_node(state: GraphState) -> GraphState:
    context = "\n\n".join(d["text"] for d in state["relevant_docs"])[:6000]
    raw = chat_fast([
        {"role": "system", "content": "You are a strict hallucination detector. Follow the output format exactly."},
        {"role": "user", "content": VERIFIER_PROMPT.format(context=context, answer=state["final_answer"])},
    ])

    upper = raw.upper()
    if "NOT_GROUNDED" in upper or ("VERDICT" in upper and "GROUNDED" not in upper.replace("NOT_GROUNDED", "")):
        state["verification_feedback"] = raw.strip()
    else:
        state["verification_feedback"] = ""

    state["verify_loops"] += 1
    return state
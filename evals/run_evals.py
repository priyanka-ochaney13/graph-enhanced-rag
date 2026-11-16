import json
import uuid
from pathlib import Path
from langchain_community.embeddings import (
    HuggingFaceEmbeddings as LocalHuggingFaceEmbeddings,
)
from ragas.embeddings.base import LangchainEmbeddingsWrapper
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

from src.graph import run_query

from openai import OpenAI
from ragas.llms import llm_factory
from src.config import settings

def main():
    data = json.loads(Path("evals/golden_set.json").read_text())

    rows = []
    for item in data:
        trace_id = str(uuid.uuid4())
        result = run_query(item["question"], item["roles"], trace_id)
        rows.append({
            "question": item["question"],
            "answer": result.get("final_answer", ""),
            "contexts": [d["text"] for d in result.get("relevant_docs", [])],
            "ground_truth": item["expected"],
        })
        print(f"Q: {item['question']}\nA: {result.get('final_answer')}\n---")

    dataset = Dataset.from_list(rows)
    groq_client = OpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1",
    )

    evaluator_llm = llm_factory(
        settings.groq_model_reasoning,
        provider="openai",
        client=groq_client,
    )
    evaluator_embeddings = LangchainEmbeddingsWrapper(
        LocalHuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    )
    results = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy],
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
        raise_exceptions=True,
    )
    scores = results.to_pandas()

    output = {
        "faithfulness": float(scores["faithfulness"].mean()),
        "answer_relevancy": float(scores["answer_relevancy"].mean()),
        "n_questions": len(rows),
    }

    Path("evals/last_results.json").write_text(
        json.dumps(output, indent=2),
        encoding="utf-8",
    )

    print(results)
    print(scores)


if __name__ == "__main__":
    main()
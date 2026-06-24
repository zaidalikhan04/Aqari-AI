import json
import os
import time
import re
from dotenv import load_dotenv
load_dotenv()

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from ragas.run_config import RunConfig
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from openai import OpenAI

from rag_chain import PropertyRAG

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama-3.3-70b-versatile"

EVAL_DATASET = [
    {
        "question": "Show me studio apartments for sale in International City",
        "ground_truth": "There are studio apartments in International City starting from AED 325,000, unfurnished and ready to move in, around 483 sqft.",
        "category": "location_filter"
    },
    {
        "question": "Find me 2 bedroom apartments in JVC under 2 million AED",
        "ground_truth": "2 bedroom apartments in JVC are available under 2 million AED, mostly off-plan and unfurnished.",
        "category": "price_filter"
    },
    {
        "question": "What are the cheapest studios available in Dubai?",
        "ground_truth": "Cheapest studios in Dubai start from AED 325,000 in International City and AED 470,000 in Arjan.",
        "category": "price_filter"
    },
    {
        "question": "Show me furnished apartments for sale in Dubai",
        "ground_truth": "Furnished apartments include studios in Arjan at AED 470,000 and larger units in Dubai Islands.",
        "category": "furnishing_filter"
    },
    {
        "question": "Find townhouses for sale in DAMAC Hills",
        "ground_truth": "Townhouses in DAMAC Hills 2 start from AED 1,800,000 with 3 beds and 4 baths, off-plan.",
        "category": "property_type_filter"
    },
    {
        "question": "Show me ready to move in apartments in Business Bay",
        "ground_truth": "Business Bay has ready apartments including 1 bedroom in Scala Tower at AED 1,250,000 with around 1,000 sqft.",
        "category": "completion_filter"
    },
    {
        "question": "Find 1 bedroom apartments under 1.5 million AED ready to move in",
        "ground_truth": "Ready 1 bedroom apartments under 1.5 million include Scala Tower in Business Bay at AED 1,250,000.",
        "category": "combined_filter"
    },
]


def get_bm25_contexts(rag: PropertyRAG, query: str) -> list[str]:
    """BM25-only baseline — no ChromaDB, no expansion, no reranking."""
    try:
        tokens = re.findall(r"[a-z0-9]+", query.lower())
        scores = rag.bm25.get_scores(tokens)
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:5]
        return [rag.bm25_docs[i] for i in ranked]
    except Exception as e:
        print(f"    BM25 baseline error: {e}")
        return []


def get_full_contexts(rag: PropertyRAG, query: str) -> list[str]:
    """Full 4-stage pipeline — expansion, hybrid RRF, cross-encoder reranking."""
    try:
        result = rag.query(query, chat_history=[], filters=None)
        return [m["text"] for m in result["matches"]]
    except Exception as e:
        print(f"    Full pipeline error: {e}")
        return []


def generate_answer(client: OpenAI, contexts: list[str], question: str) -> str:
    """Generate answer from contexts using Groq."""
    context_str = "\n\n".join(contexts)[:600]
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "Answer using only the property listings context. Be brief."
            },
            {
                "role": "user",
                "content": f"Context:\n{context_str}\n\nQuestion: {question}"
            }
        ]
    )
    return resp.choices[0].message.content or ""


def run_evaluation(rag, client, context_fn, label: str) -> dict:
    print(f"\n{'='*50}")
    print(f"Evaluating: {label}")
    print(f"{'='*50}")

    q_list, a_list, ctx_list, gt_list = [], [], [], []

    for i, item in enumerate(EVAL_DATASET):
        print(f"  [{i+1}/{len(EVAL_DATASET)}] {item['question'][:55]}...")
        try:
            ctx = context_fn(rag, item["question"])
            time.sleep(5)
            answer = generate_answer(client, ctx, item["question"])
            time.sleep(5)
            print(f"    Got {len(ctx)} contexts, answer: {answer[:60]}...")
            q_list.append(item["question"])
            a_list.append(answer)
            ctx_list.append([c[:300] for c in ctx] if ctx else ["No results found."])
            gt_list.append(item["ground_truth"])
        except Exception as e:
            print(f"    ERROR on question {i+1}: {e}")
            q_list.append(item["question"])
            a_list.append("No information available.")
            ctx_list.append(["No results found."])
            gt_list.append(item["ground_truth"])

    dataset = Dataset.from_dict({
        "question": q_list,
        "answer": a_list,
        "contexts": ctx_list,
        "ground_truth": gt_list,
    })

    safe_label = label.replace(" ", "_").replace("(", "").replace(")", "")
    dataset.to_json(f"eval_inputs_{safe_label}.json")
    print(f"  Saved inputs to eval_inputs_{safe_label}.json")

    print(f"\nWaiting 30s before RAGAs scoring to reset rate limit...")
    time.sleep(30)

    eval_llm = LangchainLLMWrapper(ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,
        max_tokens=512,
    ))
    eval_embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    )

    scores = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=eval_llm,
        embeddings=eval_embeddings,
        run_config=RunConfig(
            max_workers=1,
            max_wait=120,
            timeout=180,
        ),
    )

    print(f"\nResults — {label}:")
    print(scores)
    return {"label": label, "scores": scores}


if __name__ == "__main__":
    print("Initialising RAG system...")
    rag = PropertyRAG()

    client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url=GROQ_BASE_URL
    )

    # Run baseline first
    bm25_results = run_evaluation(
        rag, client, get_bm25_contexts, "BM25 Baseline"
    )

    print("\nWaiting 90 seconds before full pipeline evaluation...")
    time.sleep(90)

    # Run full pipeline
    full_results = run_evaluation(
        rag, client, get_full_contexts, "Full 4-Stage Pipeline"
    )

    print("\n" + "="*50)
    print("FINAL COMPARISON")
    print("="*50)
    print(f"\nBM25 Baseline:  {bm25_results['scores']}")
    print(f"Full Pipeline:  {full_results['scores']}")

    with open("ragas_results.json", "w") as f:
        json.dump({
            "bm25_baseline": str(bm25_results["scores"]),
            "full_pipeline": str(full_results["scores"]),
        }, f, indent=2)

    print("\nSaved to ragas_results.json")
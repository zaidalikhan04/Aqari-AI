import json
import os
import pickle
import re
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()

BM25_INDEX_PATH = os.path.join("data", "bm25_index.pkl")
BM25_DOCS_PATH = os.path.join("data", "bm25_docs.pkl")
DOCS_META_PATH = os.path.join("data", "docs_meta.pkl")
EMBEDDINGS_PATH = os.path.join("data", "embeddings.npy")

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama-3.3-70b-versatile"

_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _rrf(rank: int, k: int = 60) -> float:
    return 1.0 / (rank + k)


def _last_n_messages(chat_history: list[dict], n: int) -> list[dict]:
    if not chat_history:
        return []
    return chat_history[-n:]


def _safe_json_list(text: str) -> list[str]:
    """
    Best-effort parse of LLM output intended to be a JSON list of strings.
    """
    
    text = text.strip()
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()]
    except Exception:
        pass

    # Fallback: extract lines / bullets
    lines = [l.strip(" \t-•").strip() for l in text.splitlines()]
    lines = [l for l in lines if l]
    return lines[:3]


@dataclass
class RetrievedDoc:
    doc_id: str
    text: str
    metadata: dict
    score: float = 0.0


class PropertyRAG:
    def __init__(self) -> None:
        from openai import OpenAI

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("Missing GROQ_API_KEY environment variable.")

        self.client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)

        # Load BM25 assets once
        if not os.path.exists(BM25_INDEX_PATH) or not os.path.exists(BM25_DOCS_PATH):
            raise RuntimeError(
                "Missing BM25 artifacts. Run `python ingest.py` to build "
                f"`{BM25_INDEX_PATH}` and `{BM25_DOCS_PATH}`."
            )
        with open(BM25_INDEX_PATH, "rb") as f:
            self.bm25 = pickle.load(f)
        with open(BM25_DOCS_PATH, "rb") as f:
            self.bm25_docs: list[str] = pickle.load(f)

        # Load numpy embeddings + metadatas (crash-safe, no ChromaDB/hnswlib)
        import numpy as np

        self.doc_embeddings = np.load(EMBEDDINGS_PATH)  # shape (N, D)
        with open(DOCS_META_PATH, "rb") as f:
            self.doc_metadatas: list[dict] = pickle.load(f)

        # Bi-encoder for query embedding (must match ingest.py's EMBED_MODEL_NAME)
        from sentence_transformers import SentenceTransformer, CrossEncoder

        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        # Cross-encoder for reranking
        self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    def _expand_queries(self, user_query: str, chat_history: list[dict]) -> list[str]:
        memory = _last_n_messages(chat_history, 4)
        messages = [
            {
                "role": "system",
                "content": (
                    "Rewrite the user's real-estate search query into 3 alternative phrasings. "
                    "Keep meaning the same; preserve constraints like budget, bedrooms, city/area, "
                    "sale vs rent, and property type. Output ONLY a JSON array of 3 strings."
                ),
            },
        ]
        if memory:
            messages.append(
                {
                    "role": "user",
                    "content": "Recent conversation context (last messages):\n" + json.dumps(memory, ensure_ascii=False),
                }
            )
        messages.append({"role": "user", "content": f"User query: {user_query}"})

        resp = self.client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0.2,
            messages=messages,
        )
        content = resp.choices[0].message.content or "[]"
        variants = _safe_json_list(content)
        variants = [v for v in variants if v and v.lower() != user_query.lower()]
        return [user_query] + variants[:3]

    def _bm25_topk(self, query: str, k: int = 20) -> list[tuple[str, int]]:
        tokens = _tokenize(query)
        scores = self.bm25.get_scores(tokens)
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        # Return (doc_id, rank)
        return [(f"listing_{i}", rank) for rank, i in enumerate(ranked)]

    def _vector_topk(self, query: str, k: int = 20, filters: dict | None = None) -> list[tuple[str, int]]:
        import numpy as np
        q_emb = self.embedder.encode(query)
        # Cosine similarity via dot product on L2-normalised vectors
        norms = np.linalg.norm(self.doc_embeddings, axis=1, keepdims=True)
        normed = self.doc_embeddings / np.clip(norms, 1e-10, None)
        q_norm = q_emb / max(float(np.linalg.norm(q_emb)), 1e-10)
        sims = normed @ q_norm
        ranked = sims.argsort()[::-1][:k]
        return [(f"listing_{i}", rank) for rank, i in enumerate(ranked)]

    def _fetch_docs(self, doc_ids: list[str]) -> dict[str, RetrievedDoc]:
        out: dict[str, RetrievedDoc] = {}
        for doc_id in doc_ids:
            try:
                idx = int(doc_id.replace("listing_", ""))
                text = self.bm25_docs[idx]
                md = self.doc_metadatas[idx] if idx < len(self.doc_metadatas) else {}
                out[doc_id] = RetrievedDoc(doc_id=doc_id, text=text, metadata=md)
            except Exception:
                out[doc_id] = RetrievedDoc(doc_id=doc_id, text="", metadata={})
        return out

    def query(self, user_query: str, chat_history: list[dict] = [], filters: dict | None = None) -> dict:
        """
        Returns a dict:
          - answer: str
          - matches: list[{id, metadata, text, score}]
          - expanded_queries: list[str]
        """
        expanded = self._expand_queries(user_query, chat_history)

        # Step 1+2: Hybrid retrieval across all query variants + RRF fusion
        rrf_scores: dict[str, float] = {}
        seen_sources: dict[str, set] = {}

        for q in expanded:
            bm25_ranked = self._bm25_topk(q, k=20)
            vec_ranked = self._vector_topk(q, k=20, filters=filters)

            for doc_id, rank in bm25_ranked:
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + _rrf(rank)
                seen_sources.setdefault(doc_id, set()).add(f"bm25:{q}")

            for doc_id, rank in vec_ranked:
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + _rrf(rank)
                seen_sources.setdefault(doc_id, set()).add(f"vec:{q}")

        top10_ids = [doc_id for doc_id, _ in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:10]]
        docs_map = self._fetch_docs(top10_ids)
        retrieved = [docs_map[i] for i in top10_ids if i in docs_map]

        # Step 3: Cross-encoder reranking against the (original) user query
        pairs = [(user_query, d.text) for d in retrieved]
        if pairs:
            ce_scores = self.cross_encoder.predict(pairs).tolist()
            for d, s in zip(retrieved, ce_scores):
                d.score = float(s)
        reranked = sorted(retrieved, key=lambda d: d.score, reverse=True)[:5]

        # Step 4+5: Generate answer with conversation memory
        memory = _last_n_messages(chat_history, 4)
        listings_payload = []
        for d in reranked:
            md = dict(d.metadata or {})
            md.pop("embeddings", None)
            listings_payload.append(
                {
                    "id": d.doc_id,
                    "score": d.score,
                    "metadata": md,
                    "text": d.text,
                }
            )

        system_prompt = (
            "You are a friendly UAE real estate assistant serving both Arabic and English speakers.\n\n"
            "LANGUAGE RULE — this is the most important rule:\n"
            "- Detect the language of the user's query.\n"
            "- If the query is in Arabic, respond ENTIRELY in Arabic. Every word of your response must be Arabic.\n"
            "- If the query is in English, respond ENTIRELY in English.\n"
            "- Never mix languages in a single response.\n"
            "- Property-specific terms that have no Arabic equivalent may remain as-is: "
            "AED, sqft, Off-Plan, Ready. All Dubai area names (Dubai Marina, Palm Jumeirah, DIFC, etc.) "
            "remain in their original form regardless of response language.\n\n"
            "FORMAT RULE — apply in whichever language you are responding in:\n"
            "1) Start with a short 2-3 sentence summary paragraph describing the overall results "
            "(price range, locations, what the listings have in common, and any key trade-offs).\n"
            "2) Then add a heading line: 'Top matches' (or 'أفضل النتائج' in Arabic). "
            "On the following lines, output a clean numbered list "
            "where each listing is ONE line in this exact format:\n"
            "[Price] · [beds] beds · [City] · [Area] · [Property Type] · [Community/Building]\n"
            "For example: 3,750,000 · 2 beds · Dubai · Dubai Marina · Apartment · Marina Shores\n"
            "3) End with ONE short follow-up sentence asking a clarifying question, "
            "but only if it is relevant.\n\n"
            "RULES:\n"
            "- Do NOT use bold text on property names.\n"
            "- Do NOT include per-listing descriptions or long breakdowns.\n"
            "- Do NOT output bullet-point trade-off sections.\n"
            "- Do NOT output numbered lists of follow-up questions.\n"
            "- Keep the entire response short and very easy to scan."
        )
        messages = [{"role": "system", "content": system_prompt}]
        if memory:
            messages.append(
                {
                    "role": "user",
                    "content": "Conversation context (last messages):\n" + json.dumps(memory, ensure_ascii=False),
                }
            )
        messages.append(
            {
                "role": "user",
                "content": (
                    "User query:\n"
                    f"{user_query}\n\n"
                    "Top candidate listings (JSON):\n"
                    f"{json.dumps(listings_payload, ensure_ascii=False)}"
                ),
            }
        )

        resp = self.client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0.4,
            messages=messages,
        )
        answer = resp.choices[0].message.content or ""

        return {
            "answer": answer,
            "matches": listings_payload,
            "expanded_queries": expanded,
        }


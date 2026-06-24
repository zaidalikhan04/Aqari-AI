import os
import pickle
import re

from dotenv import load_dotenv
import numpy as np
import pandas as pd

load_dotenv()

DATA_CSV_PATH = os.path.join("data", "uae-housing_dataset.csv")
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

BM25_INDEX_PATH = os.path.join("data", "bm25_index.pkl")
BM25_DOCS_PATH = os.path.join("data", "bm25_docs.pkl")
EMBEDDINGS_PATH = os.path.join("data", "embeddings.npy")
METADATAS_PATH = os.path.join("data", "metadatas.npy")

_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def _row_to_text(row: pd.Series) -> str:
    parts = []
    for k, v in row.items():
        if pd.isna(v):
            continue
        s = str(v).strip()
        if not s:
            continue
        parts.append(f"{k}: {s}")
    return " | ".join(parts)


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def main() -> None:
    os.makedirs("data", exist_ok=True)

    df = pd.read_csv(DATA_CSV_PATH)
    df = df.fillna("")
    records = df.to_dict(orient="records")

    documents: list[str] = []
    metadatas: list[dict] = []

    for i, rec in enumerate(records):
        doc = _row_to_text(pd.Series(rec))
        documents.append(doc)
        md = dict(rec)
        md["row_index"] = i
        metadatas.append(md)

    print(f"Loaded {len(documents)} listings from {DATA_CSV_PATH}")

    # --- Build embeddings matrix (pure numpy, no ChromaDB/hnswlib)
    from sentence_transformers import SentenceTransformer

    embedder = SentenceTransformer(EMBED_MODEL_NAME)
    print("Encoding documents...")
    embeddings = embedder.encode(documents, batch_size=64, show_progress_bar=True)
    np.save(EMBEDDINGS_PATH, embeddings)
    np.save(METADATAS_PATH, np.array(metadatas, dtype=object), allow_pickle=True)
    print(f"Saved embeddings: {embeddings.shape} -> {EMBEDDINGS_PATH}")

    # --- Build BM25 index
    from rank_bm25 import BM25Okapi

    tokenized = [_tokenize(d) for d in documents]
    bm25 = BM25Okapi(tokenized)

    with open(BM25_INDEX_PATH, "wb") as f:
        pickle.dump(bm25, f)
    with open(BM25_DOCS_PATH, "wb") as f:
        pickle.dump(documents, f)
    with open(os.path.join("data", "docs_meta.pkl"), "wb") as f:
        pickle.dump(metadatas, f)

    print(f"Saved BM25 index -> {BM25_INDEX_PATH}")
    print(f"Saved docs -> {BM25_DOCS_PATH}")
    print("Ingest complete.")


if __name__ == "__main__":
    main()

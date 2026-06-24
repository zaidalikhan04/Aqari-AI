# AqariAI — Dubai Property Intelligence

> Hybrid AI-powered real estate search for the UAE market, built with Llama 3.3 · Groq · BM25 · Sentence Transformers

---

## Overview

AqariAI is a conversational property search platform that lets users find UAE real estate listings using natural language. It combines BM25 keyword search, dense vector retrieval, and cross-encoder reranking into a single hybrid pipeline — then generates summarised answers via Llama 3.3 on Groq.

The React frontend provides a chat interface, a market analytics dashboard, and a side-by-side property comparison tool.

---

## Screenshots

### Chat — Conversational Property Search
![Chat interface showing studio apartments search results in Dubai](assets/chat.png)

Ask anything in plain English (or Arabic). The system expands your query, retrieves the top matches from 5,380 UAE listings, reranks them, and returns a concise summary with property cards.

### Analytics — Market Intelligence Dashboard
![Analytics dashboard showing median price by area, supply by property type, and KPI cards](assets/analytics.png)

Live KPIs (total listings, average price, premium area, value density) and four interactive Recharts visualisations — all driven directly from the dataset.

### Compare — Side-by-Side Property Comparison
![Property comparison table showing two studio apartments side by side](assets/compare.png)

Add up to 3 properties from search results and compare them attribute-by-attribute. The best price and best price-per-sqft are highlighted automatically.

---

## Architecture

```
User query
    │
    ▼
Query Expansion (Llama 3.3 via Groq)    ← generates 3 rephrased variants
    │
    ▼
Hybrid Retrieval (per variant)
  ├── BM25 (rank-bm25)                  ← lexical keyword match
  └── Vector Search (numpy cosine)      ← semantic similarity via all-MiniLM-L6-v2
    │
    ▼
RRF Fusion                              ← Reciprocal Rank Fusion across all variants
    │
    ▼
Cross-Encoder Reranking                 ← ms-marco-MiniLM-L-6-v2 rescores top 10
    │
    ▼
Answer Generation (Llama 3.3 via Groq)  ← structured summary + top matches
    │
    ▼
React Frontend (Flask API)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Llama 3.3 70B via Groq |
| Embeddings | `all-MiniLM-L6-v2` (sentence-transformers) |
| Reranking | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Keyword search | BM25 (rank-bm25) |
| Vector search | NumPy cosine similarity |
| Backend | Flask (Python 3.12) |
| Frontend | React 18, Recharts, Axios |
| Dataset | 5,380 UAE property listings |

---

## Project Structure

```
AqariAI-final/
├── api.py               # Flask REST API (/search, /stats, /health)
├── rag_chain.py         # 4-stage RAG pipeline
├── ingest.py            # Builds BM25 index + numpy embedding matrix
├── data/
│   ├── uae-housing_dataset.csv
│   ├── embeddings.npy   # (5380, 384) float32 embedding matrix
│   ├── docs_meta.pkl    # per-listing metadata
│   ├── bm25_index.pkl
│   └── bm25_docs.pkl
└── frontend/
    ├── src/
    │   ├── App.js
    │   ├── api.js
    │   └── components/
    │       ├── ChatPage.js
    │       ├── AnalyticsPage.js
    │       ├── ComparePage.js
    │       └── Sidebar.js
    └── package.json
```

---

## Getting Started

### Prerequisites
- Python 3.12
- Node.js 18+
- Groq API key (free at [console.groq.com](https://console.groq.com))

### 1. Clone & configure

```bash
git clone https://github.com/zaidalikhan04/Aqari-AI.git
cd Aqari-AI/AqariAI-final
cp .env.example .env
# Add your GROQ_API_KEY to .env
```

### 2. Install Python dependencies

```bash
pip install flask flask-cors openai "sentence-transformers==3.0.1" rank-bm25 pandas python-dotenv numpy
```

### 3. Build the search index

```bash
set USE_TF=0        # Windows
python ingest.py
```

This encodes all 5,380 listings (~90 seconds) and saves `embeddings.npy`, `docs_meta.pkl`, and BM25 artifacts to `data/`.

### 4. Start the backend

```bash
set USE_TF=0
python api.py
# Running on http://localhost:8000
```

### 5. Start the frontend

```bash
cd frontend
npm install
npm start
# Running on http://localhost:3000
```

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/search` | POST | RAG-powered property search |
| `/stats` | GET | Aggregated market statistics |

### POST /search

```json
{
  "query": "furnished 2BR in Dubai Marina under 2M",
  "chat_history": [],
  "filters": {
    "max_price": 2000000,
    "property_type": "Apartment",
    "furnishing": "Furnished"
  }
}
```

---

## Dataset

5,380 UAE property listings covering Dubai, Abu Dhabi, and Sharjah with fields: price, bedrooms, bathrooms, area (sqft), city, neighbourhood, property type, furnishing, completion status, project name, and handover date.

---

## License

MIT

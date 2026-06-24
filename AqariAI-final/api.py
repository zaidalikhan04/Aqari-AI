import os
from dotenv import load_dotenv

load_dotenv()

import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS

from rag_chain import PropertyRAG

app = Flask(__name__)
CORS(app)

rag = PropertyRAG()


def _build_chroma_filters(f: dict) -> dict:
    where = {}
    if f.get("max_price") is not None:
        where["price"] = where.get("price", {})
        where["price"]["$lte"] = float(f["max_price"])
    if f.get("min_price") is not None:
        where["price"] = where.get("price", {})
        where["price"]["$gte"] = float(f["min_price"])
    if f.get("property_type") and f["property_type"].lower() not in {"all", "any"}:
        where["propert_type"] = f["property_type"]
    if f.get("furnishing") and f["furnishing"].lower() not in {"all", "any"}:
        where["furnishing"] = f["furnishing"]
    if f.get("completion_status") and f["completion_status"].lower() not in {"all", "any"}:
        where["completion_status"] = f["completion_status"]
    return where


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/search")
def search():
    data = request.get_json(force=True)
    query = data.get("query", "")
    chat_history = data.get("chat_history", [])
    filters = _build_chroma_filters(data.get("filters") or {})

    result = rag.query(
        user_query=query,
        chat_history=chat_history,
        filters=filters or None,
    )
    return jsonify({
        "answer": result.get("answer"),
        "matches": result.get("matches", []),
        "expanded_queries": result.get("expanded_queries", []),
    })


@app.get("/stats")
def stats():
    df = pd.read_csv("data/uae-housing_dataset.csv")

    df["price"] = (
        df["price"].astype(str).str.replace(",", "", regex=False).str.strip()
    )
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["price"])

    total_listings = int(len(df))
    avg_price = float(df["price"].mean()) if total_listings else 0.0

    top_areas = (
        df["address"].value_counts().head(5).index.astype(str).tolist()
        if "address" in df.columns else []
    )

    property_types = (
        sorted(df["propert_type"].dropna().astype(str).unique().tolist())
        if "propert_type" in df.columns else []
    )

    if "area(sqft)" in df.columns:
        area_col = "area(sqft)"
        df[area_col] = (
            df[area_col].astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("sqft", "", case=False, regex=False)
            .str.strip()
        )
        df[area_col] = pd.to_numeric(df[area_col], errors="coerce")
        df = df.dropna(subset=[area_col])
        df = df[df[area_col] > 0]
        df["price_per_sqft"] = df["price"] / df[area_col]
    else:
        df["price_per_sqft"] = None

    price_by_area = []
    if "address" in df.columns:
        grouped = (
            df.groupby("address", as_index=False)
            .agg(median_price=("price", "median"))
            .sort_values("median_price", ascending=False)
            .head(10)
        )
        price_by_area = [
            {"area": str(row["address"]), "median_price": float(row["median_price"])}
            for _, row in grouped.iterrows()
        ]

    type_breakdown = []
    if "propert_type" in df.columns:
        tb = df["propert_type"].value_counts().reset_index()
        tb.columns = ["type", "count"]
        type_breakdown = [
            {"type": str(row["type"]), "count": int(row["count"])}
            for _, row in tb.iterrows()
        ]

    price_per_sqft = []
    if "price_per_sqft" in df.columns and "address" in df.columns:
        pps = (
            df.dropna(subset=["price_per_sqft"])
            .groupby("address", as_index=False)
            .agg(avg_price_sqft=("price_per_sqft", "mean"))
            .sort_values("avg_price_sqft", ascending=False)
            .head(10)
        )
        price_per_sqft = [
            {"area": str(row["address"]), "avg_price_sqft": float(row["avg_price_sqft"])}
            for _, row in pps.iterrows()
        ]

    bins = [
        (0, 500_000, "Under 500K"),
        (500_000, 1_000_000, "500K-1M"),
        (1_000_000, 2_000_000, "1M-2M"),
        (2_000_000, 5_000_000, "2M-5M"),
        (5_000_000, float("inf"), "5M+"),
    ]

    def bucket_price(p):
        for low, high, label in bins:
            if low <= p < high:
                return label
        return "Other"

    df["price_bucket"] = df["price"].apply(bucket_price)
    pb_counts = df["price_bucket"].value_counts().reindex([b[2] for b in bins], fill_value=0)
    price_buckets = [
        {"range": str(idx), "count": int(count)} for idx, count in pb_counts.items()
    ]

    return jsonify({
        "total_listings": total_listings,
        "avg_price": avg_price,
        "top_areas": top_areas,
        "property_types": property_types,
        "price_by_area": price_by_area,
        "type_breakdown": type_breakdown,
        "price_per_sqft": price_per_sqft,
        "price_buckets": price_buckets,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=False)

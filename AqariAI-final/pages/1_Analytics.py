import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


DATA_CSV_PATH = os.path.join("data", "uae-housing_dataset.csv")


def _load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_CSV_PATH)

    # Strip whitespace from all string columns
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()

    # Clean price
    df["price"] = (
        df["price"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0).astype(int)
    df = df[df["price"] > 0]

    # Clean area(sqft)
    area_col = "area(sqft)"
    df[area_col] = (
        df[area_col]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("sqft", "", case=False, regex=False)
        .str.strip()
    )
    df[area_col] = pd.to_numeric(df[area_col], errors="coerce")
    df = df[df[area_col] > 0]

    # Rename columns
    df = df.rename(columns={"propert_type": "property_type", "address": "neighbourhood"})

    # Price per sqft
    df["price_per_sqft"] = df["price"] / df[area_col]

    return df


def _luxury_analytics_css() -> str:
    return """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Syne:wght@600;700&display=swap');

      :root {
        --aq-bg: #0D0F14;
        --aq-sidebar: #090B0F;
        --aq-card: #1A1D24;
        --aq-border: #2A2D35;
        --aq-gold: #C9A84C;
        --aq-text: #F0EDE6;
        --aq-muted: #6B7280;
      }

      .stApp {
        background: radial-gradient(circle at 80% 0%, rgba(120, 20, 20, 0.15), transparent 55%), var(--aq-bg);
        color: var(--aq-text);
        font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      }

      [data-testid="stSidebar"] {
        background: var(--aq-sidebar);
        border-right: 1px solid #171923;
      }

      .aq-analytics-logo {
        padding: 1.4rem 0.5rem 0.7rem 0.5rem;
        font-family: 'Syne', system-ui, sans-serif;
        font-weight: 700;
        font-size: 1.15rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }
      .aq-analytics-logo span {
        color: rgba(201, 168, 76, 0.9);
      }
      .aq-analytics-divider {
        border: none;
        border-top: 1px solid rgba(201, 168, 76, 0.4);
        margin: 0.4rem 0 0.9rem 0;
      }
      .aq-sidebar-section-label {
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.18em;
        color: var(--aq-muted);
        margin: 0.4rem 0 0.15rem 0;
      }

      .stMetric {
        background: var(--aq-card);
        border-radius: 14px;
        padding: 0.85rem 0.9rem;
        border: 1px solid var(--aq-border);
      }

      .stSelectbox > div[data-baseweb="select"] > div {
        background: #11131A;
        border-radius: 999px;
        border: 1px solid var(--aq-border);
        color: var(--aq-text);
      }
      .stSelectbox > div[data-baseweb="select"] > div:focus-within {
        border-color: var(--aq-gold);
        box-shadow: 0 0 0 1px var(--aq-gold);
      }

      .stSlider > div > div > div[data-baseweb="slider"] > div {
        background: #11131A;
      }
      .stSlider [data-baseweb="slider"] > div:nth-child(2) > div {
        background-color: rgba(201, 168, 76, 0.7);
      }
      .stSlider [data-baseweb="slider"] span[data-baseweb="thumb"] {
        background-color: var(--aq-gold);
        box-shadow: 0 0 0 1px #000;
      }

      .aq-analytics-hero {
        padding: 0.6rem 0 0.7rem 0;
      }
      .aq-analytics-title {
        font-family: 'Syne', system-ui, sans-serif;
        font-size: 1.7rem;
        font-weight: 700;
        letter-spacing: 0.04em;
      }
      .aq-analytics-sub {
        color: var(--aq-muted);
        margin-top: 0.18rem;
        font-size: 0.9rem;
      }
      .aq-analytics-divider-main {
        border: none;
        border-top: 1px solid rgba(201, 168, 76, 0.6);
        margin: 0.6rem 0 0.4rem 0;
        max-width: 260px;
      }
    </style>
    """


def _apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.markdown(
        '<div class="aq-analytics-logo">Aqari<span>AI</span> · Insights</div>'
        '<hr class="aq-analytics-divider" />',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown('<div class="aq-sidebar-section-label">Filters</div>', unsafe_allow_html=True)

    # Property type filter
    all_types = sorted(df["property_type"].dropna().unique().tolist())
    selected_types = st.sidebar.multiselect(
        "Property type",
        options=all_types,
        default=all_types,
    )

    # Price range filter
    min_price = int(df["price"].min())
    max_price = int(df["price"].max())
    price_range = st.sidebar.slider(
        "Price range (AED)",
        min_value=min_price,
        max_value=max_price,
        value=(min_price, max_price),
        step=50000,
    )

    mask = (df["price"] >= price_range[0]) & (df["price"] <= price_range[1])
    if selected_types:
        mask &= df["property_type"].isin(selected_types)

    return df[mask].copy()


def _render_kpis(df: pd.DataFrame) -> None:
    total_listings = len(df)
    avg_price = int(df["price"].mean()) if total_listings else 0
    median_pps = float(df["price_per_sqft"].median()) if total_listings else 0.0
    most_listed_area = (
        df["neighbourhood"].value_counts().idxmax() if total_listings else "N/A"
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Listings", f"{total_listings:,}")
    c2.metric("Avg Price (AED)", f"{avg_price:,.0f}")
    c3.metric("Median Price/sqft (AED)", f"{median_pps:,.0f}")
    c4.metric("Most Listed Area", most_listed_area)


def _chart_price_by_neighbourhood(df: pd.DataFrame) -> go.Figure:
    grouped = (
        df.groupby("neighbourhood", as_index=False)
        .agg(median_price=("price", "median"))
        .sort_values("median_price", ascending=False)
        .head(15)
    )
    fig = px.bar(
        grouped,
        x="median_price",
        y="neighbourhood",
        orientation="h",
        color="median_price",
        color_continuous_scale="Teal",
        title="Median listing price by neighbourhood",
        labels={"median_price": "Median price (AED)", "neighbourhood": "Neighbourhood"},
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        coloraxis_showscale=False,
    )
    fig.update_yaxes(autorange="reversed")
    return fig


def _chart_property_type_donut(df: pd.DataFrame) -> go.Figure:
    grouped = df["property_type"].value_counts().reset_index()
    grouped.columns = ["property_type", "count"]
    fig = px.pie(
        grouped,
        values="count",
        names="property_type",
        hole=0.5,
        title="Supply by property type",
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        showlegend=False,
    )
    return fig


def _chart_avg_pps_by_neighbourhood(df: pd.DataFrame) -> go.Figure:
    grouped = (
        df.groupby("neighbourhood", as_index=False)
        .agg(avg_pps=("price_per_sqft", "mean"))
        .sort_values("avg_pps", ascending=False)
        .head(15)
    )
    fig = px.bar(
        grouped,
        x="avg_pps",
        y="neighbourhood",
        orientation="h",
        color="avg_pps",
        color_continuous_scale="OrRd",
        title="Avg price per sqft — top 15 areas",
        labels={"avg_pps": "Avg price/sqft (AED)", "neighbourhood": "Neighbourhood"},
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        coloraxis_showscale=False,
    )
    fig.update_yaxes(autorange="reversed")
    return fig


def _chart_price_range_heatmap(df: pd.DataFrame) -> go.Figure:
    bins = [
        (0, 500_000, "Under 500K"),
        (500_000, 1_000_000, "500K-1M"),
        (1_000_000, 2_000_000, "1M-2M"),
        (2_000_000, 5_000_000, "2M-5M"),
        (5_000_000, float("inf"), "5M+"),
    ]

    def bucket_price(p: float) -> str:
        for low, high, label in bins:
            if low <= p < high:
                return label
        return "Other"

    df = df.copy()
    df["price_bucket"] = df["price"].apply(bucket_price)

    pivot = (
        df.pivot_table(
            index="property_type",
            columns="price_bucket",
            values="price",
            aggfunc="count",
            fill_value=0,
        )
        .reindex(columns=[b[2] for b in bins])
        .fillna(0)
    )

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale="Blues",
            colorbar=dict(title="Listings"),
        )
    )
    fig.update_layout(
        title="Listing density by type and price range",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
    )
    return fig


def main() -> None:
    st.set_page_config(page_title="Dubai Property Market Intelligence", layout="wide")
    st.markdown(_luxury_analytics_css(), unsafe_allow_html=True)

    st.markdown(
        """
        <div class="aq-analytics-hero">
          <div class="aq-analytics-title">Dubai Property Market Intelligence</div>
          <div class="aq-analytics-sub">High-level pricing, supply, and density insights across Dubai neighbourhoods.</div>
          <hr class="aq-analytics-divider-main" />
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = _load_data()
    df_filtered = _apply_filters(df)

    _render_kpis(df_filtered)
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(_chart_price_by_neighbourhood(df_filtered), use_container_width=True)
    with col2:
        st.plotly_chart(_chart_property_type_donut(df_filtered), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(_chart_avg_pps_by_neighbourhood(df_filtered), use_container_width=True)
    with col4:
        st.plotly_chart(_chart_price_range_heatmap(df_filtered), use_container_width=True)


if __name__ == "__main__":
    main()


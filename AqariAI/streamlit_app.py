import streamlit as st

from rag_chain import PropertyRAG


SUGGESTED_QUERIES = [
    "Studio under AED 500K",
    "Furnished 2BR Marina",
    "Villa DAMAC Hills",
    "Off-plan penthouse",
]


def _luxury_theme_css() -> str:
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

      .aq-logo-wrap {
        padding: 1.5rem 0.5rem 0.5rem 0.5rem;
      }
      .aq-logo {
        display: flex;
        align-items: center;
        gap: 0.6rem;
      }
      .aq-logo-icon {
        width: 26px;
        height: 26px;
        border-radius: 8px;
        border: 1px solid rgba(201, 168, 76, 0.75);
        display: flex;
        align-items: center;
        justify-content: center;
        background: radial-gradient(circle at 30% 0%, rgba(201,168,76,0.28), transparent 70%);
      }
      .aq-logo-icon-inner {
        width: 10px;
        height: 10px;
        border-radius: 3px;
        border: 2px solid var(--aq-gold);
        transform: rotate(45deg);
      }
      .aq-logo-text-main {
        font-family: 'Syne', system-ui, sans-serif;
        font-weight: 700;
        font-size: 1.4rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      .aq-logo-text-sub {
        font-family: 'Syne', system-ui, sans-serif;
        font-weight: 500;
        font-size: 0.75rem;
        color: rgba(201, 168, 76, 0.8);
        margin-top: 0.15rem;
      }
      .aq-sidebar-divider {
        border: none;
        border-top: 1px solid rgba(201, 168, 76, 0.4);
        margin: 0.75rem 0 1.25rem 0;
      }
      .aq-sidebar-section-label {
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.18em;
        color: var(--aq-muted);
        margin: 0.5rem 0 0.25rem 0;
      }

      /* Inputs and selects */
      .stTextInput > div > div > input,
      .stChatInput textarea {
        background: #1A1D24 !important;
        border-radius: 999px !important;
        border: 1px solid var(--aq-border) !important;
        color: var(--aq-text) !important;
      }
      .stTextInput > div > div > input:focus-visible,
      .stChatInput textarea:focus-visible {
        outline: none !important;
        border-color: var(--aq-gold) !important;
        box-shadow: 0 0 0 1px var(--aq-gold) !important;
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

      /* Buttons */
      .stButton > button {
        background: transparent;
        border-radius: 999px;
        border: 1px solid rgba(201, 168, 76, 0.35);
        color: var(--aq-text);
        padding: 0.35rem 0.9rem;
        font-size: 0.8rem;
      }
      .stButton > button:hover {
        border-color: var(--aq-gold);
        background: rgba(201, 168, 76, 0.08);
        color: var(--aq-text);
      }

      .aq-hero {
        padding: 1.25rem 0 0.75rem 0;
      }
      .aq-hero-title {
        font-family: 'Syne', system-ui, sans-serif;
        font-size: 2.1rem;
        font-weight: 700;
        letter-spacing: 0.03em;
      }
      .aq-hero-sub {
        color: var(--aq-muted);
        margin-top: 0.25rem;
        font-size: 0.9rem;
      }
      .aq-hero-divider {
        border: none;
        border-top: 1px solid rgba(201, 168, 76, 0.6);
        margin: 0.75rem 0 0.75rem 0;
        max-width: 220px;
      }

      .aq-chat-container {
        margin-top: 0.5rem;
      }

      .aq-bubble-row {
        display: flex;
        margin-bottom: 0.6rem;
      }
      .aq-bubble-user {
        margin-left: auto;
        max-width: 78%;
        background: #1A1D24;
        border-radius: 16px;
        padding: 0.6rem 0.9rem;
        border-left: 3px solid rgba(201, 168, 76, 0.7);
      }
      .aq-bubble-assistant {
        margin-right: auto;
        max-width: 82%;
        background: #141720;
        border-radius: 16px;
        padding: 0.6rem 0.9rem;
        border-left: 3px solid var(--aq-gold);
      }

      .aq-listing-card {
        border-radius: 16px;
        background: #1A1D24;
        border: 1px solid var(--aq-border);
        padding: 0.75rem 0.9rem 0.7rem 0.9rem;
        margin-top: 0.55rem;
        transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.1s ease;
      }
      .aq-listing-card:hover {
        border-color: var(--aq-gold);
        box-shadow: 0 4px 24px rgba(201, 168, 76, 0.08);
        transform: translateY(-1px);
      }
      .aq-listing-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.35rem;
      }
      .aq-listing-price {
        font-weight: 600;
        color: var(--aq-gold);
        font-size: 1.0rem;
      }
      .aq-badge {
        border-radius: 999px;
        padding: 0.12rem 0.65rem;
        border: 1px solid rgba(201, 168, 76, 0.7);
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: rgba(201, 168, 76, 0.9);
      }
      .aq-listing-row {
        font-size: 0.75rem;
        color: var(--aq-text);
        opacity: 0.92;
      }
      .aq-listing-row-muted {
        font-size: 0.75rem;
        color: var(--aq-muted);
      }
      .aq-listing-bottom {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 0.4rem;
        gap: 0.6rem;
      }
      .aq-score-bar {
        flex: 1;
        height: 4px;
        border-radius: 999px;
        background: #11131A;
        overflow: hidden;
      }
      .aq-score-bar-inner {
        height: 100%;
        background: linear-gradient(90deg, rgba(201, 168, 76, 0.35), var(--aq-gold));
      }
      .aq-score-label {
        font-size: 0.7rem;
        color: var(--aq-muted);
        margin-left: 0.3rem;
        white-space: nowrap;
      }

      .aq-typing {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        margin-top: 0.25rem;
      }
      .aq-typing-dot {
        width: 6px;
        height: 6px;
        border-radius: 999px;
        background: var(--aq-gold);
        opacity: 0.8;
        animation: aq-bounce 1.2s infinite ease-in-out;
      }
      .aq-typing-dot:nth-child(2) { animation-delay: 0.15s; }
      .aq-typing-dot:nth-child(3) { animation-delay: 0.3s; }

      @keyframes aq-bounce {
        0%, 60%, 100% { transform: translateY(0); opacity: 0.3; }
        30% { transform: translateY(-4px); opacity: 1; }
      }

      .aq-footer {
        font-size: 0.7rem;
        color: var(--aq-muted);
        margin-top: 1.5rem;
      }
    </style>
    """


@st.cache_resource
def _get_rag() -> PropertyRAG:
    return PropertyRAG()


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="aq-logo-wrap">
              <div class="aq-logo">
                <div class="aq-logo-icon">
                  <div class="aq-logo-icon-inner"></div>
                </div>
                <div>
                  <div class="aq-logo-text-main">AqariAI</div>
                  <div class="aq-logo-text-sub">أقاري</div>
                </div>
              </div>
            </div>
            <hr class="aq-sidebar-divider" />
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="aq-sidebar-section-label">Search</div>', unsafe_allow_html=True)

        # Filters (UI only, core RAG logic kept unchanged)
        st.slider("Max price (AED)", min_value=200_000, max_value=10_000_000, value=5_000_000, step=100_000)
        st.selectbox(
            "Property type",
            options=["Any", "Apartment", "Villa", "Townhouse", "Penthouse", "Studio"],
            index=0,
        )
        st.selectbox(
            "Furnishing",
            options=["Any", "Furnished", "Unfurnished"],
            index=0,
        )
        st.selectbox(
            "Completion status",
            options=["Any", "Ready", "Off-Plan"],
            index=0,
        )

        st.markdown('<div class="aq-sidebar-section-label" style="margin-top:1.25rem;">Suggested</div>', unsafe_allow_html=True)
        for q in SUGGESTED_QUERIES:
            if st.button(q, use_container_width=True, key=f"suggest_{q}"):
                st.session_state.pending_query = q

        st.markdown(
            '<div class="aq-footer">Powered by Llama 3.3 · ChromaDB · Groq</div>',
            unsafe_allow_html=True,
        )


def _render_chat_history() -> None:
    st.markdown('<div class="aq-chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        bubble_class = "aq-bubble-user" if role == "user" else "aq-bubble-assistant"
        st.markdown(
            f"""
            <div class="aq-bubble-row">
              <div class="{bubble_class}">
                {content}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def _render_listing_cards(matches: list[dict]) -> None:
    if not matches:
        return

    # Normalise scores for progress bar
    scores = [m.get("score") for m in matches if isinstance(m.get("score"), (int, float))]
    max_score = max(scores) if scores else 1.0

    for m in matches:
        md = m.get("metadata", {}) or {}
        price = md.get("price", "")
        beds = md.get("bedroom", "")
        baths = md.get("bathroom", "")
        area = md.get("area(sqft)", "")
        city = md.get("city", "")
        neighbourhood = md.get("address", "") or md.get("neighbourhood", "")
        ptype = md.get("propert_type", "") or md.get("property_type", "")
        project = md.get("project_name", "")
        score = m.get("score", 0.0)
        pct = 0 if not max_score else max(min(score / max_score, 1.0), 0.0) * 100

        st.markdown(
            f"""
            <div class="aq-listing-card">
              <div class="aq-listing-top">
                <div class="aq-listing-price">{price}</div>
                <div class="aq-badge">{ptype or "Property"}</div>
              </div>
              <div class="aq-listing-row">
                {beds or "?"} beds · {baths or "?"} baths · {area or "?"} sqft
              </div>
              <div class="aq-listing-row-muted">
                📍 {city}{(" · " + neighbourhood) if neighbourhood else ""}
              </div>
              <div class="aq-listing-bottom">
                <div class="aq-listing-row-muted" style="flex:0 0 auto; max-width:50%;">
                  {project or ""}
                </div>
                <div class="aq-score-bar">
                  <div class="aq-score-bar-inner" style="width:{pct:.0f}%;"></div>
                </div>
                <div class="aq-score-label">Match</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def main() -> None:
    st.set_page_config(page_title="AqariAI · Dubai Property Intelligence", page_icon="🏙️", layout="wide")
    st.markdown(_luxury_theme_css(), unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    _render_sidebar()

    # Hero header
    st.markdown(
        """
        <div class="aq-hero">
          <div class="aq-hero-title">Dubai Property Intelligence</div>
          <div class="aq-hero-sub">Ask anything about UAE real estate — powered by hybrid AI search.</div>
          <hr class="aq-hero-divider" />
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_chat_history()

    # Input (either from suggested searches or chat box)
    pending = st.session_state.pop("pending_query", None) if "pending_query" in st.session_state else None
    user_text = pending or st.chat_input("Describe your ideal property in Dubai...")
    if not user_text:
        return

    st.session_state.chat_history.append({"role": "user", "content": user_text})

    # Assistant response with typing indicator and listing cards
    typing_placeholder = st.empty()
    typing_placeholder.markdown(
        """
        <div class="aq-bubble-row">
          <div class="aq-bubble-assistant">
            <div class="aq-typing">
              <div class="aq-typing-dot"></div>
              <div class="aq-typing-dot"></div>
              <div class="aq-typing-dot"></div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.spinner("Searching listings..."):
        rag = _get_rag()
        result = rag.query(user_text, chat_history=st.session_state.chat_history, filters=None)
        answer = result.get("answer", "")
        matches = result.get("matches", [])

    typing_placeholder.empty()

    # Render assistant message bubble
    st.markdown(
        f"""
        <div class="aq-bubble-row">
          <div class="aq-bubble-assistant">
            {answer or "_No answer returned._"}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_listing_cards(matches)

    st.session_state.chat_history.append({"role": "assistant", "content": answer or "_No answer returned._"})


if __name__ == "__main__":
    main()


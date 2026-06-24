import React, { useState } from "react";
import { searchProperties } from "../api";

const SUGGESTED = [
  "Cheapest studios in Dubai",
  "Furnished 2BR Dubai Marina",
  "Villa in DAMAC Hills",
  "Off-plan penthouse",
];

function clampScoreToPercent(score) {
  const min = -5;
  const max = 15;
  if (typeof score !== "number" || Number.isNaN(score)) return 50;
  const clamped = Math.min(max, Math.max(min, score));
  return ((clamped - min) / (max - min)) * 100;
}

function normaliseFilters(filters) {
  return {
    max_price: filters.max_price ? Number(filters.max_price) : null,
    min_price: filters.min_price ? Number(filters.min_price) : null,
    property_type:
      filters.property_type && filters.property_type !== "All"
        ? filters.property_type
        : null,
    furnishing:
      filters.furnishing && filters.furnishing !== "All"
        ? filters.furnishing
        : null,
    completion_status:
      filters.completion_status && filters.completion_status !== "All"
        ? filters.completion_status
        : null,
  };
}

function ChatPage({
  filters,
  messages,
  setMessages,
  chatHistory,
  setChatHistory,
  loading,
  setLoading,
  compareList,
  addToCompare,
  removeFromCompare,
}) {
  const [input, setInput] = useState("");

  const renderAssistantContent = (text) => {
    if (!text) return null;
    const lines = text.split("\n").filter((l) => l.trim().length > 0);

    return lines.map((line, idx) => {
      const trimmed = line.trim();
      if (trimmed.startsWith("##")) {
        const label = trimmed.replace(/^##\s*/, "");
        return (
          <div key={`h-${idx}`} style={{ fontWeight: 600, marginBottom: "0.25rem" }}>
            {label}
          </div>
        );
      }

      const match = trimmed.match(/^(\d+)\.\s+(.*)$/);
      if (match) {
        return (
          <div
            key={`li-${idx}`}
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "0.4rem",
              fontSize: "0.88rem",
            }}
          >
            <span
              style={{
                marginTop: "0.25rem",
                width: 6,
                height: 6,
                borderRadius: "999px",
                backgroundColor: "#C9A84C",
                flexShrink: 0,
              }}
            />
            <span>{match[2]}</span>
          </div>
        );
      }

      return (
        <div key={`p-${idx}`} style={{ marginBottom: "0.25rem" }}>
          {trimmed}
        </div>
      );
    });
  };

  const handleSend = async (text) => {
    const trimmed = (text ?? input).trim();
    if (!trimmed || loading) return;

    const userMsg = { role: "user", content: trimmed };
    setMessages((prev) => [...prev, { ...userMsg }]);
    setInput("");
    setLoading(true);

    const nextHistory = [...chatHistory, userMsg];
    try {
      const res = await searchProperties(
        trimmed,
        nextHistory,
        normaliseFilters(filters)
      );
      const { answer, matches } = res.data;
      const assistantMsg = {
        role: "assistant",
        content: answer || "",
        matches: matches || [],
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setChatHistory([...nextHistory, { role: "assistant", content: answer }]);
    } catch (err) {
      const assistantMsg = {
        role: "assistant",
        content:
          "Sorry, something went wrong while searching. Please try again in a moment.",
        matches: [],
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggested = (q) => {
    setInput(q);
    handleSend(q);
  };

  return (
    <>
      <section className="hero">
        <div className="hero-title">Dubai Property Intelligence</div>
        <div className="hero-sub">
          Ask anything about UAE real estate — powered by hybrid AI search.
        </div>
        <hr className="hero-divider" />
      </section>

      <section className="chat-container">
        {messages.length === 0 && (
          <div className="suggested-queries">
            {SUGGESTED.map((q) => (
              <button
                key={q}
                className="suggested-pill"
                type="button"
                onClick={() => handleSuggested(q)}
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {messages.map((m, idx) => (
          <div key={idx}>
            <div className="message-row">
              <div
                className={
                  m.role === "user" ? "bubble-user bubble-text" : "bubble-assistant bubble-text"
                }
              >
                {m.role === "assistant" ? renderAssistantContent(m.content) : m.content}
                {m.role === "assistant" && loading && idx === messages.length - 1 && (
                  <div className="loading-dots">
                    <span className="loading-dot" />
                    <span className="loading-dot" />
                    <span className="loading-dot" />
                  </div>
                )}
              </div>
            </div>
            {m.role === "assistant" && Array.isArray(m.matches) && m.matches.length > 0 && (
              <div className="listings-grid">
                {m.matches.map((match, i) => {
                  const md = match.metadata || {};
                  const pct = clampScoreToPercent(match.score);
                  return (
                    <div className="listing-card" key={i}>
                      <div className="listing-top">
                        <div className="listing-price">
                          {md.price || "Price on request"}
                        </div>
                        <div className="type-badge">
                          {md.propert_type || "Property"}
                        </div>
                      </div>
                      <div className="listing-row">
                        {(md.bedroom || "?") +
                          " · " +
                          (md.bathroom || "?") +
                          " · " +
                          (md["area(sqft)"] || "?")}
                      </div>
                      <div className="listing-row-muted">
                        📍 {md.address || md.city || "Dubai"}
                      </div>
                      <div className="listing-bottom">
                        <div className="listing-row-muted" style={{ flex: "0 0 auto" }}>
                          {md.project_name || ""}
                        </div>
                        <div className="score-bar">
                          <div
                            className="score-bar-inner"
                            style={{ width: `${pct.toFixed(0)}%` }}
                          />
                        </div>
                        <div className="score-label">Match</div>
                      </div>
                      {(() => {
                        const isCompared = compareList?.find((p) => p.id === match.id);
                        const atLimit = compareList?.length >= 3 && !isCompared;
                        return (
                          <button
                            type="button"
                            className={`compare-btn ${isCompared ? "compare-btn-active" : ""}`}
                            disabled={atLimit}
                            onClick={() =>
                              isCompared
                                ? removeFromCompare(match.id)
                                : addToCompare({
                                    id: match.id,
                                    metadata: match.metadata,
                                    score: match.score,
                                  })
                            }
                          >
                            {isCompared ? "✓ Added" : atLimit ? "Max 3" : "+ Compare"}
                          </button>
                        );
                      })()}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </section>

      <div className="chat-input-bar">
        <div className="chat-input-inner">
          <input
            className="chat-input"
            type="text"
            value={input}
            placeholder="Describe your ideal property in Dubai..."
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                handleSend();
              }
            }}
          />
          <button
            type="button"
            className="chat-send"
            onClick={() => handleSend()}
            disabled={loading}
          >
            Send
          </button>
        </div>
      </div>
    </>
  );
}

export default ChatPage;


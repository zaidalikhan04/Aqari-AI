import React from "react";

function Sidebar({
  activePage,
  setActivePage,
  collapsed,
  setCollapsed,
  compareCount,
}) {
  return (
    <aside
      className={`layout-sidebar ${collapsed ? "sidebar-collapsed" : ""}`}
    >
      <button
        type="button"
        className="sidebar-toggle-btn"
        onClick={() => setCollapsed?.((prev) => !prev)}
      >
        {collapsed ? "›" : "‹"}
      </button>
      <div>
        <div className="logo-wrap">
          <div className="logo-icon">
            <div className="logo-icon-inner" />
          </div>
          {!collapsed && (
            <div>
              <div className="logo-text-main">AqariAI</div>
              <div className="logo-text-sub">أقاري</div>
            </div>
          )}
        </div>
        <hr className="logo-divider" />

        <nav className="nav-main">
          <div
            className={`nav-item ${activePage === "chat" ? "active" : ""}`}
            onClick={() => setActivePage("chat")}
          >
            <span className="icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
            </span>
            {!collapsed && <span>Chat</span>}
          </div>
          <div
            className={`nav-item ${activePage === "analytics" ? "active" : ""}`}
            onClick={() => setActivePage("analytics")}
          >
            <span className="icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="20" x2="18" y2="10"/>
                <line x1="12" y1="20" x2="12" y2="4"/>
                <line x1="6" y1="20" x2="6" y2="14"/>
              </svg>
            </span>
            {!collapsed && <span>Analytics</span>}
          </div>
          <div
            className={`nav-item ${activePage === "compare" ? "active" : ""}`}
            onClick={() => setActivePage("compare")}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2" strokeLinecap="round"
              strokeLinejoin="round">
              <rect x="2" y="3" width="9" height="18" rx="1"/>
              <rect x="13" y="3" width="9" height="18" rx="1"/>
            </svg>
            {!collapsed && (
              <span>
                Compare
                {compareCount > 0 && (
                  <span className="compare-badge">{compareCount}</span>
                )}
              </span>
            )}
          </div>
        </nav>
      </div>

      <div className="sidebar-footer">
        {!collapsed && "Powered by Llama 3.3 · ChromaDB · Groq"}
      </div>
    </aside>
  );
}

export default Sidebar;


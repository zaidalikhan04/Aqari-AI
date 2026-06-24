import React, { useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatPage from "./components/ChatPage";
import AnalyticsPage from "./components/AnalyticsPage";
import ComparePage from "./components/ComparePage";

function App() {
  const [activePage, setActivePage] = useState("chat");
  const [messages, setMessages] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    max_price: "",
    min_price: "",
    property_type: "All",
    furnishing: "All",
    completion_status: "All",
  });

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [compareList, setCompareList] = useState([]);

  const addToCompare = (property) => {
    setCompareList((prev) => {
      if (prev.find((p) => p.id === property.id)) return prev;
      if (prev.length >= 3) return prev;
      return [...prev, property];
    });
  };

  const removeFromCompare = (id) => {
    setCompareList((prev) => prev.filter((p) => p.id !== id));
  };

  return (
    <div className="app-root">
      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
        compareCount={compareList.length}
      />
      <main className={`layout-main ${sidebarCollapsed ? "main-collapsed" : ""}`}>
        {activePage === "chat" ? (
          <ChatPage
            filters={filters}
            messages={messages}
            setMessages={setMessages}
            chatHistory={chatHistory}
            setChatHistory={setChatHistory}
            loading={loading}
            setLoading={setLoading}
            compareList={compareList}
            addToCompare={addToCompare}
            removeFromCompare={removeFromCompare}
          />
        ) : activePage === "analytics" ? (
          <AnalyticsPage filters={filters} setFilters={setFilters} />
        ) : (
          <ComparePage
            compareList={compareList}
            removeFromCompare={removeFromCompare}
          />
        )}
      </main>
    </div>
  );
}

export default App;


import React, { useEffect, useState, useMemo } from "react";
import { getStats } from "../api";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
} from "recharts";

function formatAED(value) {
  if (value === null || value === undefined) return "-";
  const n = Number(value);
  if (!Number.isFinite(n)) return "-";
  return `AED ${Math.round(n).toLocaleString()}`;
}

const DEFAULTS = {
  max_price: "",
  min_price: "",
  property_type: "All",
  furnishing: "All",
  completion_status: "All",
};

function AnalyticsPage({ filters, setFilters }) {
  const hasActiveFilters =
    (filters?.max_price ?? "") !== DEFAULTS.max_price ||
    (filters?.min_price ?? "") !== DEFAULTS.min_price ||
    (filters?.property_type ?? "All") !== DEFAULTS.property_type ||
    (filters?.furnishing ?? "All") !== DEFAULTS.furnishing ||
    (filters?.completion_status ?? "All") !== DEFAULTS.completion_status;
  const [stats, setStats] = useState(null);

  useEffect(() => {
    getStats()
      .then((res) => setStats(res.data))
      .catch(() => {
        setStats({
          total_listings: 0,
          avg_price: 0,
          top_areas: [],
          property_types: [],
        });
      });
  }, []);

  const total = stats?.total_listings ?? 0;
  const avg = stats?.avg_price ?? 0;
  const typeCount = stats?.property_types?.length ?? 0;
  const priceByArea = stats?.price_by_area || [];
  const supplyLeader =
    stats?.type_breakdown?.reduce((a, b) => (a.count > b.count ? a : b), {})?.area ??
    stats?.top_areas?.[0] ??
    "-";
  const premiumArea =
    stats?.price_by_area?.reduce((a, b) =>
      a.median_price > b.median_price ? a : b,
      {}
    )?.area ?? "-";
  const valueDensity =
    stats?.price_per_sqft?.reduce((a, b) =>
      a.avg_price_sqft > b.avg_price_sqft ? a : b,
      {}
    )?.area ?? "-";
  const typeBreakdown = stats?.type_breakdown || [];
  const pricePerSqft = stats?.price_per_sqft || [];
  const priceBuckets = stats?.price_buckets || [];

  const filteredPriceByArea = useMemo(() => {
    if (!priceByArea.length) return priceByArea;
    return priceByArea.filter((item) => {
      if (filters?.max_price && item.median_price > Number(filters.max_price))
        return false;
      if (filters?.min_price && item.median_price < Number(filters.min_price))
        return false;
      return true;
    });
  }, [priceByArea, filters]);

  const filteredTypeBreakdown = useMemo(() => {
    if (!typeBreakdown.length) return typeBreakdown;
    if (!filters?.property_type || filters.property_type === "All")
      return typeBreakdown;
    return typeBreakdown.filter((item) => item.type === filters.property_type);
  }, [typeBreakdown, filters]);

  const filteredPricePerSqft = useMemo(() => {
    if (!pricePerSqft.length) return pricePerSqft;
    return pricePerSqft.filter((item) => {
      if (
        filters?.max_price &&
        item.avg_price_sqft > Number(filters.max_price) / 100
      )
        return false;
      return true;
    });
  }, [pricePerSqft, filters]);

  const filteredPriceBuckets = useMemo(() => {
    if (!priceBuckets.length) return priceBuckets;
    return priceBuckets;
  }, [priceBuckets, filters]);

  const pieColors = ["#C9A84C", "#FBBF24", "#F97316", "#14B8A6", "#38BDF8", "#A855F7"];

  return (
    <div className="analytics-wrapper">
      <section className="hero">
        <div className="hero-title">Market Intelligence</div>
        <div className="hero-sub">Dubai real estate at a glance.</div>
        <hr className="hero-divider" />
      </section>

      <div className="analytics-filters">
        <input
          type="number"
          placeholder="Max price (AED)"
          value={filters?.max_price ?? ""}
          onChange={(e) =>
            setFilters((prev) => ({ ...prev, max_price: e.target.value }))
          }
        />
        <input
          type="number"
          placeholder="Min price (AED)"
          value={filters?.min_price ?? ""}
          onChange={(e) =>
            setFilters((prev) => ({ ...prev, min_price: e.target.value }))
          }
        />
        <select
          value={filters?.property_type ?? "All"}
          onChange={(e) =>
            setFilters((prev) => ({ ...prev, property_type: e.target.value }))
          }
        >
          {["All", "Apartment", "Villa", "Townhouse", "Penthouse", "Residential Building", "Villa Compound"].map(
            (opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            )
          )}
        </select>
        <select
          value={filters?.furnishing ?? "All"}
          onChange={(e) =>
            setFilters((prev) => ({ ...prev, furnishing: e.target.value }))
          }
        >
          {["All", "Furnished", "Unfurnished"].map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
        <select
          value={filters?.completion_status ?? "All"}
          onChange={(e) =>
            setFilters((prev) => ({
              ...prev,
              completion_status: e.target.value,
            }))
          }
        >
          {["All", "Ready", "Off-Plan"].map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
        {hasActiveFilters && (
          <button
            type="button"
            className="reset-filters-btn"
            onClick={() => setFilters({ ...DEFAULTS })}
          >
            Reset
          </button>
        )}
      </div>

      <section className="kpi-row">
        <div className="kpi-card">
          <div className="kpi-label">Total Listings</div>
          <div className="kpi-value">
            {total ? total.toLocaleString() : "-"}
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Avg Price</div>
          <div className="kpi-value">{formatAED(avg)}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Supply Leader</div>
          <div className="kpi-value">{supplyLeader}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Premium Area</div>
          <div className="kpi-value">{premiumArea}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Value Density</div>
          <div className="kpi-value">{valueDensity}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Property Types</div>
          <div className="kpi-value">{typeCount}</div>
        </div>
      </section>

      <section className="charts-grid">
        <div className="chart-card">
          <strong>Median price by area</strong>
          <div style={{ height: 300, marginTop: "0.35rem" }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={filteredPriceByArea}
                layout="vertical"
                margin={{ top: 10, right: 20, left: 10, bottom: 10 }}
              >
                <CartesianGrid stroke="#2A2D35" horizontal={true} vertical={false} />
                <XAxis type="number" tick={{ fill: "#F0EDE6", fontSize: 11 }} />
                <YAxis
                  dataKey="area"
                  type="category"
                  width={100}
                  tick={{ fill: "#F0EDE6", fontSize: 11 }}
                />
                <Tooltip
                  contentStyle={{ background: "#11131A", border: "1px solid #C9A84C" }}
                  itemStyle={{ color: "#F0EDE6" }}
                />
                <Bar dataKey="median_price" fill="#C9A84C" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-card">
          <strong>Supply by property type</strong>
          <div style={{ height: 300, marginTop: "0.35rem" }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Tooltip
                  contentStyle={{ background: "#11131A", border: "1px solid #C9A84C" }}
                  itemStyle={{ color: "#F0EDE6" }}
                />
                <Pie
                  data={filteredTypeBreakdown}
                  dataKey="count"
                  nameKey="type"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={3}
                  label={(entry) => entry.type}
                >
                  {filteredTypeBreakdown.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={pieColors[index % pieColors.length]}
                    />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-card">
          <strong>Avg price per sqft — top areas</strong>
          <div style={{ height: 300, marginTop: "0.35rem" }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={filteredPricePerSqft}
                layout="vertical"
                margin={{ top: 10, right: 20, left: 10, bottom: 10 }}
              >
                <CartesianGrid stroke="#2A2D35" horizontal={true} vertical={false} />
                <XAxis type="number" tick={{ fill: "#F0EDE6", fontSize: 11 }} />
                <YAxis
                  dataKey="area"
                  type="category"
                  width={120}
                  tick={{ fill: "#F0EDE6", fontSize: 11 }}
                />
                <Tooltip
                  contentStyle={{ background: "#11131A", border: "1px solid #FBBF24" }}
                  itemStyle={{ color: "#F0EDE6" }}
                />
                <Bar dataKey="avg_price_sqft" fill="#FBBF24" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-card">
          <strong>Listing count by price range</strong>
          <div style={{ height: 300, marginTop: "0.35rem" }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={filteredPriceBuckets}
                margin={{ top: 10, right: 20, left: 0, bottom: 10 }}
              >
                <CartesianGrid stroke="#2A2D35" horizontal={true} vertical={false} />
                <XAxis
                  dataKey="range"
                  tick={{ fill: "#F0EDE6", fontSize: 11 }}
                />
                <YAxis tick={{ fill: "#F0EDE6", fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: "#11131A", border: "1px solid #14B8A6" }}
                  itemStyle={{ color: "#F0EDE6" }}
                />
                <Bar dataKey="count" fill="#14B8A6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>
    </div>
  );
}

export default AnalyticsPage;


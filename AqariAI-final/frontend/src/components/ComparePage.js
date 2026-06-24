import React from "react";

function ComparePage({ compareList, removeFromCompare }) {
  if (!compareList || compareList.length === 0) {
    return (
      <>
        <section className="hero">
          <div className="hero-title">Property Comparison</div>
          <div className="hero-sub">
            Compare up to 3 properties side by side.
          </div>
          <hr className="hero-divider" />
        </section>
        <div className="compare-empty">
          <div className="compare-empty-icon">⚖️</div>
          <div className="compare-empty-text">
            No properties selected yet.
          </div>
          <div className="compare-empty-sub">
            Go to Chat, search for properties, and click "+ Compare" 
            on up to 3 listings.
          </div>
        </div>
      </>
    );
  }

  const fields = [
    { label: "Price", key: "price" },
    { label: "Bedrooms", key: "bedroom" },
    { label: "Bathrooms", key: "bathroom" },
    { label: "Size", key: "area(sqft)" },
    { label: "City", key: "city" },
    { label: "Area", key: "address" },
    { label: "Type", key: "propert_type" },
    { label: "Furnishing", key: "furnishing" },
    { label: "Status", key: "completion_status" },
    { label: "Handover", key: "handover" },
    { label: "Project", key: "project_name" },
  ];

  const getPriceNum = (md) => {
    if (!md?.price) return null;
    const n = Number(String(md.price).replace(/[^0-9.]/g, ""));
    return Number.isFinite(n) ? n : null;
  };

  const getSqftNum = (md) => {
    if (!md?.["area(sqft)"]) return null;
    const n = Number(String(md["area(sqft)"]).replace(/[^0-9.]/g, ""));
    return Number.isFinite(n) ? n : null;
  };

  const getPriceSqft = (md) => {
    const price = getPriceNum(md);
    const sqft = getSqftNum(md);
    if (!price || !sqft) return null;
    return Math.round(price / sqft);
  };

  const prices = compareList.map((p) => getPriceNum(p.metadata));
  const minPrice = Math.min(...prices.filter(Boolean));

  return (
    <>
      <section className="hero">
        <div className="hero-title">Property Comparison</div>
        <div className="hero-sub">
          Comparing {compareList.length} propert
          {compareList.length === 1 ? "y" : "ies"} side by side.
        </div>
        <hr className="hero-divider" />
      </section>

      <div className="compare-wrapper">
        <div className="compare-grid"
          style={{ gridTemplateColumns: `180px repeat(${compareList.length}, 1fr)` }}>

          <div className="compare-header-cell" />
          {compareList.map((prop, i) => {
            const md = prop.metadata || {};
            const price = getPriceNum(md);
            const isCheapest = price === minPrice && prices.filter(p => p === minPrice).length === 1;
            return (
              <div key={i} className="compare-header-cell">
                <div className="compare-property-name">
                  {md.project_name || md.address || `Property ${i + 1}`}
                </div>
                <div className="compare-property-price">
                  {md.price || "—"}
                </div>
                {isCheapest && (
                  <div className="compare-badge-best">Best Price</div>
                )}
                <button
                  type="button"
                  className="compare-remove-btn"
                  onClick={() => removeFromCompare(prop.id)}
                >
                  Remove
                </button>
              </div>
            );
          })}

          {fields.map((field) => (
            <React.Fragment key={field.key}>
              <div className="compare-label-cell">{field.label}</div>
              {compareList.map((prop, i) => (
                <div key={i} className="compare-value-cell">
                  {prop.metadata?.[field.key] || "—"}
                </div>
              ))}
            </React.Fragment>
          ))}

          <div className="compare-label-cell">Price / sqft</div>
          {compareList.map((prop, i) => {
            const ppsf = getPriceSqft(prop.metadata);
            const allPpsf = compareList.map(p => getPriceSqft(p.metadata)).filter(Boolean);
            const minPpsf = Math.min(...allPpsf);
            const isBest = ppsf === minPpsf && allPpsf.filter(p => p === minPpsf).length === 1;
            return (
              <div
                key={i}
                className={`compare-value-cell ${isBest ? "compare-value-best" : ""}`}
              >
                {ppsf ? `AED ${ppsf.toLocaleString()}` : "—"}
              </div>
            );
          })}

        </div>
      </div>
    </>
  );
}

export default ComparePage;

import React, { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_BASE || "";

// Normalize a domain by stripping protocol, www, and paths
function normalizeDomain(domain) {
  if (!domain) return "";
  try {
    domain = domain.trim().toLowerCase();
    if (!/^https?:\/\//.test(domain)) {
      domain = "http://" + domain;
    }
    const url = new URL(domain);
    let host = url.hostname;
    if (host.startsWith("www.")) host = host.slice(4);
    return host;
  } catch {
    return domain;
  }
}

export function FilterPanel({ onApply, onClear }) {
  const [companyName, setCompanyName] = useState("");
  const [nameSuggestions, setNameSuggestions] = useState([]);
  const [domain, setDomain] = useState("");
  const [selectedRanges, setSelectedRanges] = useState([]);
  const [customMin, setCustomMin] = useState("");
  const [customMax, setCustomMax] = useState("");
  const [hq, setHq] = useState("");

  const ranges = [
    { label: "1-10", min: 1, max: 10 },
    { label: "11-50", min: 11, max: 50 },
    { label: "51-200", min: 51, max: 200 },
    { label: "201-500", min: 201, max: 500 },
    { label: "501-1000", min: 501, max: 1000 },
    { label: "1001-5000", min: 1001, max: 5000 },
    { label: "5001-10,000", min: 5001, max: 10000 },
    { label: "10,001+", min: 10001, max: null },
  ];

  // Fetch suggestions when companyName changes
  useEffect(() => {
    if (companyName.trim().length < 2) {
      setNameSuggestions([]);
      return;
    }
    const controller = new AbortController();
    fetch(`${API}/api/company_updated?search=${companyName}`, {
      signal: controller.signal,
    })
      .then((res) => res.json())
      .then((data) => {
        const names = (data.companies || []).map((c) => c.name).filter(Boolean);
        setNameSuggestions(Array.from(new Set(names)));
      })
      .catch(() => {});
    return () => controller.abort();
  }, [companyName]);

  const handleRangeChange = (label) => {
    setSelectedRanges((prev) =>
      prev.includes(label) ? prev.filter((r) => r !== label) : [...prev, label],
    );
    setCustomMin("");
    setCustomMax("");
  };

  const handleCustomMinChange = (e) => {
    setSelectedRanges([]);
    setCustomMin(e.target.value);
  };

  const handleCustomMaxChange = (e) => {
    setSelectedRanges([]);
    setCustomMax(e.target.value);
  };

  const applyFilters = () => {
    const payload = {
      companyName,
      domain: normalizeDomain(domain),
      sizeRanges: selectedRanges,
      sizeMin: customMin,
      sizeMax: customMax,
      hq,
    };
    onApply && onApply(payload);
  };

  const clearFilters = () => {
    setCompanyName("");
    setDomain("");
    setSelectedRanges([]);
    setCustomMin("");
    setCustomMax("");
    setHq("");
    onClear && onClear();
  };

  return (
    <div className="bg-gray-100 border p-4 rounded w-full md:w-64 mb-4 md:mb-0 md:mr-4">
      <h2 className="text-lg font-semibold mb-4">Filters</h2>

      {/* Company Name */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">Company Name</label>
        <input
          type="text"
          list="company-suggestions"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          className="w-full p-2 border rounded"
          placeholder="Type a company name"
        />
        <datalist id="company-suggestions">
          {nameSuggestions.map((name) => (
            <option key={name} value={name} />
          ))}
        </datalist>
      </div>

      {/* Domain */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">Company Domain</label>
        <input
          type="text"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          className="w-full p-2 border rounded"
          placeholder="https://example.com"
        />
      </div>

      {/* Employee Size */}
      <div className="mb-4">
        <p className="text-sm font-medium mb-1">Number of Employees</p>
        {ranges.map((r) => (
          <label key={r.label} className="flex items-center space-x-2 mb-1">
            <input
              type="checkbox"
              checked={selectedRanges.includes(r.label)}
              onChange={() => handleRangeChange(r.label)}
            />
            <span>{r.label}</span>
          </label>
        ))}
        <div className="flex items-center space-x-2 mt-2">
          <input
            type="number"
            value={customMin}
            onChange={handleCustomMinChange}
            placeholder="Min"
            className="w-20 p-1 border rounded"
          />
          <span>-</span>
          <input
            type="number"
            value={customMax}
            onChange={handleCustomMaxChange}
            placeholder="Max"
            className="w-20 p-1 border rounded"
          />
        </div>
      </div>

      {/* Headquarters */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">
          Headquarters Location
        </label>
        <input
          type="text"
          value={hq}
          onChange={(e) => setHq(e.target.value)}
          className="w-full p-2 border rounded"
          placeholder="City or Country"
        />
      </div>

      {/* Buttons */}
      <div className="flex space-x-2">
        <button
          onClick={applyFilters}
          className="flex-1 bg-blue-500 text-white py-2 rounded hover:bg-blue-600"
        >
          Apply Filters
        </button>
        <button
          onClick={clearFilters}
          className="flex-1 border border-gray-400 text-gray-700 py-2 rounded hover:bg-gray-50"
        >
          Clear Filters
        </button>
      </div>
    </div>
  );
}

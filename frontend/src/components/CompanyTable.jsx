import React, { useEffect, useState } from "react";
import { CompanyDetailsPanel } from "./CompanyDetailsPanel";

const API = import.meta.env.VITE_API_BASE || "";

export function CompanyTable() {
  const [companies, setCompanies] = useState([]);
  const [search, setSearch] = useState("");
  const [sortConfig, setSortConfig] = useState({
    key: "name",
    direction: "asc",
  });
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    fetch(`${API}/api/company_updated`)
      .then((res) => res.json())
      .then((data) => setCompanies(data.companies || []));
  }, []);

  const formatLinkedInUrl = (url) =>
    /^https?:\/\//i.test(url) ? url : `https://${url}`;

  const handleSort = (key) => {
    let direction = "asc";
    if (sortConfig.key === key && sortConfig.direction === "asc") {
      direction = "desc";
    }
    setSortConfig({ key, direction });
  };

  const sorted = [...companies].sort((a, b) => {
    const valA = a[sortConfig.key] || "";
    const valB = b[sortConfig.key] || "";
    if (valA < valB) return sortConfig.direction === "asc" ? -1 : 1;
    if (valA > valB) return sortConfig.direction === "asc" ? 1 : -1;
    return 0;
  });

  const filtered = sorted.filter((c) => {
    const term = search.toLowerCase();
    return (
      (c.name || "").toLowerCase().includes(term) ||
      (c.domain || "").toLowerCase().includes(term) ||
      (c.industry || "").toLowerCase().includes(term) ||
      (c.hq || "").toLowerCase().includes(term)
    );
  });

  return (
    <div className="relative text-green-400 font-mono">
      <input
        type="text"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search..."
        className="mb-4 w-full bg-gray-900 border border-green-500 rounded px-3 py-2 placeholder-green-700 focus:outline-none"
      />
      <div className="overflow-x-auto">
        <table className="min-w-full border border-green-500">
          <thead className="bg-gray-900">
            <tr>
              <th
                className="px-4 py-2 border border-green-500 cursor-pointer"
                onClick={() => handleSort("name")}
              >
                Company Name
              </th>
              <th
                className="px-4 py-2 border border-green-500 cursor-pointer"
                onClick={() => handleSort("domain")}
              >
                Domain
              </th>
              <th
                className="px-4 py-2 border border-green-500 cursor-pointer"
                onClick={() => handleSort("hq")}
              >
                Headquarters
              </th>
              <th
                className="px-4 py-2 border border-green-500 cursor-pointer"
                onClick={() => handleSort("industry")}
              >
                Industry
              </th>
              <th className="px-4 py-2 border border-green-500">LinkedIn</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((c) => (
              <tr
                key={c.id}
                className="hover:bg-gray-800 transition-colors cursor-pointer"
                onClick={() => setSelected(c)}
              >
                <td className="px-4 py-2 border border-green-500">
                  {c.name || "N/A"}
                </td>
                <td className="px-4 py-2 border border-green-500">
                  {c.domain}
                </td>
                <td className="px-4 py-2 border border-green-500">
                  {c.hq || "N/A"}
                </td>
                <td className="px-4 py-2 border border-green-500">
                  {c.industry || "N/A"}
                </td>
                <td className="px-4 py-2 border border-green-500 text-center">
                  {c.linkedin_url ? (
                    <a
                      href={formatLinkedInUrl(c.linkedin_url)}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="text-blue-400 hover:underline"
                    >
                      Link
                    </a>
                  ) : (
                    "N/A"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <CompanyDetailsPanel
        company={selected}
        onClose={() => setSelected(null)}
      />
    </div>
  );
}

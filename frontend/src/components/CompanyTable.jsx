import React, { useEffect, useState } from "react";
import { CompanyDetailsPanel } from "./CompanyDetailsPanel";

const API = import.meta.env.VITE_API_BASE || "";

export function CompanyTable({ filters = {} }) {
  const [companies, setCompanies] = useState([]);
  const [sortConfig, setSortConfig] = useState({
    key: "name",
    direction: "asc",
  });
  const [selected, setSelected] = useState(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    const params = new URLSearchParams({
      page,
      page_size: pageSize,
      sort_key: sortConfig.key,
      sort_dir: sortConfig.direction,
    });
    if (filters.companyName) params.append("company_name", filters.companyName);
    if (filters.domain) params.append("domain", filters.domain);
    if (filters.hq) params.append("hq", filters.hq);
    if (filters.sizeMin) params.append("size_min", filters.sizeMin);
    if (filters.sizeMax) params.append("size_max", filters.sizeMax);
    if (filters.sizeRanges && filters.sizeRanges.length) {
      filters.sizeRanges.forEach((r) => params.append("size_range", r));
    }
    fetch(`${API}/api/company_updated?${params.toString()}`)
      .then((res) => res.json())
      .then((data) => {
        setCompanies(data.companies || []);
        setTotal(data.total || 0);
      });
  }, [page, pageSize, sortConfig.key, sortConfig.direction, filters]);

  useEffect(() => {
    setPage(1);
  }, [filters]);

  const formatLinkedInUrl = (url) =>
    /^https?:\/\//i.test(url) ? url : `https://${url}`;

  const handleSort = (key) => {
    let direction = "asc";
    if (sortConfig.key === key && sortConfig.direction === "asc") {
      direction = "desc";
    }
    setSortConfig({ key, direction });
    setPage(1);
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  const getPageNumbers = () => {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }
    const pages = [1];
    if (page > 4) pages.push("...");
    const start = page <= 4 ? 2 : page - 1;
    const end = page >= totalPages - 3 ? totalPages - 1 : page + 1;
    for (let i = start; i <= end; i++) pages.push(i);
    if (page < totalPages - 3) pages.push("...");
    pages.push(totalPages);
    return pages;
  };

  const startItem = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, total);

  return (
    <div className="relative text-green-400 font-mono">
      <div className="flex justify-end items-center mb-4">
        <div className="flex items-center space-x-2">
          <label htmlFor="pageSize">Records per page:</label>
          <select
            id="pageSize"
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
            className="bg-gray-900 border border-green-500 rounded px-2 py-1"
          >
            {[10, 20, 50, 100].map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </div>
      </div>

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
                onClick={() => handleSort("size")}
              >
                Employees
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
            {companies.map((c) => (
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
                  {c.size || "N/A"}
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

      <div className="flex justify-between items-center mt-4">
        <span className="text-sm">
          Showing {startItem}-{endItem} of {total} results
        </span>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setPage((p) => p - 1)}
            disabled={page === 1}
            className="px-2 py-1 border border-green-500 rounded disabled:opacity-50"
          >
            Previous
          </button>
          {getPageNumbers().map((p, idx) =>
            p === "..." ? (
              <span key={idx} className="px-2">
                ...
              </span>
            ) : (
              <button
                key={p}
                onClick={() => setPage(p)}
                className={`px-2 py-1 border border-green-500 rounded ${
                  p === page ? "bg-green-500 text-black" : ""
                }`}
              >
                {p}
              </button>
            ),
          )}
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={page === totalPages}
            className="px-2 py-1 border border-green-500 rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>

      <CompanyDetailsPanel
        company={selected}
        onClose={() => setSelected(null)}
      />
    </div>
  );
}

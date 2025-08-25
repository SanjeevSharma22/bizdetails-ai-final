import React, { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_BASE || "";

export function CompanyTable({ filters = {} }) {
  const [companies, setCompanies] = useState([]);
  const [sortConfig, setSortConfig] = useState({
    key: "name",
    direction: "asc",
  });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [selectedRows, setSelectedRows] = useState([]);
  const [bulkOption, setBulkOption] = useState("page");
  const [customCount, setCustomCount] = useState(100);

  const buildParams = (pageParam, sizeParam) => {
    const params = new URLSearchParams({
      page: pageParam,
      page_size: sizeParam,
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
    return params;
  };

  const fetchBulk = async (limit) => {
    const results = [];
    let pageNum = 1;
    const maxSize = 100;
    while (results.length < limit) {
      const params = buildParams(pageNum, Math.min(maxSize, limit - results.length));
      const res = await fetch(`${API}/api/company_updated?${params.toString()}`);
      const data = await res.json();
      results.push(...(data.companies || []));
      if (results.length >= data.total || (data.companies || []).length === 0) break;
      pageNum += 1;
    }
    return results.slice(0, limit);
  };

  useEffect(() => {
    const params = buildParams(page, pageSize);
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

  const handleRowSelect = (company, checked) => {
    setSelectedRows((prev) => {
      if (checked) {
        if (prev.some((r) => r.id === company.id)) return prev;
        return [...prev, company];
      }
      return prev.filter((r) => r.id !== company.id);
    });
  };

  const allSelectedThisPage = companies.every((c) =>
    selectedRows.some((r) => r.id === c.id)
  );

  const toggleSelectAll = (checked) => {
    if (checked) {
      const newRows = companies.filter(
        (c) => !selectedRows.some((r) => r.id === c.id)
      );
      setSelectedRows((prev) => [...prev, ...newRows]);
    } else {
      setSelectedRows((prev) =>
        prev.filter((r) => !companies.some((c) => c.id === r.id))
      );
    }
  };

  const handleDownload = async () => {
    let records = [];
    if (bulkOption === "page") {
      records = selectedRows.length ? selectedRows : companies;
    } else if (bulkOption === "1000") {
      records = await fetchBulk(Math.min(1000, total));
    } else if (bulkOption === "all") {
      records = await fetchBulk(total);
    } else if (bulkOption === "custom") {
      records = await fetchBulk(Math.min(customCount, total));
    }
    if (!records.length) return;
    const headers = [
      "Company Name",
      "Website",
      "Headquarters",
      "Industry",
      "Employee Size",
      "Company LinkedIn",
    ];
    const rows = records.map((r) => [
      r.name || "N/A",
      r.domain || "N/A",
      r.hq || "N/A",
      r.industry || "N/A",
      r.size || "N/A",
      r.linkedin_url || "N/A",
    ]);
    const csv = [headers.join(","), ...rows.map((row) => row.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "companies.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="relative">
      <div className="flex items-center mb-2 space-x-2">
        <select
          value={bulkOption}
          onChange={(e) => setBulkOption(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="page">This page</option>
          <option value="1000">1000 records</option>
          <option value="all">All results</option>
          <option value="custom">Custom number</option>
        </select>
        {bulkOption === "custom" && (
          <input
            type="number"
            min="1"
            value={customCount}
            onChange={(e) => setCustomCount(Number(e.target.value))}
            className="border rounded px-2 py-1 w-24"
          />
        )}
        <button
          onClick={handleDownload}
          className="px-3 py-1 border rounded bg-purple-600 text-white"
        >
          Download
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full border border-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 border border-gray-200">
                <input
                  type="checkbox"
                  checked={companies.length > 0 && allSelectedThisPage}
                  onChange={(e) => toggleSelectAll(e.target.checked)}
                />
              </th>
              <th
                className="px-4 py-2 border border-gray-200 cursor-pointer"
                onClick={() => handleSort("name")}
              >
                Company Name
              </th>
              <th
                className="px-4 py-2 border border-gray-200 cursor-pointer"
                onClick={() => handleSort("domain")}
              >
                Domain
              </th>
              <th
                className="px-4 py-2 border border-gray-200 cursor-pointer"
                onClick={() => handleSort("hq")}
              >
                Headquarters
              </th>
              <th
                className="px-4 py-2 border border-gray-200 cursor-pointer"
                onClick={() => handleSort("size")}
              >
                Employees
              </th>
              <th
                className="px-4 py-2 border border-gray-200 cursor-pointer"
                onClick={() => handleSort("industry")}
              >
                Industry
              </th>
              <th className="px-4 py-2 border border-gray-200">LinkedIn</th>
            </tr>
          </thead>
          <tbody>
            {companies.map((c) => (
              <tr
                key={c.id}
                className="hover:bg-gray-100 transition-colors"
              >
                <td className="px-4 py-2 border border-gray-200">
                  <input
                    type="checkbox"
                    checked={selectedRows.some((r) => r.id === c.id)}
                    onChange={(e) => {
                      e.stopPropagation();
                      handleRowSelect(c, e.target.checked);
                    }}
                  />
                </td>
                <td className="px-4 py-2 border border-gray-200">
                  {c.name || "N/A"}
                </td>
                <td className="px-4 py-2 border border-gray-200">
                  {c.domain}
                </td>
                <td className="px-4 py-2 border border-gray-200">
                  {c.hq || "N/A"}
                </td>
                <td className="px-4 py-2 border border-gray-200">
                  {c.size || "N/A"}
                </td>
                <td className="px-4 py-2 border border-gray-200">
                  {c.industry || "N/A"}
                </td>
                <td className="px-4 py-2 border border-gray-200 text-center">
                  {c.linkedin_url ? (
                    <a
                      href={formatLinkedInUrl(c.linkedin_url)}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="text-primary hover:underline"
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
        <div className="flex items-center space-x-2">
          <label htmlFor="pageSize">Records per page:</label>
          <select
            id="pageSize"
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
            className="border rounded px-2 py-1"
          >
            {[10, 20, 50, 100].map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setPage((p) => p - 1)}
            disabled={page === 1}
            className="px-2 py-1 border rounded disabled:opacity-50"
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
                className={`px-2 py-1 border rounded ${
                  p === page ? "bg-purple-600 text-white" : ""
                }`}
              >
                {p}
              </button>
            ),
          )}
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={page === totalPages}
            className="px-2 py-1 border rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>

    </div>
  );
}

import React, { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_BASE || "";

export function JobDetails({ jobId, onClose }) {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetch(`${API}/api/jobs/${jobId}`)
      .then((r) => r.json())
      .then(setData);
  }, [jobId]);

  if (!data) return null;
  const { meta, results } = data;
  const total = meta.internal_fields + meta.ai_fields;
  const internalPct = total ? (meta.internal_fields / total) * 100 : 0;
  const aiPct = total ? (meta.ai_fields / total) * 100 : 0;

  return (
    <div className="mt-4 card p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg">Job Details</h2>
        <button onClick={onClose} className="text-sm underline">
          Close
        </button>
      </div>
      <div className="grid sm:grid-cols-4 gap-4 mb-4 text-center">
        <div className="bg-gray-100 p-2 rounded">Total {meta.total_records}</div>
        <div className="bg-gray-100 p-2 rounded">Enriched {meta.processed_records}</div>
        <div className="bg-gray-100 p-2 rounded">Internal {meta.internal_fields}</div>
        <div className="bg-gray-100 p-2 rounded">AI {meta.ai_fields}</div>
      </div>
      <div className="mb-4">
        <div className="w-full bg-gray-200 h-4 flex">
          <div
            className="bg-purple-600"
            style={{ width: `${internalPct}%` }}
          />
          <div className="bg-blue-500" style={{ width: `${aiPct}%` }} />
        </div>
        <div className="flex justify-between text-xs">
          <span>{internalPct.toFixed(0)}% Internal</span>
          <span>{aiPct.toFixed(0)}% AI</span>
        </div>
      </div>
      <div className="overflow-auto max-h-64">
        <table className="w-full text-xs">
          <thead>
            <tr>
              <th className="p-1">Company</th>
              <th className="p-1">Domain</th>
              <th className="p-1">Industry</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => (
              <tr key={r.id} className="border-t border-gray-200">
                <td className="p-1">{r.companyName}</td>
                <td className="p-1">
                  {r.domain}
                  {r.sources.domain && (
                    <span className="ml-1 px-1 text-[10px] rounded bg-gray-200">
                      {r.sources.domain === "internal" ? "INT" : "AI"}
                    </span>
                  )}
                </td>
                <td className="p-1">
                  {r.industry}
                  {r.sources.industry && (
                    <span className="ml-1 px-1 text-[10px] rounded bg-gray-200">
                      {r.sources.industry === "internal" ? "INT" : "AI"}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

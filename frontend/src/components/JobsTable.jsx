import React from "react";

export function JobsTable({ jobs, onSelect }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left">
          <th className="p-2">Status</th>
          <th className="p-2">Progress</th>
          <th className="p-2">Created</th>
          <th className="p-2">Attribution</th>
          <th className="p-2">Downloads</th>
        </tr>
      </thead>
      <tbody>
        {jobs.map((j) => (
          <tr
            key={j.job_id}
            className="border-t border-gray-800 hover:bg-gray-800 cursor-pointer"
            onClick={() => onSelect && onSelect(j.job_id)}
          >
            <td className="p-2">{j.status}</td>
            <td className="p-2">{j.progress.toFixed(0)}%</td>
            <td className="p-2">
              {new Date(j.created_at).toLocaleString()}
            </td>
            <td className="p-2">
              <div className="w-32 bg-gray-700 h-2 mb-1 flex">
                <div
                  className="bg-green-500 h-2"
                  style={{ width: `${j.internal_pct}%` }}
                />
                <div
                  className="bg-blue-500 h-2"
                  style={{ width: `${j.ai_pct}%` }}
                />
              </div>
              <div className="text-xs flex justify-between">
                <span>{j.internal_pct.toFixed(0)}% INT</span>
                <span>{j.ai_pct.toFixed(0)}% AI</span>
              </div>
            </td>
            <td className="p-2 space-x-2">
              <button
                disabled={j.status !== "completed"}
                className="px-2 py-1 border border-green-500 rounded disabled:opacity-50"
              >
                Full CSV
              </button>
              <button
                disabled={j.status !== "completed"}
                className="px-2 py-1 border border-green-500 rounded disabled:opacity-50"
              >
                Failed
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

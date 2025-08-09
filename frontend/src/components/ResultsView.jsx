import React from "react";

const API = import.meta.env.VITE_API_BASE || "";

export function ResultsView({ results }) {
  if (!results) {
    return <p>No results available.</p>;
  }

  const downloadCSV = () => {
    const headers = [
      "Company Name",
      "Website",
      "Headquarters",
      "Industry",
      "Employee Size",
      "Company LinkedIn",
    ];
    const rows = results.map((r) => [
      r.companyName,
      r.domain,
      r.hq || "N/A",
      r.industry || "N/A",
      r.size || "N/A",
      r.linkedin_url || "N/A",
    ]);
    const csv = [headers.join(","), ...rows.map((row) => row.join(","))].join(
      "\n",
    );
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "enriched.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const saveResults = async () => {
    await fetch(`${API}/api/save_results`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ results }),
    });
  };

  return (
    <div className="text-green-400 font-mono">
      <div className="flex gap-4 mb-4">
        <button
          onClick={downloadCSV}
          className="px-4 py-2 bg-gray-900 border border-green-500 rounded hover:bg-gray-800"
        >
          Download Enriched CSV
        </button>
        <button
          onClick={saveResults}
          className="px-4 py-2 bg-gray-900 border border-green-500 rounded hover:bg-gray-800"
        >
          Save to My List
        </button>
      </div>
      <table className="min-w-full text-left border border-green-500">
        <thead className="bg-gray-900">
          <tr>
            <th className="border border-green-500 px-2">Company Name</th>
            <th className="border border-green-500 px-2">Website</th>
            <th className="border border-green-500 px-2">Headquarters</th>
            <th className="border border-green-500 px-2">Industry</th>
            <th className="border border-green-500 px-2">Employee Size</th>
            <th className="border border-green-500 px-2">Company LinkedIn</th>
          </tr>
        </thead>
        <tbody>
          {results.map((r) => (
            <tr key={r.id} className="hover:bg-gray-800">
              <td className="border border-green-500 px-2">{r.companyName}</td>
              <td className="border border-green-500 px-2">{r.domain}</td>
              <td className="border border-green-500 px-2">{r.hq || "N/A"}</td>
              <td className="border border-green-500 px-2">
                {r.industry || "N/A"}
              </td>
              <td className="border border-green-500 px-2">
                {r.size || "N/A"}
              </td>
              <td className="border border-green-500 px-2">
                {r.linkedin_url ? (
                  <a
                    href={r.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
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
  );
}

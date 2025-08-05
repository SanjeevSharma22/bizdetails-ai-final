import React from 'react';

export function ResultsView({ results }) {
  if (!results) {
    return <p>No results available.</p>;
  }
  return (
    <table className="min-w-full text-left border">
      <thead>
        <tr>
          <th className="border px-2">Company</th>
          <th className="border px-2">Domain</th>
          <th className="border px-2">Confidence</th>
          <th className="border px-2">Match Type</th>
        </tr>
      </thead>
      <tbody>
        {results.map((r) => (
          <tr key={r.id}>
            <td className="border px-2">{r.companyName}</td>
            <td className="border px-2">{r.domain}</td>
            <td className="border px-2">{r.confidence}</td>
            <td className="border px-2">{r.matchType}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

import React from 'react';

export function ResultsView({ results }) {
  if (!results) {
    return <p>No results available.</p>;
  }

  return (
    <table className="min-w-full text-left border">
      <thead>
        <tr>
          <th className="border px-2">Company Name</th>
          <th className="border px-2">Website</th>
          <th className="border px-2">Headquarters</th>
          <th className="border px-2">Industry</th>
          <th className="border px-2">Employee Size</th>
          <th className="border px-2">Company LinkedIn</th>
        </tr>
      </thead>
      <tbody>
        {results.map((r) => (
          <tr key={r.id}>
            <td className="border px-2">{r.companyName}</td>
            <td className="border px-2">{r.domain}</td>
            <td className="border px-2">{r.hq}</td>
            <td className="border px-2">{r.industry}</td>
            <td className="border px-2">{r.size}</td>
            <td className="border px-2">{r.linkedin_url}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

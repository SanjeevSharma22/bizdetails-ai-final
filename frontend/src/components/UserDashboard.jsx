import React, { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_BASE || "";

export function UserDashboard({ token }) {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    if (!token) return;
    fetch(`${API}/api/dashboard`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((d) => setStats(d.stats || {}));
  }, [token]);

  if (!stats) {
    return (
      <div className="bg-black p-4 rounded border border-green-500 text-green-400">
        Loading...
      </div>
    );
  }

  return (
    <div className="bg-black p-4 rounded border border-green-500 text-green-400 space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-lg font-bold">{stats.enrichment_count || 0}</div>
          <div className="text-xs text-green-300">Enrichment Jobs</div>
        </div>
        <div>
          <div className="text-lg font-bold">
            {stats.last_login ? new Date(stats.last_login).toLocaleString() : "—"}
          </div>
          <div className="text-xs text-green-300">Last Login</div>
        </div>
        <div>
          <div className="text-lg font-bold">
            {stats.last_enrichment_at
              ? new Date(stats.last_enrichment_at).toLocaleString()
              : "—"}
          </div>
          <div className="text-xs text-green-300">Last Enrichment</div>
        </div>
      </div>
      {stats.activity_log && stats.activity_log.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold mb-2">Recent Activity</h3>
          <ul className="text-xs space-y-1">
            {stats.activity_log
              .slice()
              .reverse()
              .slice(0, 5)
              .map((a, i) => (
                <li key={i}>
                  {new Date(a.timestamp).toLocaleString()} – {a.action}
                </li>
              ))}
          </ul>
        </div>
      )}
    </div>
  );
}

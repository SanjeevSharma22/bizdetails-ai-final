import React, { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_BASE || "";

export function UserDashboard({ token }) {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    fetch(`${API}/api/dashboard`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((d) => setStats(d.stats || {}));
  }, [token]);

  if (!stats) {
    return <div className="card p-4">Loading...</div>;
  }

  const lastJob = stats.last_job || null;
  const progress = lastJob && lastJob.total_records
    ? Math.round((lastJob.processed_records / lastJob.total_records) * 100)
    : 0;

  const downloadLastFile = async () => {
    setError("");
    try {
      const res = await fetch(`${API}/api/dashboard/last-file`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        throw new Error("Download failed");
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = lastJob?.file_name || "enriched.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-4 flex flex-col items-center text-center space-y-1">
          <div className="text-2xl font-bold">{stats.enrichment_count || 0}</div>
          <div className="text-xs text-primary">Enrichment Jobs</div>
        </div>
        <div className="card p-4 flex flex-col items-center text-center space-y-1">
          <div className="text-2xl font-bold">
            {stats.last_login ? new Date(stats.last_login).toLocaleString() : "—"}
          </div>
          <div className="text-xs text-primary">Last Login</div>
        </div>
        <div className="card p-4 flex flex-col items-center text-center space-y-1">
          <div className="text-2xl font-bold">
            {stats.last_enrichment_at
              ? new Date(stats.last_enrichment_at).toLocaleString()
              : "—"}
          </div>
          <div className="text-xs text-primary">Last Enrichment</div>
        </div>
        <div className="card p-4 text-sm space-y-2">
          <div className="text-center text-lg font-bold">Enrichment Results</div>
          <div>
            File Name: <span className="font-medium">{lastJob?.file_name || "—"}</span>
          </div>
          <div>Accounts Pushed: {lastJob?.total_records || 0}</div>
          <div>Accounts Enriched: {lastJob?.processed_records || 0}</div>
          <div>
            Timestamp: {lastJob?.timestamp ? new Date(lastJob.timestamp).toLocaleString() : "—"}
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <div className="text-right text-xs">{progress}%</div>
          {lastJob && (
            <button onClick={downloadLastFile} className="btn btn-primary w-full">
              Download Last Enriched File
            </button>
          )}
          {error && <div className="text-xs text-red-500 text-center">{error}</div>}
        </div>
      </div>

      <div className="card p-4">
        <h3 className="text-sm font-semibold mb-2">Recent Activity</h3>
        {stats.activity_log && stats.activity_log.length > 0 ? (
          <div className="max-h-48 overflow-y-auto">
            <ul className="relative border-l border-gray-200 pl-4 space-y-4 text-xs">
              {stats.activity_log
                .slice()
                .reverse()
                .map((a, i) => (
                  <li key={i} className="relative">
                    <span className="absolute -left-1.5 top-1 w-3 h-3 bg-primary rounded-full"></span>
                    <time className="block text-gray-500">
                      {new Date(a.timestamp).toLocaleString()}
                    </time>
                    <p>{a.action}</p>
                  </li>
                ))}
            </ul>
          </div>
        ) : (
          <div className="text-xs text-gray-500">No recent activity.</div>
        )}
      </div>
    </div>
  );
}


import React, { useState } from "react";
import { Building2, CheckCircle, Gauge, Timer, X } from "lucide-react";
import { Badge } from "./ui/badge";

export function ProcessingDashboard() {
  const [showBanner, setShowBanner] = useState(true);

  const recentRuns = [
    {
      file: "q4-prospects.csv",
      time: "2025-01-28 14:30",
      companies: 150,
      matched: 128,
      percent: 85,
      dist: { high: 60, medium: 30, low: 10 },
    },
    {
      file: "tech-companies.csv",
      time: "2025-01-28 11:15",
      companies: 75,
      matched: 68,
      percent: 91,
      dist: { high: 70, medium: 20, low: 10 },
    },
    {
      file: "startup-list.csv",
      time: "2025-01-25 16:45",
      companies: 200,
      matched: 165,
      percent: 83,
      dist: { high: 50, medium: 30, low: 20 },
    },
  ];

  return (
    <div className="space-y-6">
      {showBanner && (
        <div className="bg-yellow-100 text-yellow-900 px-4 py-2 rounded flex items-start justify-between gap-4">
          <span className="text-sm">
            Data Processing Notice: This tool processes company data to map domains. We comply with GDPR/CCPA requirements and do not store personally identifiable information. By using this service, you consent to data processing for company data enrichment purposes only.
          </span>
          <button onClick={() => setShowBanner(false)} className="text-yellow-900" aria-label="Close banner">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gray-900 p-4 rounded border border-green-500 flex items-center justify-between">
          <div>
            <p className="text-2xl font-bold text-green-400">1,234</p>
            <p className="text-sm text-green-400 mt-1">Companies Processed</p>
          </div>
          <Building2 className="w-8 h-8 text-green-500" />
        </div>

        <div className="bg-gray-900 p-4 rounded border border-green-500 flex items-center justify-between">
          <div>
            <p className="text-2xl font-bold text-green-400">92%</p>
            <p className="text-sm text-green-400 mt-1">Success Rate</p>
            <div className="w-full bg-gray-700 h-1 mt-2">
              <div className="h-full bg-green-500" style={{ width: "92%" }} />
            </div>
          </div>
          <CheckCircle className="w-8 h-8 text-green-500" />
        </div>

        <div className="bg-gray-900 p-4 rounded border border-green-500 flex items-center justify-between">
          <div>
            <p className="text-2xl font-bold text-green-400">87%</p>
            <p className="text-sm text-green-400 mt-1">Avg Confidence</p>
            <div className="w-full bg-gray-700 h-1 mt-2">
              <div className="h-full bg-purple-500" style={{ width: "87%" }} />
            </div>
          </div>
          <Gauge className="w-8 h-8 text-purple-500" />
        </div>

        <div className="bg-gray-900 p-4 rounded border border-green-500 flex items-center justify-between">
          <div>
            <p className="text-2xl font-bold text-green-400">1.2s</p>
            <p className="text-sm text-green-400 mt-1">Avg Processing</p>
          </div>
          <Timer className="w-8 h-8 text-orange-500" />
        </div>
      </div>

      <div className="space-y-2">
        <h2 className="text-lg font-semibold text-green-400">Recent Processing History</h2>
        <p className="text-sm text-green-400">Your latest domain mapping runs and their results.</p>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm text-left">
            <thead className="text-green-400">
              <tr>
                <th className="px-4 py-2">File Name</th>
                <th className="px-4 py-2">Timestamp</th>
                <th className="px-4 py-2 text-right">Companies</th>
                <th className="px-4 py-2 text-right">Matched</th>
                <th className="px-4 py-2">Confidence Distribution</th>
                <th className="px-4 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {recentRuns.map((run, idx) => (
                <tr key={idx} className="border-t border-gray-700">
                  <td className="px-4 py-2">{run.file}</td>
                  <td className="px-4 py-2">{run.time}</td>
                  <td className="px-4 py-2 text-right">{run.companies}</td>
                  <td className="px-4 py-2 text-right">
                    {run.matched} ({run.percent}%)
                  </td>
                  <td className="px-4 py-2">
                    <div className="w-32 h-2 bg-gray-700 flex">
                      <div className="h-full bg-green-500" style={{ width: `${run.dist.high}%` }} />
                      <div className="h-full bg-yellow-500" style={{ width: `${run.dist.medium}%` }} />
                      <div className="h-full bg-red-500" style={{ width: `${run.dist.low}%` }} />
                    </div>
                  </td>
                  <td className="px-4 py-2">
                    <Badge className="bg-green-900 text-green-400">Completed</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex items-center gap-4 text-xs text-green-400">
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 bg-green-500" />
            High
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 bg-yellow-500" />
            Medium
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 bg-red-500" />
            Low
          </div>
        </div>
      </div>
    </div>
  );
}


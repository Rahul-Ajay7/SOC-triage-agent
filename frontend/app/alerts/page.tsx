"use client";

import { useEffect, useState } from "react";
import { api, type Alert } from "@/lib/api";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.alerts().then(setAlerts).catch((e) => setError((e as Error).message));
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-sm font-semibold text-muted">Raw alert queue</h2>
      {error && (
        <div className="rounded-lg border border-critical/40 bg-critical/10 p-3 text-sm text-critical">
          {error}
        </div>
      )}
      <div className="overflow-hidden rounded-lg border border-edge bg-panel">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-muted">
              <th className="p-3">#</th>
              <th className="p-3">Source</th>
              <th className="p-3">Title</th>
              <th className="p-3">Status</th>
              <th className="p-3">Created</th>
            </tr>
          </thead>
          <tbody>
            {alerts.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-10 text-center text-muted">
                  No alerts. Load demo alerts from the dashboard.
                </td>
              </tr>
            ) : (
              alerts.map((a) => (
                <tr key={a.id} className="border-t border-edge hover:bg-panel2">
                  <td className="p-3">{a.id}</td>
                  <td className="p-3 text-muted">{a.source}</td>
                  <td className="p-3">{a.title}</td>
                  <td className="p-3 text-muted">{a.status}</td>
                  <td className="p-3 text-muted">
                    {a.created_at ? new Date(a.created_at).toLocaleString() : "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

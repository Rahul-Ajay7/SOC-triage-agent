"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type Incident } from "@/lib/api";
import AlertQueue from "@/components/AlertQueue";

export default function Dashboard() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [llm, setLlm] = useState<string>("…");
  const [seeding, setSeeding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setIncidents(await api.incidents());
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    load();
    api
      .health()
      .then((h) => setLlm(h.llm_configured ? "connected" : "heuristic mode"))
      .catch(() => setLlm("offline"));
  }, [load]);

  async function seed() {
    setSeeding(true);
    try {
      await api.seed();
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSeeding(false);
    }
  }

  const counts = {
    critical: incidents.filter((i) => i.verdict === "critical").length,
    suspicious: incidents.filter((i) => i.verdict === "suspicious").length,
    benign: incidents.filter((i) => i.verdict === "benign").length,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex gap-3 text-sm">
          <Stat label="Critical" value={counts.critical} color="text-critical" />
          <Stat label="Suspicious" value={counts.suspicious} color="text-suspicious" />
          <Stat label="Benign" value={counts.benign} color="text-benign" />
        </div>
        <div className="flex items-center gap-3">
          <span className="rounded-full border border-edge px-3 py-1 text-xs text-muted">
            LLM: {llm}
          </span>
          <button
            onClick={seed}
            disabled={seeding}
            className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {seeding ? "Running agent…" : "Load demo alerts"}
          </button>
          <button
            onClick={load}
            className="rounded-lg border border-edge px-4 py-2 text-sm hover:border-accent"
          >
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-critical/40 bg-critical/10 p-3 text-sm text-critical">
          Backend unreachable: {error}. Is the API running on{" "}
          {process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001"}?
        </div>
      )}

      <h2 className="text-sm font-semibold text-muted">Incident queue</h2>
      <AlertQueue incidents={incidents} />
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="rounded-lg border border-edge bg-panel px-4 py-2">
      <span className={`text-lg font-bold ${color}`}>{value}</span>{" "}
      <span className="text-muted">{label}</span>
    </div>
  );
}

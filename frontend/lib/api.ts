// Thin fetch wrapper around the SOC backend.
const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";

export type Verdict = "benign" | "suspicious" | "critical";

export interface Mitre {
  id: string;
  name: string;
  tactic: string;
  url: string;
  reason: string;
}

export interface TraceStep {
  step: string;
  label: string;
  detail: string;
  data: Record<string, unknown>;
  iteration: number;
  timestamp: string;
}

export interface Incident {
  id: number;
  alert_id: number;
  verdict: Verdict;
  confidence: number;
  summary: string;
  iocs: { ips?: string[]; users?: string[]; hashes?: string[]; domains?: string[] };
  mitre: Mitre[];
  action: "pending" | "approved" | "rejected";
  action_note: string | null;
  llm_source: string;
  created_at: string | null;
  trace?: TraceStep[];
}

export interface Alert {
  id: number;
  source: string;
  title: string;
  raw_log: string | null;
  parsed: Record<string, unknown>;
  status: string;
  created_at: string | null;
}

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    ...opts,
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => req<{ status: string; app: string; llm_configured: boolean }>("/api/health"),
  incidents: () => req<Incident[]>("/api/incidents"),
  incident: (id: number) => req<Incident>(`/api/incidents/${id}`),
  alerts: () => req<Alert[]>("/api/alerts"),
  seed: () => req<{ seeded: number }>("/api/seed", { method: "POST" }),
  action: (id: number, action: "approved" | "rejected", note?: string) =>
    req<Incident>(`/api/incidents/${id}/action`, {
      method: "POST",
      body: JSON.stringify({ action, note: note || null }),
    }),
  createAlert: (raw_log: string) =>
    req<{ incident: Incident }>("/api/alerts", {
      method: "POST",
      body: JSON.stringify({ source: "auth_log", raw_log }),
    }),
};

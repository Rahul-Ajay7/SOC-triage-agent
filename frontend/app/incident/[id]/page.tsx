"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Incident } from "@/lib/api";
import VerdictBadge from "@/components/VerdictBadge";
import MitreMap from "@/components/MitreMap";
import AgentTrace from "@/components/AgentTrace";
import ActionPanel from "@/components/ActionPanel";

export default function IncidentDetail({ params }: { params: { id: string } }) {
  const id = Number(params.id);
  const [incident, setIncident] = useState<Incident | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.incident(id).then(setIncident).catch((e) => setError((e as Error).message));
  }, [id]);

  if (error) {
    return (
      <div className="rounded-lg border border-critical/40 bg-critical/10 p-4 text-critical">
        {error}
      </div>
    );
  }
  if (!incident) {
    return <p className="text-muted">Loading incident #{id}…</p>;
  }

  const iocs = incident.iocs || {};
  const chips = [
    ...(iocs.ips || []).map((x) => `IP ${x}`),
    ...(iocs.users || []).map((x) => `user ${x}`),
    ...(iocs.hashes || []).map((x) => `hash ${x.slice(0, 12)}…`),
  ];

  return (
    <div className="space-y-6">
      <Link href="/" className="text-sm text-accent hover:underline">
        ← Back to queue
      </Link>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
        {/* main */}
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <VerdictBadge verdict={incident.verdict} />
            <span className="text-sm text-muted">
              confidence {Math.round((incident.confidence || 0) * 100)}%
            </span>
            <span className="rounded-full border border-edge px-2 py-0.5 text-[11px] text-muted">
              engine: {incident.llm_source}
            </span>
          </div>

          <p className="rounded-lg border border-edge bg-panel2 p-4 text-sm leading-relaxed">
            {incident.summary}
          </p>

          <div>
            <h4 className="mb-2 text-xs font-semibold uppercase text-muted">IOCs</h4>
            <div className="flex flex-wrap gap-2">
              {chips.length ? (
                chips.map((c, i) => (
                  <span
                    key={i}
                    className="rounded border border-edge bg-panel2 px-2.5 py-1 text-xs"
                  >
                    {c}
                  </span>
                ))
              ) : (
                <span className="text-sm text-muted">none</span>
              )}
            </div>
          </div>

          <div>
            <h4 className="mb-2 text-xs font-semibold uppercase text-muted">MITRE ATT&CK</h4>
            <MitreMap mitre={incident.mitre} />
          </div>

          <div>
            <h3 className="mb-3 text-base font-semibold">🧠 Agent reasoning trace</h3>
            <AgentTrace trace={incident.trace || []} />
          </div>
        </div>

        {/* side */}
        <aside>
          <ActionPanel incident={incident} onChange={setIncident} />
        </aside>
      </div>
    </div>
  );
}

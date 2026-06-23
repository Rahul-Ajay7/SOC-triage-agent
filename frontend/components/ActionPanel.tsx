"use client";

import { useState } from "react";
import { api, type Incident } from "@/lib/api";

export default function ActionPanel({
  incident,
  onChange,
}: {
  incident: Incident;
  onChange: (i: Incident) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");

  async function act(action: "approved" | "rejected") {
    setBusy(true);
    try {
      const updated = await api.action(incident.id, action, note);
      onChange(updated);
    } catch (e) {
      alert("Action failed: " + (e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-lg border border-edge bg-panel2 p-4">
      <div className="mb-3 flex items-center gap-2">
        <h4 className="text-xs font-semibold uppercase text-muted">Analyst decision</h4>
        <span
          className={`text-xs ${
            incident.action === "approved"
              ? "text-benign"
              : incident.action === "rejected"
              ? "text-critical"
              : "text-muted"
          }`}
        >
          · {incident.action}
        </span>
      </div>
      <input
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Optional note…"
        className="mb-3 w-full rounded border border-edge bg-bg px-3 py-2 text-sm outline-none focus:border-accent"
      />
      <div className="flex gap-2">
        <button
          disabled={busy}
          onClick={() => act("approved")}
          className="rounded border border-benign px-3 py-2 text-sm text-benign hover:bg-benign/10 disabled:opacity-50"
        >
          Approve
        </button>
        <button
          disabled={busy}
          onClick={() => act("rejected")}
          className="rounded border border-critical px-3 py-2 text-sm text-critical hover:bg-critical/10 disabled:opacity-50"
        >
          Reject
        </button>
      </div>
      {incident.action_note && (
        <p className="mt-3 text-xs text-muted">Note: {incident.action_note}</p>
      )}
    </div>
  );
}

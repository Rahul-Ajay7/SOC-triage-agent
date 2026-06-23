import type { Mitre } from "@/lib/api";

export default function MitreMap({ mitre }: { mitre: Mitre[] }) {
  if (!mitre?.length) {
    return <span className="text-sm text-muted">No techniques mapped.</span>;
  }
  return (
    <div className="flex flex-wrap gap-2">
      {mitre.map((m) => (
        <a
          key={m.id}
          href={m.url}
          target="_blank"
          rel="noreferrer"
          title={`${m.tactic} — ${m.reason}`}
          className="rounded border border-accent px-2.5 py-1 text-xs text-accent hover:bg-accent/10"
        >
          {m.id} · {m.name}
        </a>
      ))}
    </div>
  );
}

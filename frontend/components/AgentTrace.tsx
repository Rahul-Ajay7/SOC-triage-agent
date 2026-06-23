// The star feature — replays the agent's reasoning step by step.
import type { TraceStep } from "@/lib/api";

const ICONS: Record<string, string> = {
  ingest: "📥",
  extract_iocs: "🔍",
  enrich: "🛠️",
  assess: "⚖️",
  classify: "🏷️",
  summarize: "📝",
};

export default function AgentTrace({ trace }: { trace: TraceStep[] }) {
  if (!trace?.length) {
    return <p className="text-sm text-muted">No trace recorded.</p>;
  }
  return (
    <ol className="relative ml-2 border-l-2 border-edge">
      {trace.map((s, i) => {
        const looped = s.iteration > 0 && s.step === "enrich";
        return (
          <li key={i} className="relative mb-5 pl-8">
            <span
              className={`absolute -left-[13px] flex h-6 w-6 items-center justify-center rounded-full border-2 bg-bg text-[11px] ${
                looped ? "border-suspicious" : "border-accent"
              }`}
            >
              {ICONS[s.step] || "•"}
            </span>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold">{s.label}</span>
              {s.iteration > 0 && (
                <span className="rounded border border-edge px-1.5 py-0.5 text-[10px] text-muted">
                  loop {s.iteration}
                </span>
              )}
            </div>
            <p className="mt-1 text-sm leading-relaxed text-muted">{s.detail}</p>
          </li>
        );
      })}
    </ol>
  );
}

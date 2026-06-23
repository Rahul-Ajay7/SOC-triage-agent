import type { Verdict } from "@/lib/api";

const STYLES: Record<Verdict, string> = {
  benign: "bg-benign/15 text-benign",
  suspicious: "bg-suspicious/15 text-suspicious",
  critical: "bg-critical/15 text-critical",
};

export default function VerdictBadge({ verdict }: { verdict: Verdict }) {
  return (
    <span
      className={`rounded px-2.5 py-1 text-xs font-bold uppercase tracking-wide ${STYLES[verdict]}`}
    >
      {verdict}
    </span>
  );
}

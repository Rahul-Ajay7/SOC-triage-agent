"use client";

import Link from "next/link";
import type { Incident } from "@/lib/api";
import VerdictBadge from "./VerdictBadge";

export default function AlertQueue({ incidents }: { incidents: Incident[] }) {
  if (!incidents.length) {
    return (
      <div className="rounded-lg border border-edge bg-panel p-10 text-center text-muted">
        No incidents yet — click “Load demo alerts”.
      </div>
    );
  }
  return (
    <div className="overflow-hidden rounded-lg border border-edge bg-panel">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-muted">
            <th className="p-3">#</th>
            <th className="p-3">Verdict</th>
            <th className="p-3">Conf.</th>
            <th className="p-3">Summary</th>
            <th className="p-3">Action</th>
          </tr>
        </thead>
        <tbody>
          {incidents.map((i) => (
            <tr key={i.id} className="border-t border-edge hover:bg-panel2">
              <td className="p-3">
                <Link href={`/incident/${i.id}`} className="text-accent hover:underline">
                  {i.id}
                </Link>
              </td>
              <td className="p-3">
                <VerdictBadge verdict={i.verdict} />
              </td>
              <td className="p-3">{Math.round((i.confidence || 0) * 100)}%</td>
              <td className="max-w-[280px] truncate p-3 text-muted" title={i.summary}>
                <Link href={`/incident/${i.id}`}>{i.summary}</Link>
              </td>
              <td className="p-3">
                <span
                  className={
                    i.action === "approved"
                      ? "text-benign"
                      : i.action === "rejected"
                      ? "text-critical"
                      : "text-muted"
                  }
                >
                  {i.action}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

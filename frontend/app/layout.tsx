import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "SOC Triage Agent",
  description: "Autonomous SOC alert triage with a LangGraph reasoning loop",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="flex items-center justify-between border-b border-edge px-6 py-4">
          <Link href="/" className="flex items-center gap-3">
            <span className="text-3xl">🛡️</span>
            <div>
              <h1 className="text-lg font-semibold tracking-wide">SOC Triage Agent</h1>
              <p className="text-xs text-muted">
                Autonomous alert triage · LangGraph reasoning loop
              </p>
            </div>
          </Link>
          <nav className="flex gap-4 text-sm text-muted">
            <Link href="/" className="hover:text-white">Dashboard</Link>
            <Link href="/alerts" className="hover:text-white">Alerts</Link>
          </nav>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-6">{children}</main>
      </body>
    </html>
  );
}

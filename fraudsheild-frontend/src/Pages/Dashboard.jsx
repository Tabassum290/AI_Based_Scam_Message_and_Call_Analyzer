import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getStats } from "../Api";
import { RiskPill } from "./ScanResult";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      setData(await getStats());
    } catch (e) {
      setError(
        e.message === "Ball cholbo na "
          ? "Could not reach the server. Please check that the backend is running."
          : e.message || "Could not load the dashboard."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const stats = data && [
    [data.checks, "Checks run"],
    [data.scams, "Flagged as scams"],
    [data.reports, "Reports filed"],
    [data.scams_week, "Scams caught this week"],
  ];
  const max = data ? Math.max(1, ...data.week.map((d) => d.count)) : 1;
  const maxType = data ? Math.max(1, ...data.by_type.map((t) => t.count)) : 1;

  return (
    <main className="mx-auto max-w-6xl px-4 pb-16 pt-8 md:px-10">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold">Dashboard</h1>
          <p className="mt-1 opacity-70">Your checks, reports and weekly activity in one place.</p>
        </div>
        <Link to="/scan" className="btn btn-primary text-white">Scan a message</Link>
      </div>

      {/* Loading */}
      {loading && !data && (
        <div className="flex items-center gap-3 py-16 opacity-70">
          <span className="loading loading-spinner" aria-hidden="true" />
          Loading your dashboard…
        </div>
      )}

      {/* Error */}
      {error && (
        <div role="alert" className="alert alert-error mb-4 flex justify-between">
          <span>{error}</span>
          <button className="btn btn-sm" onClick={load} disabled={loading}>
            {loading ? "Trying…" : "Try again"}
          </button>
        </div>
      )}

      {data && (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {stats.map(([n, label]) => (
              <div key={label} className="card border border-base-300 bg-base-100">
                <div className="card-body p-5">
                  <b className="font-display text-3xl">{n}</b>
                  <span className="text-sm opacity-70">{label}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-[1.1fr_.9fr]">
            {/* Last 7 days */}
            <div className="card border border-base-300 bg-base-100"><div className="card-body">
              <h2 className="font-display text-lg font-bold">Scams caught, last 7 days</h2>
              <div className="mt-3 flex h-44 items-end gap-3">
                {data.week.map((d, i) => (
                  <div key={i} className="flex-1 text-center text-xs opacity-80">
                    <div className="mb-1 font-semibold">{d.count}</div>
                    <div
                      className="mb-1 rounded-t-md bg-primary"
                      style={{ height: `${Math.max(2, (d.count / max) * 100)}px` }}
                      title={`${d.count} on ${d.day}`}
                    />
                    {d.day}
                  </div>
                ))}
              </div>
            </div></div>

            {/* Recent checks */}
            <div className="card border border-base-300 bg-base-100"><div className="card-body">
              <h2 className="font-display text-lg font-bold">Recent checks</h2>
              {data.recent.length === 0 ? (
                <p className="mt-2 text-sm opacity-70">
                  No checks yet. Scan a message to see it here.
                </p>
              ) : (
                <ul className="mt-2 divide-y divide-base-300">
                  {data.recent.map((c) => (
                    <li key={c.id} className="flex items-center justify-between gap-3 py-2.5">
                      <span className="truncate"><b>{c.type_label}</b> · {c.summary}</span>
                      <RiskPill score={c.score} />
                    </li>
                  ))}
                </ul>
              )}
            </div></div>
          </div>

          {/* Scam types */}
          <div className="card mt-4 border border-base-300 bg-base-100"><div className="card-body">
            <h2 className="font-display text-lg font-bold">Scam types detected</h2>
            {data.by_type.length === 0 ? (
              <p className="mt-2 text-sm opacity-70">Scam hoy nai.</p>
            ) : (
              <ul className="mt-2 grid gap-3">
                {data.by_type.map((t) => (
                  <li key={t.label}>
                    <div className="mb-1 flex justify-between text-sm">
                      <span>{t.label}</span>
                      <b>{t.count}</b>
                    </div>
                    <div className="h-2 rounded-full bg-base-200">
                      <div
                        className="h-2 rounded-full bg-primary"
                        style={{ width: `${(t.count / maxType) * 100}%` }}
                      />
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div></div>
        </>
      )}
    </main>
  );
}
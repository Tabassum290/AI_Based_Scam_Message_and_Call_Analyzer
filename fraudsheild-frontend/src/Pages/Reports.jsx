import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { createReport, getReports } from "../Api";

const TYPES = [
  "Phishing message",
  "Fake payment request",
  "Account takeover",
  "Impersonation call",
  "Other",
];

const friendly = (e, fallback) =>
  e.message === "Failed to fetch"
    ? "Could not reach the server. Please check that the backend is running."
    : e.message || fallback;

export default function Reports() {
  const { state } = useLocation(); // the "Report this" button sends the message text here

  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [form, setForm] = useState({
    type: TYPES[0],
    source: "",
    amount: "",
    description: state?.description ?? "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  const set = (key) => (e) => {
    setForm({ ...form, [key]: e.target.value });
    setDone(false);
  };

  async function load() {
    setLoading(true);
    setLoadError("");
    try {
      setReports(await getReports());
    } catch (e) {
      setLoadError(friendly(e, "Could not load reports."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function submit() {
    if (!form.source.trim() && !form.description.trim()) {
      setError("Add the sender or a short description so the report can be reviewed.");
      return;
    }
    setError("");
    setSaving(true);
    try {
      const saved = await createReport({
        type: form.type,
        source: form.source.trim(),
        description: form.description.trim(),
        amount: Number(form.amount) || 0,
      });
      setReports((prev) => [saved, ...prev]);
      setForm({ type: TYPES[0], source: "", amount: "", description: "" });
      setDone(true);
    } catch (e) {
      setError(friendly(e, "Could not submit the report. Please try again."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="mx-auto max-w-6xl px-4 pb-16 pt-8 md:px-10">
      <h1 className="font-display text-3xl font-bold">Fraud reports</h1>
      <p className="mb-6 mt-1 opacity-70">Report a scam so others can be warned.</p>

      <div className="grid gap-4 lg:grid-cols-[.9fr_1.1fr]">
        {/* Form */}
        <div className="card border border-base-300 bg-base-100">
          <div className="card-body gap-1">
            <h2 className="font-display text-lg font-bold">New report</h2>

            <label htmlFor="rtype" className="mt-2 text-sm font-semibold">What happened?</label>
            <select id="rtype" value={form.type} onChange={set("type")} className="select select-bordered w-full">
              {TYPES.map((t) => <option key={t}>{t}</option>)}
            </select>

            <label htmlFor="rsrc" className="mt-2 text-sm font-semibold">Sender, number, or website</label>
            <input id="rsrc" value={form.source} onChange={set("source")}
              placeholder="e.g. +1 555 0100 or pay-verify.example" className="input input-bordered w-full" />

            <label htmlFor="ramt" className="mt-2 text-sm font-semibold">Money lost (optional)</label>
            <input id="ramt" type="number" min="0" value={form.amount} onChange={set("amount")}
              placeholder="0" className="input input-bordered w-full" />

            <label htmlFor="rdesc" className="mt-2 text-sm font-semibold">What did they say or do?</label>
            <textarea id="rdesc" value={form.description} onChange={set("description")}
              className="textarea textarea-bordered min-h-24 w-full" />

            {error && <p role="alert" className="text-sm text-error">{error}</p>}
            {done && <p role="status" className="text-sm text-success">Report submitted. Thank you for helping others.</p>}

            <button className="btn btn-primary mt-3 w-fit text-blue-800 px-2" onClick={submit} disabled={saving}>
              {saving ? "Submitting…" : "Submit Report"}
            </button>
          </div>
        </div>

        {/* List */}
        <div className="card border border-base-300 bg-base-100">
          <div className="card-body">
            <h2 className="font-display text-lg font-bold">Your reports</h2>

            {loadError && (
              <div role="alert" className="alert alert-error flex justify-between">
                <span>{loadError}</span>
                <button className="btn btn-sm" onClick={load} disabled={loading}>Try again</button>
              </div>
            )}

            {loading && !loadError ? (
              <div className="flex items-center gap-3 py-6 opacity-70">
                <span className="loading loading-spinner" aria-hidden="true" /> Loading reports…
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="table">
                  <thead>
                    <tr><th>Type</th><th>Source</th><th>Status</th></tr>
                  </thead>
                  <tbody>
                    {reports.length === 0 && !loadError && (
                      <tr><td colSpan={3}>No reports yet.</td></tr>
                    )}
                    {reports.map((r) => (
                      <tr key={r.id}>
                        <td>{r.type}</td>
                        <td className="break-all">{r.source || "Not given"}</td>
                        <td>
                          <span className={`badge badge-outline ${r.status === "Confirmed" ? "badge-error" : "badge-warning"}`}>
                            {r.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
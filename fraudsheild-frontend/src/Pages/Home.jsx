import { useState } from "react";
import { Link } from "react-router-dom";
import ScanResult from "./ScanResult";
import { useApp } from "./AppProvider";
import { scanText, toSegments } from "../Api";

// const SAMPLE = "You have won a $500 gift card! Claim your reward within 1 hour at http://claim-prize.example and send the OTP to confirm.";

const FEATURES = [
  { to: "/scan", title: "Message scanner", text: "Highlights pressure, fake links and requests for codes." },
  { to: "/reports", title: "Fraud reports", text: "Report a scam so others can be warned." },
];
const STEPS = [
  ["Paste or upload.", "Add the message or a screenshot."],
  ["Decide and report.", "Ignore it, confirm through a trusted number, or report it."],
];
const TIPS = [
  "Never share an OTP, PIN or password. Real companies don’t ask.",
  "Don’t pay to claim a prize or refund.",
  "Call the company on a number you already trust.",
];

export default function Home() {
  const { addCheck } = useApp();
  const [message, setMessage] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleCheck() {
    const text = message.trim();
    if (!text) { setError("Paste a message first."); setResult(null); return; }
    setError("");
    setLoading(true);
    try {
      const data = await scanText(text);
      setResult({ ...data, segments: toSegments(text, data.highlights) });
      addCheck({ type: "Message", summary: text.slice(0, 44) + (text.length > 44 ? "…" : ""), score: data.score });
    } catch (e) {
      setResult(null);
      setError(e.message || "Could not reach the server. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-6xl px-4 pb-16 pt-8 md:px-10">
      <section className="grid items-start gap-8 xl:grid-cols-[1.05fr_.95fr]">
        <div>
          <h1 className="font-display text-4xl font-bold leading-tight tracking-tight md:text-5xl">
            Got a strange message? Check it before you reply.
          </h1>
          <p className="mt-4 max-w-[46ch] text-lg opacity-70">
            Checkpoint scans messages and screenshots for the tricks scammers use, and tells you in plain words what looks wrong.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link to="/scan" className="btn btn-primary text-white ">Scan a message</Link>
            <Link to="/about" className="btn btn-outline">About us</Link>
          </div>
        </div>

        {/* <div className="card border border-base-300 bg-base-100">
          <div className="card-body">
            <h2 className="font-display text-lg font-bold">Try it now</h2>
            <label htmlFor="heroMsg" className="text-sm font-semibold">Paste a message</label>
            <textarea id="heroMsg" value={message} onChange={(e) => setMessage(e.target.value)}
              placeholder="Paste an SMS, email or chat message" className="textarea textarea-bordered min-h-28 w-full" />
            {error && <p role="alert" className="text-sm text-error">{error}</p>}
            <div className="flex flex-wrap gap-3">
              <button className="btn btn-primary" onClick={handleCheck} disabled={loading}>
                {loading ? "Checking…" : "Check this message"}
              </button>
              <button className="btn btn-outline" onClick={() => setMessage(SAMPLE)}>Use a sample scam</button>
            </div>
            {result && <ScanResult result={result} text={message} />}
          </div>
        </div> */}
      </section>

      <h2 className="font-display mb-4 mt-10 text-xl font-bold">Three ways to stay safe</h2>
      <div className="grid gap-4 md:grid-cols-3">
        {FEATURES.map((f) => (
          <Link key={f.title} to={f.to} className="card border border-base-300 bg-base-100 transition-colors hover:border-primary">
            <div className="card-body">
              <h3 className="font-display text-base font-bold">{f.title}</h3>
              <p className="text-sm opacity-70">{f.text}</p>
            </div>
          </Link>
        ))}
      </div>

      <div className="mt-10 grid gap-4 md:grid-cols-2">
        <div className="card border border-base-300 bg-base-100"><div className="card-body">
          <h2 className="font-display text-lg font-bold">How a check works</h2>
          <ol className="mt-2 grid list-decimal gap-3 pl-5">
            {STEPS.map(([b, r]) => <li key={b}><b>{b}</b> {r}</li>)}
          </ol>
        </div></div>
        <div className="card border border-base-300 bg-base-100"><div className="card-body">
          <h2 className="font-display text-lg font-bold">Four rules that stop most scams</h2>
          <ul className="mt-2 grid list-disc gap-3 pl-5">{TIPS.map((t) => <li key={t}>{t}</li>)}</ul>
        </div></div>
      </div>

      <p className="mt-8 text-sm opacity-70">
        Checkpoint gives guidance, not a guarantee. If you’ve already lost money, contact your bank straight away.
      </p>
    </main>
  );
}
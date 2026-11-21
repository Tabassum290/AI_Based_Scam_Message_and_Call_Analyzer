import { useState } from "react";
import ScanResult from "./ScanResult";
import { useApp } from "./AppProvider";
import { scanText, toSegments } from "../Api";

const SAMPLE =
  "You have won a $500 gift card! Claim your reward within 1 hour at http://claim-prize.example and send the OTP to confirm.";

const MAX_CHARS = 2000; // same limit as the backend

export default function Message() {
  const { addCheck } = useApp();

  const [message, setMessage] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleCheck() {
    const text = message.trim();

    if (!text) {
      setError("Please paste a message before scanning.");
      setResult(null);
      return;
    }

    if (text.length > MAX_CHARS) {
      setError(`This message is too long. Please keep it under ${MAX_CHARS} characters.`);
      setResult(null);
      return;
    }

    setError("");
    setLoading(true);

    try {
      // Ask the FastAPI backend (XLM-RoBERTa model) to scan the message
      const data = await scanText(text);

      setResult({ ...data, segments: toSegments(text, data.highlights) });

      addCheck({
        type: "Message",
        summary: text.slice(0, 44) + (text.length > 44 ? "…" : ""),
        score: data.score,
      });
    } catch (e) {
      setResult(null);
      setError(
        e.message === "Failed to fetch"
          ? "Could not reach the server. Please check that the backend is running."
          : e.message || "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  function handleSample() {
    setMessage(SAMPLE);
    setResult(null);
    setError("");
  }

  function handleClear() {
    setMessage("");
    setResult(null);
    setError("");
  }

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-5 py-10 md:px-10">

      {/* Page Heading */}
      <div className="mb-8">
        <h1 className="font-heading text-3xl font-bold tracking-tight md:text-4xl">
          Message Scanner
        </h1>

        <p className="mt-3 max-w-2xl text-base leading-7 text-base-content/70 md:text-lg">
          Check suspicious SMS, emails, and chat messages.
          Our scanner analyzes the text and highlights possible
          scam indicators to help you stay safe.
        </p>
      </div>

      {/* Scanner Card */}
      <section className="card border border-base-300 bg-base-100 shadow-sm">
        <div className="card-body gap-5 p-6 md:p-8">

          <div>
            <h2 className="text-xl font-bold md:text-2xl">
              Paste your message
            </h2>

            <p className="mt-2 text-sm leading-6 text-base-content/60 md:text-base">
              Copy the suspicious message and paste it below
              for analysis.
            </p>
          </div>

          {/* Textarea */}
          <div>
            <div className="mb-2 flex items-center justify-between">
              <label
                htmlFor="message"
                className="text-sm font-semibold md:text-base"
              >
                Message content
              </label>

              <span
                className={`text-xs ${
                  message.length > MAX_CHARS ? "text-error" : "text-base-content/50"
                }`}
              >
                {message.length} / {MAX_CHARS} characters
              </span>
            </div>

            <textarea
              id="message"
              value={message}
              onChange={(e) => {
                setMessage(e.target.value);
                setError("");
                setResult(null);
              }}
              disabled={loading}
              placeholder="Paste your SMS, email, WhatsApp message, or any suspicious text here..."
              className="textarea textarea-bordered min-h-56 w-full resize-y p-4 text-base leading-7 focus:outline-primary md:min-h-64 md:text-lg"
            />

            {error && (
              <p role="alert" className="mt-2 text-sm text-error">
                {error}
              </p>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-3">

            <button
              onClick={handleCheck}
              disabled={loading}
              className="btn btn-primary px-7 text-base border-2"
            >
              {loading ? "Scanning…" : "Scan Message"}
            </button>

            <button
              onClick={handleSample}
              disabled={loading}
              className="btn btn-outline"
            >
              Try Sample
            </button>

            <button
              onClick={handleClear}
              className="btn btn-ghost"
              disabled={loading || (!message && !result)}
            >
              Clear
            </button>

          </div>

          {/* Result */}
          {result && (
            <div className="mt-4 border-t border-base-300 pt-6">
              <h2 className="mb-4 text-xl font-bold">
                Scan Result
              </h2>

              <ScanResult result={result} text={message} />
            </div>
          )}

        </div>
      </section>

      {/* Safety Information */}
      <div className="mt-6 rounded-xl border border-base-300 bg-base-100 p-5">
        <h3 className="font-semibold">
          <span className="mr-2">🛡️</span>
          Stay Safe
        </h3>

        <p className="mt-2 text-sm leading-6 text-base-content/65">
          Never share your OTP, PIN, or password with anyone.
          Always verify suspicious requests through official
          contact channels.
        </p>
      </div>

    </main>
  );
}
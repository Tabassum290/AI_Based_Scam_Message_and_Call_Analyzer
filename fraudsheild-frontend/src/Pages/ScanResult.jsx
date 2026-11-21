
import { useNavigate } from "react-router-dom";
import { levelKey, LEVELS } from "./scan";

export function RiskPill({ score, riskLevel }) {
  const level = riskLevel || LEVELS[levelKey(score)].label;

  const colors = {
    "Low Risk": "bg-success/15 text-success",
    "Medium Risk": "bg-warning/15 text-warning",
    "High Risk": "bg-error/15 text-error",
  };

  return (
    <span
      className={`inline-block rounded-full px-3 py-1 text-xs font-semibold ${
        colors[level] || "bg-base-200"
      }`}
    >
      {level}
    </span>
  );
}

function Gauge({ score }) {
  const safeScore = Math.max(0, Math.min(100, Number(score) || 0));

  const length = Math.PI * 80;
  const offset = length * (1 - safeScore / 100);

  return (
    <div className="mx-auto w-[170px] text-center">
      <svg
        viewBox="0 0 200 110"
        aria-hidden="true"
        className="block h-[100px] w-[170px]"
      >
        <path
          d="M20 100A80 80 0 0 1 180 100"
          fill="none"
          strokeWidth="16"
          strokeLinecap="round"
          className="stroke-base-300"
        />

        <path
          d="M20 100A80 80 0 0 1 180 100"
          fill="none"
          strokeWidth="16"
          strokeLinecap="round"
          strokeDasharray={length}
          strokeDashoffset={offset}
          className={LEVELS[levelKey(safeScore)].stroke}
        />
      </svg>

      <b className="font-display -mt-9 block text-3xl">
        {safeScore.toFixed(2)}
      </b>

      <small className="opacity-60">out of 100</small>
    </div>
  );
}

export default function ScanResult({ result, text }) {
  const navigate = useNavigate();

  const score = Number(result.score) || 0;

  const isScam = result.verdict === "SCAM";

  const riskLevel =
    result.risk_level || LEVELS[levelKey(score)].label;

  const flags = result.flags || [];

  const segments = result.segments || [
    { text: text, hit: false },
  ];

  return (
    <div className="mt-5 grid items-center gap-5 sm:grid-cols-[170px_1fr]">

      {/* Risk Gauge */}
      <Gauge score={score} />

      <div className="min-w-0">

        {/* Verdict */}
        <div className="mb-3 flex flex-wrap items-center gap-2">

          <span
            className={`rounded-full px-3 py-1 text-sm font-bold ${
              isScam
                ? "bg-error/15 text-error"
                : "bg-success/15 text-success"
            }`}
          >
            {isScam ? "SCAM DETECTED" : "NOT SCAM"}
          </span>

          <RiskPill
            score={score}
            riskLevel={riskLevel}
          />

        </div>

        {/* Prediction Type */}
        <h3 className="text-lg font-bold">
          {result.type_label ||
            (isScam ? "Suspicious message" : "Looks legitimate")}
        </h3>

        {/* Explanation */}
        <p className="mt-2 text-sm leading-6 text-base-content/70">
          {result.message ||
            (isScam
              ? "This message contains suspicious patterns. Be careful."
              : "This message looks legitimate. Nothing suspicious was detected.")}
        </p>

        {/* Scam Flags */}
        {flags.length > 0 && (
          <ul className="mt-3 grid gap-2">
            {flags.map((f, index) => (
              <li
                key={`${f.label}-${index}`}
                className={`rounded-lg border-l-4 bg-base-200 px-3 py-2 ${
                  f.weight >= 25
                    ? "border-error"
                    : "border-warning"
                }`}
              >
                {f.label}
                {f.count > 1 ? ` (${f.count}×)` : ""}
              </li>
            ))}
          </ul>
        )}

        {/* Original Message with Highlights */}
        <div className="mt-3 whitespace-pre-wrap break-words rounded-lg bg-base-200 p-3">
          {segments.map((s, i) =>
            s.hit ? (
              <mark
                key={i}
                className="rounded bg-error/15 px-1 font-semibold text-error"
              >
                {s.text}
              </mark>
            ) : (
              <span key={i}>{s.text}</span>
            )
          )}
        </div>

        {/* Report Button */}
        {isScam && (
          <button
            className="btn btn-outline btn-sm mt-3"
            onClick={() =>
              navigate("/reports", {
                state: { description: text },
              })
            }
          >
            Report this
          </button>
        )}

      </div>
    </div>
  );
}

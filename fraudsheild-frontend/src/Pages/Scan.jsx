// Front-end only scam checker (simple keyword rules). Swap analyze() for an API call later.
export const RULES = [
  [/urgent(ly)?|immediately|act now|last warning|within \d+ (hours?|minutes?)/gi, 18, "Pressure to act fast"],
  [/\botp\b|\bpin\b|password|\bcvv\b|one[- ]time (code|password)/gi, 30, "Asks for a secret code"],
  [/https?:\/\/\S+|bit\.ly\S*|tinyurl\S*|\bwww\.\S+/gi, 15, "Contains a link"],
  [/suspend(ed)?|blocked|locked|verify your account|unusual activity/gi, 18, "Threat to your account"],
  [/\bwon\b|prize|lottery|reward|gift card|claim your/gi, 20, "Prize or reward bait"],
  [/send (money|funds)|wire|bitcoin|crypto|transfer/gi, 15, "Asks for money"],
];

export const SAMPLE =
  "URGENT: Your account is suspended due to unusual activity. Verify your account within 2 hours at http://secure-bank-verify.example and reply with the OTP we sent you.";

// Full class names are written out so Tailwind can detect them.
export const LEVELS = {
  low: { label: "Low risk", pill: "bg-success/15 text-success", stroke: "stroke-success",
    advice: "Nothing here looks unusual. Stay careful with links from unknown senders." },
  med: { label: "Medium risk", pill: "bg-warning/20 text-warning", stroke: "stroke-warning",
    advice: "Some warning signs. Don’t click links or reply. Contact the company using a number you already trust." },
  high: { label: "High risk", pill: "bg-error/15 text-error", stroke: "stroke-error",
    advice: "This looks like a scam. Don’t reply, click, or share codes. Report it so others are warned." },
};

export const levelKey = (score) => (score < 25 ? "low" : score < 55 ? "med" : "high");

export function analyze(text) {
  let score = 0;
  const flags = [];
  const ranges = [];
  RULES.forEach(([re, weight, label]) => {
    const matches = [...text.matchAll(re)];
    if (matches.length) {
      score += weight;
      flags.push({ label, weight, count: matches.length });
      matches.forEach((m) => ranges.push([m.index, m.index + m[0].length]));
    }
  });
  ranges.sort((a, b) => a[0] - b[0]);
  const merged = [];
  ranges.forEach((r) => {
    const last = merged[merged.length - 1];
    if (last && r[0] <= last[1]) last[1] = Math.max(last[1], r[1]);
    else merged.push([...r]);
  });
  const segments = [];
  let pos = 0;
  merged.forEach(([a, b]) => {
    if (a > pos) segments.push({ text: text.slice(pos, a), hit: false });
    segments.push({ text: text.slice(a, b), hit: true });
    pos = b;
  });
  if (pos < text.length) segments.push({ text: text.slice(pos), hit: false });
  return { score: Math.min(100, score), flags, segments };
}
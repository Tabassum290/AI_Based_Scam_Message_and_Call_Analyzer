// src/api.js
const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request(path, options) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const scanText = (text) =>
  request("/api/scan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

export const ocrImage = (file) => {
  const form = new FormData();
  form.append("file", file);
  return request("/api/ocr", { method: "POST", body: form });
};

export const createReport = (report) =>
  request("/api/reports", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(report),
  });

export const getReports = () => request("/api/reports");

export const getStats = () => request("/api/stats");

// Turns the API's [start, end] highlight ranges into segments for rendering
export function toSegments(text, highlights = []) {
  const segments = [];
  let pos = 0;

  [...highlights]
    .sort((a, b) => a[0] - b[0])
    .forEach(([a, b]) => {
      if (a < pos || b <= a) return;

      if (a > pos) {
        segments.push({
          text: text.slice(pos, a),
          hit: false,
        });
      }

      segments.push({
        text: text.slice(a, b),
        hit: true,
      });

      pos = b;
    });

  if (pos < text.length) {
    segments.push({
      text: text.slice(pos),
      hit: false,
    });
  }

  return segments;
}
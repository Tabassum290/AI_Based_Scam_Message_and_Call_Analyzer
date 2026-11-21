import { createContext, useContext, useState } from "react";

const Ctx = createContext(null);
export const useApp = () => useContext(Ctx);

export const WEEK = [4, 7, 5, 9, 6, 3, 8]; // demo data: scams caught Mon–Sun

const SEED_CHECKS = [
  { id: 1, type: "Message", summary: "Your bank account is locked. Verify now…", score: 88 },
  { id: 2, type: "Screenshot", summary: "Customer care: send money to unlock…", score: 72 },
  { id: 3, type: "Message", summary: "Hi, your parcel is at the depot", score: 34 },
  { id: 4, type: "Message", summary: "See you at 6 tonight?", score: 3 },
];
const SEED_REPORTS = [
  { id: 1, type: "Phishing message", source: "pay-verify.example", status: "Under review" },
  { id: 2, type: "Impersonation call", source: "+1 555 0142", status: "Confirmed" },
];

export function AppProvider({ children }) {
  const [checks, setChecks] = useState(SEED_CHECKS);
  const [reports, setReports] = useState(SEED_REPORTS);

  const addCheck = (c) => setChecks((p) => [{ id: Date.now(), ...c }, ...p]);
  const addReport = (r) => setReports((p) => [{ id: Date.now(), status: "Under review", ...r }, ...p]);

  return <Ctx.Provider value={{ checks, reports, addCheck, addReport }}>{children}</Ctx.Provider>;
}
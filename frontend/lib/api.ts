import type { AnalyzePayload, StudyPlanDay, TopicStats } from "./types";

const API = process.env.NEXT_PUBLIC_API_URL || "";

export async function extractPaper(file: File): Promise<{ text: string; status: "success" | "failed" }> {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${API}/extract`, { method: "POST", body: fd });
  if (!r.ok) throw new Error("Extract request failed");
  return r.json();
}

export async function analyzeText(text: string, syllabus: string): Promise<AnalyzePayload> {
  const r = await fetch(`${API}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, syllabus }),
  });
  if (!r.ok) throw new Error("Analyze request failed");
  return r.json();
}

export async function buildPlan(topics: TopicStats[], days: number): Promise<StudyPlanDay[]> {
  const r = await fetch(`${API}/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topics, days }),
  });
  if (!r.ok) throw new Error("Plan request failed");
  const data = await r.json();
  return data.plan as StudyPlanDay[];
}

export function saveAnalyzeResult(data: AnalyzePayload) {
  if (typeof window === "undefined") return;
  sessionStorage.setItem("analyzer:last", JSON.stringify(data));
}

export function loadAnalyzeResult(): AnalyzePayload | null {
  if (typeof window === "undefined") return null;
  const raw = sessionStorage.getItem("analyzer:last");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AnalyzePayload;
  } catch {
    return null;
  }
}

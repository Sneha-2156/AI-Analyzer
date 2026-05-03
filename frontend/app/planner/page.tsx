"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { buildPlan, loadAnalyzeResult } from "@/lib/api";
import type { StudyPlanDay, TopicStats } from "@/lib/types";

export default function PlannerPage() {
  const [topics, setTopics] = useState<TopicStats[]>([]);
  const [days, setDays] = useState(5);
  const [plan, setPlan] = useState<StudyPlanDay[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const d = loadAnalyzeResult();
    setTopics(d?.topics ?? []);
  }, []);

  async function onGenerate() {
    setError(null);
    setBusy(true);
    try {
      const p = await buildPlan(topics, days);
      setPlan(p);
    } catch {
      setError("Could not build a plan. Is the backend running?");
    } finally {
      setBusy(false);
    }
  }

  if (!topics.length) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-slate-700">Run an analysis first to get topic stats.</p>
        <Link href="/" className="mt-4 inline-block text-sm font-semibold text-accent">
          Go to Upload
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Study planner</h1>
        <p className="mt-1 text-slate-600">Generate a day-by-day plan from your topic scores (AI + rule merge on the server).</p>
      </div>

      <div className="flex flex-wrap items-end gap-4">
        <div>
          <label htmlFor="planner-days" className="text-sm font-medium text-slate-800">
            Days
          </label>
          <input
            id="planner-days"
            type="number"
            min={1}
            max={30}
            value={days}
            onChange={(e) => setDays(Number(e.target.value) || 1)}
            className="mt-1 w-24 rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-accent focus:outline-none focus:ring-2 focus:ring-blue-100"
          />
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={onGenerate}
          className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow hover:bg-slate-800 disabled:opacity-50"
        >
          {busy ? "Generating..." : "Generate plan"}
        </button>
      </div>

      {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900">{error}</div>}

      {plan && (
        <div className="grid gap-4 md:grid-cols-2">
          {plan.map((d) => (
            <article key={d.day} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Day {d.day}</h2>
              <p className="mt-1 text-sm text-slate-600">{d.hours} hours - {d.focus}</p>
              <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-800">
                {d.topics.length === 0 && <li className="text-slate-500">Light review</li>}
                {d.topics.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

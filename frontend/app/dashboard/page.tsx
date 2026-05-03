"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { loadAnalyzeResult } from "@/lib/api";
import type { AnalyzePayload } from "@/lib/types";

export default function DashboardPage() {
  const [data, setData] = useState<AnalyzePayload | null>(null);

  useEffect(() => {
    setData(loadAnalyzeResult());
  }, []);

  const chartData = useMemo(() => {
    if (!data?.topics?.length) return [];
    return [...data.topics]
      .sort((a, b) => b.frequency - a.frequency)
      .map((t) => ({
        topic: t.topic.length > 28 ? `${t.topic.slice(0, 28)}...` : t.topic,
        full: t.topic,
        frequency: t.frequency,
        score: t.score,
      }));
  }, [data]);

  const sortedByYield = useMemo(() => {
    if (!data?.topics?.length) return [];
    return [...data.topics].sort((a, b) => b.score - a.score);
  }, [data]);

  const topTopic = sortedByYield[0]?.topic ?? "-";
  const totalQuestions = data?.questions?.length ?? 0;

  if (!data) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-slate-700">No analysis in session yet.</p>
        <Link href="/" className="mt-4 inline-block text-sm font-semibold text-accent">
          Go to Upload
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="mt-1 text-slate-600">High-yield topics, frequency, and quick stats from the last run.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Total questions</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">{totalQuestions}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Top topic (score)</p>
          <p className="mt-2 text-lg font-semibold text-slate-900">{topTopic}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Topics tracked</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">{data.topics.length}</p>
        </div>
      </div>

      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Frequency by topic</h2>
        <p className="text-sm text-slate-600">Bar chart (Recharts) - sorted by frequency for readability.</p>
        <div className="mt-4 h-80 w-full">
          {chartData.length === 0 ? (
            <p className="text-sm text-slate-500">No topic aggregates yet (classification may be weak).</p>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 8, right: 8, left: 8, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="topic" interval={0} angle={-18} textAnchor="end" height={60} tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} />
                <Tooltip
                  formatter={(value: number) => [`${value}`, "frequency"]}
                  labelFormatter={(_label, payload) => (payload?.[0] && (payload[0].payload as { full?: string }).full) || ""}
                />
                <Bar dataKey="frequency" fill="#2563eb" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">High-yield topics (sorted by score)</h2>
        <ul className="mt-3 divide-y divide-slate-100">
          {sortedByYield.map((t) => (
            <li key={t.topic} className="flex flex-wrap items-center justify-between gap-2 py-3 text-sm">
              <span className="font-medium text-slate-900">{t.topic}</span>
              <span className="text-slate-600">
                score {t.score.toFixed(1)} - freq {t.frequency} - marks {t.total_marks} - {t.trend}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <Link href="/planner" className="inline-block text-sm font-semibold text-accent">
        Build study plan -&gt;
      </Link>
    </div>
  );
}

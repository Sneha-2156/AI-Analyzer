"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { analyzeText, extractPaper, saveAnalyzeResult } from "@/lib/api";

export default function UploadPage() {
  const router = useRouter();
  const [syllabus, setSyllabus] = useState("");
  const [paperText, setPaperText] = useState("");
  const [extractStatus, setExtractStatus] = useState<"idle" | "success" | "failed">("idle");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onFile(file: File | null) {
    setError(null);
    if (!file) return;
    setBusy(true);
    try {
      const res = await extractPaper(file);
      setExtractStatus(res.status);
      if (res.status === "success") {
        setPaperText(res.text);
      } else {
        setPaperText("");
        setError("Extraction returned little text (< 200 characters). Paste the paper manually below.");
      }
    } catch {
      setError("Could not reach the API. Is the backend running on port 8000?");
    } finally {
      setBusy(false);
    }
  }

  async function onAnalyze() {
    setError(null);
    setBusy(true);
    try {
      const data = await analyzeText(paperText, syllabus);
      saveAnalyzeResult(data);
      router.push("/dashboard");
    } catch {
      setError("Analyze failed. Check OPENAI_API_KEY on the server and API connectivity.");
    } finally {
      setBusy(false);
    }
  }

  async function onDemo() {
    setError(null);
    setBusy(true);
    try {
      const [p1, p2, syl] = await Promise.all([
        fetch("/demo/paper1.txt").then((r) => r.text()),
        fetch("/demo/paper2.txt").then((r) => r.text()),
        fetch("/demo/syllabus.txt").then((r) => r.text()),
      ]);
      const combined = `${p1.trim()}\n\n---\n\n${p2.trim()}`;
      setPaperText(combined);
      setSyllabus(syl);
      setExtractStatus("success");
    } catch {
      setError("Could not load demo files.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Upload & analyze</h1>
        <p className="mt-1 text-slate-600">
          Upload a PDF or text past paper, paste your syllabus, then run analysis. Demo loads two sample papers as plain
          text (no OCR).
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <label className="inline-flex cursor-pointer items-center rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white shadow hover:bg-blue-600">
          <input
            type="file"
            accept=".pdf,.txt"
            className="hidden"
            disabled={busy}
            onChange={(e) => onFile(e.target.files?.[0] ?? null)}
          />
          Choose file
        </label>
        <button
          type="button"
          onClick={onDemo}
          disabled={busy}
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-800 shadow-sm hover:bg-slate-50 disabled:opacity-50"
        >
          Try Demo Data
        </button>
      </div>

      {extractStatus !== "idle" && (
        <p className="text-sm text-slate-600">
          Extraction:{" "}
          <span className={extractStatus === "success" ? "font-semibold text-emerald-700" : "font-semibold text-amber-700"}>
            {extractStatus}
          </span>
        </p>
      )}

      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">{error}</div>
      )}

      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-800">Past paper text (manual paste if extraction failed)</label>
        <textarea
          className="min-h-[220px] w-full rounded-lg border border-slate-300 p-3 text-sm shadow-sm focus:border-accent focus:outline-none focus:ring-2 focus:ring-blue-100"
          placeholder="Paste full paper text here..."
          value={paperText}
          onChange={(e) => setPaperText(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-800">Syllabus</label>
        <textarea
          className="min-h-[160px] w-full rounded-lg border border-slate-300 p-3 text-sm shadow-sm focus:border-accent focus:outline-none focus:ring-2 focus:ring-blue-100"
          placeholder="Paste syllabus topics..."
          value={syllabus}
          onChange={(e) => setSyllabus(e.target.value)}
        />
      </div>

      <button
        type="button"
        disabled={busy || !paperText.trim()}
        onClick={onAnalyze}
        className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {busy ? "Working..." : "Analyze"}
      </button>
    </div>
  );
}

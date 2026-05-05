from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.schemas.models import AnalyzeRequest, AnalyzeResponse, ExtractResponse, PlanRequest, PlanResponse
from app.services.aggregation import build_topic_stats
from app.services.ai_service import classify_questions, extract_questions, generate_plan_ai, generate_plan_rules, merge_plan
from app.services.extraction import extract_from_upload

app = FastAPI(title="AI Past Paper Analyzer", version="0.1.0")
FRONTEND_OUT_DIR = Path(__file__).resolve().parents[2] / "frontend" / "out"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/extract", response_model=ExtractResponse)
async def extract(file: UploadFile = File(...)):
    data = await file.read()
    text, status = extract_from_upload(file.filename, data)
    return ExtractResponse(text=text, status=status)


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(body: AnalyzeRequest):
    text = (body.text or "").strip()
    syllabus = (body.syllabus or "").strip()
    if not text:
        return AnalyzeResponse(questions=[], topics=[])
    originals = extract_questions(text)
    classified = classify_questions(originals, syllabus or "General")
    topics = build_topic_stats(classified, originals)
    return AnalyzeResponse(questions=classified, topics=topics)


@app.post("/plan", response_model=PlanResponse)
def plan(body: PlanRequest):
    if body.days < 1:
        raise HTTPException(status_code=400, detail="days must be >= 1")
    rules = generate_plan_rules(body.topics, body.days)
    ai = generate_plan_ai(body.topics, body.days)
    merged = merge_plan(ai, rules)
    return PlanResponse(plan=merged)


if FRONTEND_OUT_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_OUT_DIR, html=True), name="frontend")
else:
    @app.get("/")
    def frontend_not_built():
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Frontend build not found. Run `npm run build` in `frontend/` first.",
            },
        )

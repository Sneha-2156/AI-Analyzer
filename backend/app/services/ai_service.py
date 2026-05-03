from __future__ import annotations

import os
import re
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from app.schemas.models import ClassifiedQuestion, Question, StudyPlanDay, TopicStats
from app.schemas.validation import parse_json_strict

_client: OpenAI | None = None


def get_client() -> OpenAI | None:
    global _client
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    if _client is None:
        _client = OpenAI(api_key=key)
    return _client


def _model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _complete_json_object(system: str, user: str) -> str | None:
    client = get_client()
    if not client:
        return None
    try:
        resp = client.chat.completions.create(
            model=_model(),
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = (resp.choices[0].message.content or "").strip()
        parse_json_strict(content)
        return content
    except Exception:
        return None


def _chat_json(system: str, user: str, max_retries: int = 2) -> str | None:
    client = get_client()
    if not client:
        return None
    last_err: str | None = None
    for attempt in range(max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=_model(),
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            content = (resp.choices[0].message.content or "").strip()
            parse_json_strict(content)
            return content
        except Exception as e:
            last_err = str(e)
            hint = f"\nPrevious error: {last_err}. Return ONLY valid minified JSON."
            user = user + hint if attempt < max_retries else user
    return None


def fallback_split_questions(text: str) -> list[Question]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    chunks: list[str] = []
    numbered = re.compile(r"^(?:Q\.?\s*)?(\d+)[\).:\s]+(.+)$", re.I)
    buf: list[str] = []
    for ln in lines:
        m = numbered.match(ln)
        if m and buf:
            chunks.append(" ".join(buf))
            buf = [m.group(2)]
        elif m and not buf:
            buf.append(m.group(2))
        else:
            buf.append(ln)
    if buf:
        chunks.append(" ".join(buf))
    if len(chunks) <= 1 and "?" in text:
        chunks = [p.strip() for p in re.split(r"\?\s*", text) if p.strip()]
        chunks = [c + "?" if not c.endswith("?") else c for c in chunks]
    out: list[Question] = []
    for i, c in enumerate(chunks):
        if len(c) < 10:
            continue
        out.append(Question(id=f"q{i+1}", text=c[:8000], marks=None, year=_guess_year(c)))
    if not out and text.strip():
        out.append(Question(id="q1", text=text.strip()[:8000], marks=None, year=None))
    return out


def _guess_year(text: str) -> int | None:
    m = re.search(r"\b(20[0-2]\d)\b", text)
    if m:
        return int(m.group(1))
    return None


EXTRACT_SYSTEM = """You extract exam questions from raw past-paper text.
Return JSON: {"questions":[{"id":"string","text":"string","marks":null or integer,"year":null or integer}]}
Rules: id stable q1,q2,...; text is the full question; infer marks/year only if clearly stated."""


def _norm_question_item(item: dict[str, Any], index: int) -> dict[str, Any]:
    tid = str(item.get("id") or f"q{index + 1}")
    t = str(item.get("text") or "").strip()
    marks = item.get("marks")
    year = item.get("year")
    mi: int | None
    yi: int | None
    try:
        mi = int(marks) if marks is not None and str(marks).strip() != "" else None
    except (TypeError, ValueError):
        mi = None
    try:
        yi = int(year) if year is not None and str(year).strip() != "" else None
    except (TypeError, ValueError):
        yi = None
    return {"id": tid, "text": t, "marks": mi, "year": yi}


def extract_questions(text: str) -> list[Question]:
    base_user = f"Text:\n{text[:120000]}"
    user = base_user
    for attempt in range(3):
        raw = _complete_json_object(EXTRACT_SYSTEM, user)
        if not raw:
            break
        try:
            data = parse_json_strict(raw)
            arr = data.get("questions") if isinstance(data, dict) else None
            if not isinstance(arr, list):
                raise ValueError("missing questions array")
            out: list[Question] = []
            for i, item in enumerate(arr):
                if not isinstance(item, dict):
                    raise ValueError(f"question {i} not an object")
                norm = _norm_question_item(item, i)
                out.append(Question.model_validate(norm))
            out = [q for q in out if q.text]
            if out:
                return [q.model_copy(update={"text": q.text[:8000]}) for q in out]
        except (ValidationError, ValueError, TypeError) as e:
            user = base_user + f"\nSchema validation failed ({e}). Return ONLY valid JSON matching the schema."
            if attempt >= 2:
                break
            continue
    return fallback_split_questions(text)


CLASSIFY_SYSTEM = """You classify past-paper questions into syllabus topics.
Return JSON: {"items":[{"id":"string","topic":"string","type":"theory|numerical|conceptual|derivation|application|unknown","difficulty":"easy|medium|hard|unknown","marks":null or integer}]}
topic must be one of the syllabus headings or closest match. Preserve id from input."""


def classify_questions(questions: list[Question], syllabus: str) -> list[ClassifiedQuestion]:
    if not questions:
        return []
    payload = [{"id": q.id, "text": q.text[:2000], "marks": q.marks} for q in questions]
    import json

    user = f"Syllabus:\n{syllabus[:60000]}\n\nQuestions:\n{json.dumps(payload)[:100000]}"
    raw = _chat_json(CLASSIFY_SYSTEM, user)
    classified: list[ClassifiedQuestion] = []
    seen: set[str] = set()
    if raw:
        try:
            data = parse_json_strict(raw)
            arr = data.get("items") if isinstance(data, dict) else None
            if isinstance(arr, list):
                for item in arr:
                    if not isinstance(item, dict):
                        continue
                    tid = str(item.get("id") or "")
                    if not tid:
                        continue
                    cq = ClassifiedQuestion(
                        id=tid,
                        topic=str(item.get("topic") or "Unclassified"),
                        type=_coerce_type(item.get("type")),
                        difficulty=_coerce_difficulty(item.get("difficulty")),
                        marks=_coerce_marks(item.get("marks")),
                    )
                    classified.append(cq)
                    seen.add(tid)
        except Exception:
            pass
    for q in questions:
        if q.id in seen:
            continue
        classified.append(
            ClassifiedQuestion(
                id=q.id,
                topic="Unclassified",
                type="unknown",
                difficulty="unknown",
                marks=q.marks,
            )
        )
    id_to_q = {q.id: q for q in questions}
    merged: list[ClassifiedQuestion] = []
    for c in classified:
        o = id_to_q.get(c.id)
        if o and c.marks is None and o.marks is not None:
            merged.append(c.model_copy(update={"marks": o.marks}))
        else:
            merged.append(c)
    return merged


def _coerce_type(v: Any) -> Any:
    allowed = {"theory", "numerical", "conceptual", "derivation", "application", "unknown"}
    s = str(v or "unknown").lower()
    return s if s in allowed else "unknown"


def _coerce_difficulty(v: Any) -> Any:
    allowed = {"easy", "medium", "hard", "unknown"}
    s = str(v or "unknown").lower()
    return s if s in allowed else "unknown"


def _coerce_marks(v: Any) -> int | None:
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


PLAN_SYSTEM = """You build a concise study plan from high-yield topics.
Return JSON: {"plan":[{"day":1,"topics":["..."],"hours":2.5,"focus":"string"}]}
days must match requested count sequentially."""


def generate_plan_ai(topics: list[TopicStats], days: int) -> list[StudyPlanDay] | None:
    import json

    brief = [
        {
            "topic": t.topic,
            "frequency": t.frequency,
            "total_marks": t.total_marks,
            "trend": t.trend,
            "score": t.score,
        }
        for t in topics[:40]
    ]
    user = json.dumps({"days": days, "topics": brief})
    raw = _chat_json(PLAN_SYSTEM, user)
    if not raw:
        return None
    try:
        data = parse_json_strict(raw)
        arr = data.get("plan") if isinstance(data, dict) else None
        if not isinstance(arr, list):
            return None
        out: list[StudyPlanDay] = []
        for item in arr:
            if not isinstance(item, dict):
                continue
            out.append(
                StudyPlanDay(
                    day=int(item.get("day") or 0),
                    topics=list(item.get("topics") or []),
                    hours=float(item.get("hours") or 2),
                    focus=str(item.get("focus") or ""),
                )
            )
        if len(out) == days:
            return out
    except Exception:
        return None
    return None


def generate_plan_rules(topics: list[TopicStats], days: int) -> list[StudyPlanDay]:
    """Code rules: max 3 topics/day, rotate difficulty implied by score, balance high/low score."""
    if days < 1:
        return []
    sorted_topics = sorted(topics, key=lambda t: t.score, reverse=True)
    names = [t.topic for t in sorted_topics]
    if not names:
        return [
            StudyPlanDay(day=d + 1, topics=[], hours=2.0, focus="Review syllabus") for d in range(days)
        ]
    low = list(reversed(names))
    plan: list[StudyPlanDay] = []
    hi, lo = 0, 0
    for d in range(days):
        day_topics: list[str] = []
        picks = 0
        while picks < 3 and (hi < len(names) or lo < len(low)):
            if d % 2 == 0:
                if hi < len(names):
                    t = names[hi]
                    hi += 1
                elif lo < len(low):
                    t = low[lo]
                    lo += 1
                else:
                    break
            else:
                if lo < len(low):
                    t = low[lo]
                    lo += 1
                elif hi < len(names):
                    t = names[hi]
                    hi += 1
                else:
                    break
            if t not in day_topics:
                day_topics.append(t)
                picks += 1
        hours = round(1.5 + 0.5 * min(3, len(day_topics)), 1)
        focus = f"Priority mix: {', '.join(day_topics[:2]) or 'light review'}"
        plan.append(StudyPlanDay(day=d + 1, topics=day_topics, hours=hours, focus=focus))
    return plan


def merge_plan(ai_plan: list[StudyPlanDay] | None, rules_plan: list[StudyPlanDay]) -> list[StudyPlanDay]:
    if ai_plan and len(ai_plan) == len(rules_plan):
        merged: list[StudyPlanDay] = []
        for a, r in zip(ai_plan, rules_plan):
            topics = a.topics if len(a.topics) <= 3 and a.topics else r.topics
            if len(topics) > 3:
                topics = topics[:3]
            hours = max(1.0, min(6.0, a.hours))
            focus = a.focus or r.focus
            merged.append(StudyPlanDay(day=r.day, topics=topics, hours=hours, focus=focus))
        return merged
    return rules_plan

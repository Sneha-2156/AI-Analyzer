from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Question(BaseModel):
    id: str
    text: str
    marks: int | None = None
    year: int | None = None


class ClassifiedQuestion(BaseModel):
    id: str
    topic: str
    type: Literal["theory", "numerical", "conceptual", "derivation", "application", "unknown"] = "unknown"
    difficulty: Literal["easy", "medium", "hard", "unknown"] = "unknown"
    marks: int | None = None


class TopicStats(BaseModel):
    topic: str
    frequency: int
    total_marks: int
    trend: Literal["increasing", "decreasing", "stable"]
    score: float = Field(ge=0, le=100)


class StudyPlanDay(BaseModel):
    day: int
    topics: list[str]
    hours: float
    focus: str


class ExtractResponse(BaseModel):
    text: str
    status: Literal["success", "failed"]


class AnalyzeRequest(BaseModel):
    text: str
    syllabus: str


class AnalyzeResponse(BaseModel):
    questions: list[ClassifiedQuestion]
    topics: list[TopicStats]


class PlanRequest(BaseModel):
    topics: list[TopicStats]
    days: int = Field(ge=1, le=365)


class PlanResponse(BaseModel):
    plan: list[StudyPlanDay]

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.models import ClassifiedQuestion, Question

SAMPLE = Path(__file__).resolve().parents[1] / "sample_data"


def test_health():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_extract_and_analyze_with_sample(monkeypatch):
    import app.main as main_mod

    def fake_extract(text: str):
        return [
            Question(id="q1", text="Define Big-O.", marks=5, year=2022),
            Question(id="q2", text="Explain TCP.", marks=8, year=2023),
        ]

    def fake_classify(questions, syllabus):
        return [
            ClassifiedQuestion(
                id="q1",
                topic="Algorithms & Complexity",
                type="conceptual",
                difficulty="easy",
                marks=5,
            ),
            ClassifiedQuestion(
                id="q2",
                topic="Networking",
                type="theory",
                difficulty="medium",
                marks=8,
            ),
        ]

    monkeypatch.setattr(main_mod, "extract_questions", fake_extract)
    monkeypatch.setattr(main_mod, "classify_questions", fake_classify)

    c = TestClient(app)
    paper = (SAMPLE / "paper1.txt").read_text(encoding="utf-8")
    syllabus = (SAMPLE / "syllabus.txt").read_text(encoding="utf-8")
    r = c.post("/analyze", json={"text": paper, "syllabus": syllabus})
    assert r.status_code == 200
    data = r.json()
    assert len(data["questions"]) == 2
    assert len(data["topics"]) >= 1


def test_plan_rules():
    from app.schemas.models import TopicStats

    c = TestClient(app)
    topics = [
        TopicStats(topic="A", frequency=3, total_marks=10, trend="stable", score=80),
        TopicStats(topic="B", frequency=2, total_marks=6, trend="increasing", score=60),
    ]
    r = c.post("/plan", json={"topics": [t.model_dump() for t in topics], "days": 3})
    assert r.status_code == 200
    plan = r.json()["plan"]
    assert len(plan) == 3
    for day in plan:
        assert len(day["topics"]) <= 3
        assert day["hours"] >= 1

from app.schemas.models import ClassifiedQuestion, Question
from app.services.ai_service import fallback_split_questions
from app.services.aggregation import build_topic_stats


def test_fallback_split_numbered():
    text = """1. What is O(n)? (5 marks)
2. Explain TCP. (3 marks)"""
    qs = fallback_split_questions(text)
    assert len(qs) >= 2
    assert all(q.text for q in qs)


def test_aggregation_normalizes_scores():
    originals = [
        Question(id="1", text="a", marks=5, year=2022),
        Question(id="2", text="b", marks=10, year=2023),
    ]
    classified = [
        ClassifiedQuestion(id="1", topic="Algo", type="theory", difficulty="easy", marks=5),
        ClassifiedQuestion(id="2", topic="Algo", type="numerical", difficulty="hard", marks=10),
    ]
    stats = build_topic_stats(classified, originals)
    assert len(stats) == 1
    assert stats[0].frequency == 2
    assert stats[0].total_marks == 15
    assert 0 <= stats[0].score <= 100

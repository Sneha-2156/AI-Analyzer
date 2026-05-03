from __future__ import annotations

from collections import defaultdict

from app.schemas.models import ClassifiedQuestion, Question, TopicStats

TREND_WEIGHT = {"increasing": 3, "stable": 2, "decreasing": 1}
DIFF_WEIGHT = {"hard": 3, "medium": 2, "easy": 1, "unknown": 2}


def _difficulty_weight_for_topic(weights: list[int]) -> float:
    if not weights:
        return float(DIFF_WEIGHT["unknown"])
    return sum(weights) / len(weights)


def _trend_for_topic(years_counts: dict[int, int], years_marks: dict[int, int]) -> str:
    years = sorted(years_counts.keys())
    if len(years) < 2:
        return "stable"
    early_y, late_y = years[0], years[-1]
    early = years_counts.get(early_y, 0) + years_marks.get(early_y, 0) * 0.1
    late = years_counts.get(late_y, 0) + years_marks.get(late_y, 0) * 0.1
    if late > early * 1.05:
        return "increasing"
    if late < early * 0.95:
        return "decreasing"
    return "stable"


def build_topic_stats(
    classified: list[ClassifiedQuestion],
    originals: list[Question],
) -> list[TopicStats]:
    id_to_year = {q.id: q.year for q in originals}
    by_topic: dict[str, list[ClassifiedQuestion]] = defaultdict(list)
    for cq in classified:
        by_topic[cq.topic].append(cq)

    raw_rows: list[tuple[str, float, int, int, str, float]] = []
    for topic, items in by_topic.items():
        freq = len(items)
        total_marks = sum((m or 0) for m in (x.marks for x in items))
        years_counts: dict[int, int] = defaultdict(int)
        years_marks: dict[int, int] = defaultdict(int)
        diff_weights: list[int] = []
        for x in items:
            w = DIFF_WEIGHT.get(x.difficulty, DIFF_WEIGHT["unknown"])
            diff_weights.append(w)
            y = id_to_year.get(x.id)
            if y is not None:
                years_counts[y] += 1
                years_marks[y] += x.marks or 0
        trend = _trend_for_topic(dict(years_counts), dict(years_marks))
        tw = TREND_WEIGHT[trend]
        dw = _difficulty_weight_for_topic(diff_weights)
        raw = freq * 0.4 + total_marks * 0.3 + tw * 0.2 + dw * 0.1
        raw_rows.append((topic, raw, freq, total_marks, trend, dw))

    if not raw_rows:
        return []

    scores_only = [r[1] for r in raw_rows]
    lo, hi = min(scores_only), max(scores_only)

    def norm(raw: float) -> float:
        if hi == lo:
            return 100.0
        return round((raw - lo) / (hi - lo) * 100, 2)

    stats: list[TopicStats] = []
    for topic, raw, freq, total_marks, trend, _ in raw_rows:
        stats.append(
            TopicStats(
                topic=topic,
                frequency=freq,
                total_marks=total_marks,
                trend=trend,  # type: ignore[arg-type]
                score=norm(raw),
            )
        )
    stats.sort(key=lambda s: s.score, reverse=True)
    return stats

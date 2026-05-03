from app.schemas.validation import parse_json_strict, strip_non_json_prefix_suffix


def test_strip_non_json():
    raw = 'Here you go:\n{"a":1}\nthanks'
    assert parse_json_strict(raw) == {"a": 1}
    assert strip_non_json_prefix_suffix("```json\n[1]\n```").strip().startswith("[")

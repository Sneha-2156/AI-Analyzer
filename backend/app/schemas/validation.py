from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def strip_non_json_prefix_suffix(raw: str) -> str:
    s = raw.strip()
    if not s:
        return s
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        return s[start : end + 1]
    start = s.find("[")
    end = s.rfind("]")
    if start != -1 and end != -1 and end > start:
        return s[start : end + 1]
    return s


def parse_json_strict(raw: str) -> Any:
    cleaned = strip_non_json_prefix_suffix(raw)
    return json.loads(cleaned)


def validate_model(data: Any, model: type[T]) -> T:
    return model.model_validate(data)


def safe_validate_list(raw: str, item_model: type[BaseModel], root_key: str | None) -> list[Any] | None:
    try:
        data = parse_json_strict(raw)
        if root_key and isinstance(data, dict) and root_key in data:
            data = data[root_key]
        if not isinstance(data, list):
            return None
        return [item_model.model_validate(x) for x in data]
    except (json.JSONDecodeError, ValidationError, TypeError, ValueError):
        return None

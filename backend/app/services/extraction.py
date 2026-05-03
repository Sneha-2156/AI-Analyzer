from __future__ import annotations

import io
from pathlib import Path
from typing import Literal

from pypdf import PdfReader


def extract_text_from_pdf_bytes(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        if t.strip():
            parts.append(t)
    return "\n\n".join(parts).strip()


def extract_text_with_ocr_if_needed(data: bytes) -> str:
    text = extract_text_from_pdf_bytes(data)
    if len(text) >= 200:
        return text
    try:
        import pytesseract  # type: ignore
        from pdf2image import convert_from_bytes  # type: ignore
    except ImportError:
        return text
    try:
        images = convert_from_bytes(data)
        ocr_parts: list[str] = []
        for img in images:
            ocr_parts.append(pytesseract.image_to_string(img))
        ocr = "\n\n".join(ocr_parts).strip()
        if len(ocr) > len(text):
            return ocr
    except Exception:
        pass
    return text


def extract_from_upload(filename: str | None, data: bytes) -> tuple[str, Literal["success", "failed"]]:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        text = extract_text_with_ocr_if_needed(data)
    else:
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            text = ""
    status = "success" if len(text) >= 200 else "failed"
    return text, status


def extract_from_path(path: Path) -> tuple[str, Literal["success", "failed"]]:
    suffix = path.suffix.lower()
    data = path.read_bytes()
    if suffix == ".pdf":
        text = extract_text_with_ocr_if_needed(data)
    else:
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            text = ""
    status = "success" if len(text) >= 200 else "failed"
    return text, status

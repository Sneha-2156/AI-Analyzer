from app.services.extraction import extract_from_upload


def test_extract_short_text_fails():
    text, status = extract_from_upload("x.txt", b"hi")
    assert status == "failed"
    assert len(text) < 200


def test_extract_long_text_success():
    body = b"word " * 50
    text, status = extract_from_upload("notes.txt", body)
    assert status == "success"
    assert len(text) >= 200

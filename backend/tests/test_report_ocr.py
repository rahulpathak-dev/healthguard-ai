from app.reports.ocr import extract_text_from_bytes, extract_values


def test_text_ocr_extracts_values_units_and_report_reference_ranges() -> None:
    text, confidence = extract_text_from_bytes(
        b"Hemoglobin 10.2 g/dL 12.0-16.0\nGlucose 99 mg/dL 70-110",
        "text/plain",
    )
    values = extract_values(text, confidence)
    assert values[0].label == "Hemoglobin"
    assert values[0].unit == "g/dL"
    assert values[0].reference_range == "12.0-16.0"
    assert values[0].flag == "low"
    assert values[1].flag == "normal"


def test_unsupported_file_type_does_not_invent_ocr_text() -> None:
    text, confidence = extract_text_from_bytes(b"%PDF-1.7", "application/pdf")
    assert text == ""
    assert confidence == 0.0


def test_unreadable_values_are_not_invented() -> None:
    values = extract_values("Hemoglobin unreadable g/dL range unclear", 0.5)
    assert values == []

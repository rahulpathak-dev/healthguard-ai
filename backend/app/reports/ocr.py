import re
from typing import Literal

from app.reports.schemas import ExtractedValue

VALUE_PATTERN = re.compile(
    r"(?P<label>[A-Za-z][A-Za-z /()-]{1,60})\s+"
    r"(?P<value>-?\d+(?:\.\d+)?)\s*"
    r"(?P<unit>[A-Za-z/%]+)?\s+"
    r"(?P<low>-?\d+(?:\.\d+)?)\s*[-\u2013]\s*(?P<high>-?\d+(?:\.\d+)?)"
)


def extract_text_from_bytes(data: bytes, mime_type: str) -> tuple[str, float]:
    if mime_type == "text/plain":
        text = data.decode("utf-8", errors="replace")
        replacement_rate = text.count("\ufffd") / max(len(text), 1)
        return text, round(max(0.4, 0.98 - replacement_rate), 3)
    return "", 0.0


def extract_values(text: str, base_confidence: float) -> list[ExtractedValue]:
    values: list[ExtractedValue] = []
    for match in VALUE_PATTERN.finditer(text):
        label = " ".join(match.group("label").split())[:80]
        value = match.group("value")
        unit = match.group("unit")
        low = float(match.group("low"))
        high = float(match.group("high"))
        numeric = float(value)
        flag: Literal["low", "normal", "high", "unknown"]
        if numeric < low:
            flag = "low"
        elif numeric > high:
            flag = "high"
        else:
            flag = "normal"
        values.append(
            ExtractedValue(
                label=label,
                value=value,
                unit=unit,
                reference_range=f"{match.group('low')}-{match.group('high')}",
                flag=flag,
                confidence=base_confidence,
                note="Reference range was read from the report text.",
            )
        )
    return values[:80]

"""Pure normalizers for user-provided and source-provided values."""

import re
import unicodedata
from datetime import date, datetime
from typing import Optional

ROLE_MAPPING = {
    "portiere": "P",
    "goalkeeper": "P",
    "difensore centrale": "D",
    "centre-back": "D",
    "left-back": "D",
    "right-back": "D",
    "terzino": "D",
    "defensive midfield": "C",
    "centrocampista difensivo": "C",
    "central midfield": "C",
    "centrocampista centrale": "C",
    "attacking midfield": "C",
    "trequartista": "C",
    "left winger": "A",
    "right winger": "A",
    "ala sinistra": "A",
    "ala destra": "A",
    "seconda punta": "A",
    "centre-forward": "A",
    "punta centrale": "A",
    "attaccante": "A",
}


def clean_text(value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip().replace("’", "'")
    if not text or text.lower() in {"nan", "none", "null", "n/a", "-"}:
        return None
    return re.sub(r"\s+", " ", text)


def normalize_name(value: object) -> str:
    text = clean_text(value) or ""
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    normalized = without_accents.lower().replace("’", "'")
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()


def parse_date(value: object) -> Optional[date]:
    text = clean_text(value)
    if text is None:
        return None
    for pattern in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    raise ValueError(f"Data non valida: {text}")


def calculate_age(birth_date: Optional[date], reference_date: date) -> Optional[int]:
    """Derive age at an explicit reference date; age is never persisted as source data."""
    if birth_date is None:
        return None
    years = reference_date.year - birth_date.year
    return years - int(
        (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day)
    )


def parse_decimal(value: object) -> Optional[float]:
    text = clean_text(value)
    if text is None:
        return None
    try:
        return float(text.replace(".", "").replace(",", ".")) if "," in text else float(text)
    except ValueError as exc:
        raise ValueError(f"Numero non valido: {text}") from exc


def parse_probability(value: object) -> Optional[float]:
    parsed = parse_decimal(value)
    if parsed is None:
        return None
    probability = parsed / 100 if parsed > 1 else parsed
    if not 0 <= probability <= 1:
        raise ValueError(f"Probabilità fuori intervallo: {value}")
    return probability


def parse_bool(value: object) -> bool:
    text = (clean_text(value) or "").lower()
    return text in {"1", "true", "yes", "si", "sì", "y"}


def infer_fantasy_role(source_role: object, official_role: object = None) -> str:
    selected = clean_text(official_role) or clean_text(source_role)
    if selected in {"P", "D", "C", "A"}:
        return selected
    key = (selected or "").lower()
    if key in ROLE_MAPPING:
        return ROLE_MAPPING[key]
    raise ValueError(f"Ruolo non mappabile: {selected or 'mancante'}")


def parse_market_value(value: object) -> Optional[int]:
    """Parse common Italian Transfermarkt values while preserving raw input upstream."""
    text = (clean_text(value) or "").lower().replace("€", "").strip()
    if not text or "free transfer" in text or "svincolato" in text:
        return None
    match = re.search(r"([\d.,]+)\s*(mln|mila|k)?", text)
    if not match:
        raise ValueError(f"Valore di mercato non valido: {value}")
    number = match.group(1)
    if "," in number:
        amount = float(number.replace(".", "").replace(",", "."))
    else:
        amount = float(number)
    multiplier = {"mln": 1_000_000, "mila": 1_000, "k": 1_000}.get(match.group(2), 1)
    return round(amount * multiplier)

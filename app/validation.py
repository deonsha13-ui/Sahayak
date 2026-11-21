"""Clinical validation envelopes for the five mandatory visit fields.

Deterministic only - no LLM, no diagnosis, no dosage advice. The weight
envelopes follow plausible anthropometric bounds from IMNCI / NHM ASHA
training material (a newborn is never 52 kg, an adult ASHA beneficiary is
never 2.8 kg). Out-of-envelope values are rejected and the caller asks again.

Every public function is pure so tests can pin "today".
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

VISIT_TYPES = ("ANC", "PNC", "newborn", "immunisation")

# Spoken / misspelled forms -> canonical visit type.
_VISIT_ALIASES = {
    "anc": "ANC",
    "a n c": "ANC",
    "antenatal": "ANC",
    "ante natal": "ANC",
    "prenatal": "ANC",
    "pre natal": "ANC",
    "pregnancy": "ANC",
    "pregnant": "ANC",
    "garbhvati": "ANC",
    "garbhwati": "ANC",
    "pnc": "PNC",
    "p n c": "PNC",
    "postnatal": "PNC",
    "post natal": "PNC",
    "postpartum": "PNC",
    "delivery": "PNC",
    "newborn": "newborn",
    "new born": "newborn",
    "neonate": "newborn",
    "neonatal": "newborn",
    "baby": "newborn",
    "bachcha": "newborn",
    "bacha": "newborn",
    "naya bachcha": "newborn",
    "immunisation": "immunisation",
    "immunization": "immunisation",
    "vaccination": "immunisation",
    "vaccine": "immunisation",
    "tika": "immunisation",
    "teeka": "immunisation",
    "tikakaran": "immunisation",
}

# (min, max) kilograms. The wide "default" envelope applies before the visit
# type is known.
WEIGHT_RANGES = {
    "newborn": (0.5, 6.0),
    "immunisation": (1.5, 40.0),
    "ANC": (30.0, 150.0),
    "PNC": (30.0, 150.0),
}
DEFAULT_WEIGHT_RANGE = (0.5, 150.0)
MAX_PLAUSIBLE_WEIGHT = 150.0

# National Immunization Schedule names -> canonical short names.
_VACCINE_ALIASES = {
    "tt": "TT",
    "t.t": "TT",
    "tt injection": "TT",
    "tetanus": "TT",
    "tetanus toxoid": "TT",
    "bcg": "BCG",
    "opv": "OPV",
    "opv0": "OPV-0",
    "opv 0": "OPV-0",
    "opv1": "OPV-1",
    "opv2": "OPV-2",
    "opv3": "OPV-3",
    "ipv": "IPV",
    "pentavalent": "Pentavalent",
    "penta": "Pentavalent",
    "hepatitis b": "Hepatitis B",
    "hep b": "Hepatitis B",
    "hepb": "Hepatitis B",
    "rotavirus": "Rotavirus",
    "rotavirus vaccine": "Rotavirus",
    "pcv": "PCV",
    "mr": "MR",
    "measles": "MR",
    "measles rubella": "MR",
    "rubella": "MR",
    "dpt": "DPT",
    "dpv": "DPV",
    "je": "JE",
    "vitamin a": "Vitamin A",
    "ifa": "IFA",
    "ifa tablets": "IFA",
    "iron": "IFA",
}

NONE_WORDS = {
    "none",
    "no",
    "nothing",
    "nahi",
    "nahin",
    "nhi",
    "nil",
    "koi nahi",
    "koi nahin",
    "कुछ नहीं",
    "कोई नहीं",
    "नहीं",
    "இல்லை",
    "எதுவும் இல்லை",
    "ఏమీ లేదు",
    "లేదు",
    "ಯಾವುದೂ ಇಲ್ಲ",
    "ಇಲ್ಲ",
    "ഒന്നുമില്ല",
    "ഇല്ല",
    "কিছু নেই",
    "না",
    "काहीही नाही",
    "नाही",
}

_ID_RE = re.compile(r"^[\w][\w\-/_.]{1,63}$", re.UNICODE)

_NUMBER_WORDS = {
    "ek": 1,
    "one": 1,
    "do": 2,
    "two": 2,
    "teen": 3,
    "three": 3,
    "char": 4,
    "chaar": 4,
    "four": 4,
    "paanch": 5,
    "panch": 5,
    "five": 5,
    "chhah": 6,
    "che": 6,
    "six": 6,
    "saat": 7,
    "seven": 7,
    "aath": 8,
    "eight": 8,
    "nau": 9,
    "nine": 9,
}

_DATE_FORMATS = (
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%Y/%m/%d",
    "%d.%m.%Y",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d %Y",
    "%B %d %Y",
)


def normalize_visit_type(value):
    """Return one of VISIT_TYPES, or None when it cannot be resolved."""
    if not value:
        return None
    if isinstance(value, str):
        raw = value.strip()
        if raw in VISIT_TYPES:
            return raw
        key = re.sub(r"[\s_\-]+", " ", raw.lower()).strip()
        if key in _VISIT_ALIASES:
            return _VISIT_ALIASES[key]
        for alias, canonical in _VISIT_ALIASES.items():
            if key.startswith(alias) or alias in key.split():
                return canonical
    return None


def coerce_weight(value):
    """Turn '2.8' / 'do point aath' / 52 into a float kg, else None."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None

    text = value.strip().lower().replace(",", ".")
    text = text.replace("kilos", "").replace("kilo", "").replace("kg", "").strip()
    if not text:
        return None

    # "do point aath" / "2 point 8" -> 2.8
    point_match = re.search(
        r"(\d+|[a-z]+)\s*(?:point|dot|dashamlav)\s*(\d+|[a-z]+)", text
    )
    if point_match:
        whole, frac = point_match.group(1), point_match.group(2)
        whole_n = int(whole) if whole.isdigit() else _NUMBER_WORDS.get(whole)
        frac_n = int(frac) if frac.isdigit() else _NUMBER_WORDS.get(frac)
        if whole_n is not None and frac_n is not None:
            return float(f"{whole_n}.{frac_n}")

    match = re.search(r"\d+(?:\.\d+)?", text)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None

    for word, number in _NUMBER_WORDS.items():
        if re.search(rf"(?<!\w){re.escape(word)}(?!\w)", text):
            return float(number)
    return None


def weight_envelope(visit_type):
    return WEIGHT_RANGES.get(visit_type, DEFAULT_WEIGHT_RANGE)


def check_weight(weight, visit_type):
    """Return the kg as a float when inside the envelope, else None."""
    kg = coerce_weight(weight)
    if kg is None:
        return None
    low, high = weight_envelope(visit_type)
    if low <= kg <= min(high, MAX_PLAUSIBLE_WEIGHT):
        return round(kg, 2)
    return None


def normalize_vaccinations(value):
    """Canonicalise a list of spoken vaccine names, dropping 'none' noise."""
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = re.split(r"[,;/]|\band\b|\baur\b", value)
    elif isinstance(value, (list, tuple)):
        raw_items = []
        for item in value:
            raw_items.extend(re.split(r"[,;/]|\band\b|\baur\b", str(item)))
    else:
        return []

    out = []
    for item in raw_items:
        item = item.strip().strip(".").lower()
        if not item:
            continue
        if item in NONE_WORDS:
            continue
        canonical = _VACCINE_ALIASES.get(item)
        if canonical is None:
            canonical = _VACCINE_ALIASES.get(re.sub(r"[\s_\-]+", " ", item))
        if canonical is None:
            canonical = item.upper() if len(item) <= 4 else item.title()
        if canonical not in out:
            out.append(canonical)
    return out


def normalize_beneficiary_id(value):
    if value is None:
        return None
    text = str(value).strip().strip(",.")
    text = re.sub(r"\s+", "", text)
    if not text:
        return None
    return text if _ID_RE.match(text) else None


def parse_date(value, today=None):
    """Resolve a spoken/written date to an ISO date string.

    Relative expressions ('kal', 'agle hafte', 'do hafte baad', 'next week')
    and common numeric formats are supported. Returns None when unresolved.
    """
    if not value:
        return None
    today = today or date.today()

    if isinstance(value, (date, datetime)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()

    text = str(value).strip().lower()
    if not text:
        return None

    text = text.replace("ko", "").replace("tak", "").strip()

    relative = {
        "aaj": 0,
        "today": 0,
        "kal": 1,
        "tomorrow": 1,
        "parso": 2,
        "parson": 2,
        "day after tomorrow": 2,
        "agle hafte": 7,
        "agle hafta": 7,
        "next week": 7,
        "agle mahine": 30,
        "agle mahina": 30,
        "next month": 30,
        "do hafte": 14,
        "do hafte baad": 14,
        "teen hafte": 21,
        "ek mahina": 30,
    }
    for phrase, days in relative.items():
        if text == phrase or text.startswith(phrase + " ") or text.endswith(" " + phrase):
            return (today + timedelta(days=days)).isoformat()

    week_match = re.search(r"(\d+|[a-z]+)\s+(?:hafte|hafta|week|weeks)", text)
    if week_match:
        token = week_match.group(1)
        count = int(token) if token.isdigit() else _NUMBER_WORDS.get(token)
        if count is not None:
            return (today + timedelta(weeks=count)).isoformat()

    day_match = re.search(r"(\d+|[a-z]+)\s+(?:din|day|days)", text)
    if day_match:
        token = day_match.group(1)
        count = int(token) if token.isdigit() else _NUMBER_WORDS.get(token)
        if count is not None:
            return (today + timedelta(days=count)).isoformat()

    # Values that are already ISO-ish may be truncated during extraction.
    iso_match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if iso_match:
        year, month, day = (int(g) for g in iso_match.groups())
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return None

    numeric_match = re.search(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})", text)
    if numeric_match:
        day, month, year = (int(g) for g in numeric_match.groups())
        if year < 100:
            year += 2000
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return None

    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def check_next_visit_date(value, today=None):
    """Return a strictly-future ISO date, else None."""
    today = today or date.today()
    iso = parse_date(value, today=today)
    if not iso:
        return None
    try:
        parsed = date.fromisoformat(iso)
    except ValueError:
        return None
    return iso if parsed > today else None


def validate_record(record, today=None):
    """Clean a record against the clinical envelopes.

    Returns ``(cleaned, problems)`` where ``problems`` maps a field name to a
    dict ``{"code": <i18n key>, **fmt_args}``. Fields with a problem are
    cleared so the dialogue loop asks for them again.
    """
    today = today or date.today()
    record = dict(record or {})
    cleaned = {
        "beneficiary_id": None,
        "visit_type": None,
        "weight_kg": None,
        "vaccinations_due": [],
        "next_visit_date": None,
        "danger_signs": list(record.get("danger_signs") or []),
    }
    problems = {}

    visit_type = normalize_visit_type(record.get("visit_type"))
    cleaned["visit_type"] = visit_type
    if record.get("visit_type") and not visit_type:
        problems["visit_type"] = {"code": "fix_visit"}

    beneficiary_id = normalize_beneficiary_id(record.get("beneficiary_id"))
    cleaned["beneficiary_id"] = beneficiary_id
    if record.get("beneficiary_id") and not beneficiary_id:
        problems["beneficiary_id"] = {"code": "fix_id"}

    if record.get("weight_kg") is not None:
        kg = check_weight(record.get("weight_kg"), visit_type)
        cleaned["weight_kg"] = kg
        if kg is None:
            problems["weight_kg"] = {
                "code": "fix_weight",
                "value": record.get("weight_kg"),
                "visit": (visit_type or "").lower() or "this",
            }

    cleaned["vaccinations_due"] = normalize_vaccinations(record.get("vaccinations_due"))

    if record.get("next_visit_date"):
        iso = check_next_visit_date(record.get("next_visit_date"), today=today)
        cleaned["next_visit_date"] = iso
        if iso is None:
            problems["next_visit_date"] = {"code": "fix_date"}

    return cleaned, problems

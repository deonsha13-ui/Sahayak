import re

# STARTER LIST ONLY. Before the demo, check every sign against a public
# guideline (e.g. the government ASHA training modules / MCP card danger
# signs) and cite it in your README. Add more phrases in the languages
# you support.
DANGER_SIGNS = [
    {
        "id": "bleeding_pregnancy",
        "label": "Bleeding in pregnancy",
        "context": "pregnancy",
        "phrases": ["bleeding", "blood loss", "khoon", "khun", "ब्लीडिंग", "खून", "இரத்தப்போக்கு", "ரத்தப்போக்கு"],
    },
    {
        "id": "fever_newborn",
        "label": "High fever in newborn",
        "context": "newborn",
        "phrases": ["fever", "bukhar", "bukhaar", "tez bukhar", "बुखार", "காய்ச்சல்"],
    },
    {
        "id": "convulsions",
        "label": "Convulsions / fits",
        "context": None,
        "phrases": ["convulsion", "fits", "jhatke", "daura", "seizure", "दौरा", "झटके", "வலிப்பு"],
    },
    {
        "id": "not_breathing_well",
        "label": "Difficulty breathing",
        "context": None,
        "phrases": ["breathing problem", "breathless", "saans", "सांस", "மூச்சு"],
    },
]

NEGATION_RE = re.compile(
    r"(?<!\w)(no|not|nahi|nahin|nhi|illai|without|नहीं|नही|இல்லை)(?!\w)"
)
CLAUSE_BREAK_RE = re.compile(r"[,.;!?]| aur | and | lekin | but | par | magar ")


def _negated(text: str, start: int, end: int) -> bool:
    """True if a negation sits in the same clause, before or after the phrase."""
    before = text[max(0, start - 25):start]
    before = CLAUSE_BREAK_RE.split(before)[-1]
    after = text[end:end + 25]
    after = CLAUSE_BREAK_RE.split(after)[0]
    return bool(NEGATION_RE.search(before) or NEGATION_RE.search(after))


def check_danger_signs(transcript: str, visit_type: str | None = None) -> list[dict]:
    """Return a list of hits: [{id, label, quote}]. Deterministic, no LLM."""
    text = transcript.lower()
    hits = []
    for sign in DANGER_SIGNS:
        ctx = sign["context"]
        if ctx == "newborn" and visit_type != "newborn":
            continue
        if ctx == "pregnancy" and visit_type not in ("ANC", None):
            continue
        found = False
        for phrase in sign["phrases"]:
            for m in re.finditer(re.escape(phrase.lower()), text):
                if _negated(text, m.start(), m.end()):
                    continue
                hits.append({"id": sign["id"], "label": sign["label"], "quote": phrase})
                found = True
                break
            if found:
                break
    return hits
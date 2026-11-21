"""Conversational dialogue policy for a single home visit.

The session behaves like an assistant rather than a form reader:

1. It identifies the language the worker is speaking and switches to it.
2. It acknowledges what it just heard ("Got it: weight 52 kilos.").
3. It asks only for the next missing field, conversationally.
4. Danger signs are checked first (rules only, never an LLM, never skipped).
5. ``validation`` cleans the record against the clinical envelopes; anything
   rejected is cleared and the worker is asked again with the reason.
6. When the record is complete it reads it back and asks whether to save.

The session holds pure state - persistence happens in the transport layer.
"""

from __future__ import annotations

import re

from app import i18n, lang_detect, storage, validation
from app.danger_signs import check_danger_signs
from app.extractor import EMPTY_RECORD, extract

ORDER = ["beneficiary_id", "visit_type", "weight_kg", "vaccinations_due", "next_visit_date"]
QUESTION_KEYS = {
    "beneficiary_id": "q_beneficiary_id",
    "visit_type": "q_visit_type",
    "weight_kg": "q_weight",
    "vaccinations_due": "q_vaccinations",
    "next_visit_date": "q_next_visit",
}
# How each field reads back inside an acknowledgement or the readback.
FIELD_LABELS = {
    "beneficiary_id": "rb_id",
    "visit_type": "rb_visit",
    "weight_kg": "rb_weight",
    "vaccinations_due": "rb_vacc",
    "next_visit_date": "rb_date",
}

# Latin plus Devanagari, Bengali, Tamil, Telugu, Kannada and Malayalam blocks.
_TOKEN_RE = re.compile(r"[\w\u0900-\u0D7F]+", re.UNICODE)


class Session:
    def __init__(self, language: str = "en", auto_language: bool = True):
        self.language = i18n.normalize_lang(language)
        self.auto_language = auto_language
        self.record = dict(EMPTY_RECORD)
        self.state = "collecting"      # collecting -> readback -> saved
        self.asked_vaccines = False
        self.flags = {}                # danger sign id -> localised label
        self.problems = {}             # field -> i18n args for the re-ask
        self.saved_records = []
        self.transcript = []
        # Set by the transport after it has announced an automatic switch.
        self.language_changed = None
        self._ask_again_for = None     # last field asked, to avoid blind repeats

    # ---------- language ----------
    def set_language(self, code) -> str:
        self.language = i18n.normalize_lang(code)
        return self.language

    @property
    def language_name(self) -> str:
        return i18n.LANGUAGE_NAMES[self.language]

    def t(self, key, **kwargs) -> str:
        return i18n.t(self.language, key, **kwargs)

    def greeting(self) -> str:
        return self.t("greeting")

    def _follow_language(self, text: str) -> str:
        """Switch to the language the worker just spoke, if it is a new one."""
        self.language_changed = None
        if not self.auto_language or self.state == "saved":
            return ""
        detected = lang_detect.detect_language(text)
        if not detected or detected == self.language:
            return ""
        self.language = detected
        self.language_changed = detected
        return self.t("switched", language=i18n.LANGUAGE_NAMES[detected])

    # ---------- helpers ----------
    def _tokens(self, text: str) -> set:
        return set(_TOKEN_RE.findall(text.lower()))

    _PAUSE_RE = re.compile(
        r"(?:ఒక్క\s*నిమిషం|ఒక\s*నిమిషం|నిమిషం|ఆగండి|ఆగు|"
        r"एक\s*मिनट|ज़रा\s*रुको|रुको|रुकिए|थोड़ा\s*रुक|"
        r"ஒரு\s*நிமிடம்|இருங்க|பொறுங்கள்|"
        r"ಒಂದು\s*ನಿಮಿಷ|ತಾಳಿ|"
        r"ഒരു\s*നിമിഷം|"
        r"এক\s*মিনিট|একটু\s*দাঁড়ান|"
        r"एक\s*मिनिट|थांबा|"
        r"\bone\s*minute\b|\bjust\s*a\s*minute\b|\bwait\s*a\s*minute\b|\bwait\s*a\s*second\b|"
        r"\bgive\s*me\s*a\s*second\b|\bgive\s*me\s*a\s*minute\b|\bhold\s*on\b|\bjust\s*a\s*sec\b|\bwait\b)",
        re.IGNORECASE,
    )

    def _is_pause(self, text: str) -> bool:
        return bool(self._PAUSE_RE.search(text))

    def _missing(self):
        for field in ORDER:
            if field == "vaccinations_due":
                if not self.record.get(field) and not self.asked_vaccines:
                    return field
            elif self.record.get(field) is None:
                return field
        return None

    def _is_confirm(self, text: str) -> bool:
        if re.search(r"\d", text):
            return False
        tokens = self._tokens(text)
        yes = i18n.words(self.language, "yes_words")
        no = i18n.words(self.language, "no_words")
        return any(word in tokens for word in yes) and not any(word in tokens for word in no)

    def _is_negative(self, text: str) -> bool:
        tokens = self._tokens(text)
        return any(word in tokens for word in i18n.words(self.language, "no_words"))

    def _summary(self, fields) -> str:
        """Localised "ID X, weight 52 kilos" for the fields just filled."""
        parts = []
        for field in fields:
            value = self.record.get(field)
            if field == "vaccinations_due":
                value = ", ".join(value or [])
            elif field == "visit_type":
                value = i18n.visit_label(self.language, value)
            elif field == "weight_kg" and value is not None:
                value = f"{value:g}"
            if value in (None, ""):
                continue
            parts.append(self.t(FIELD_LABELS[field], value=value))
        return ", ".join(parts)

    def _readback(self) -> str:
        record = self.record
        parts = [
            self.t("rb_id", value=record["beneficiary_id"]),
            self.t("rb_visit", value=i18n.visit_label(self.language, record["visit_type"])),
            self.t("rb_weight", value=f"{record['weight_kg']:g}"),
            self.t("rb_vacc", value=", ".join(record["vaccinations_due"]) or self.t("rb_none")),
            self.t("rb_date", value=record["next_visit_date"]),
        ]
        return self.t("readback_prefix") + ", ".join(parts) + ". " + self.t("ask_save")

    def _save(self) -> str:
        record = dict(self.record)
        record["flagged"] = bool(self.flags)
        record["danger_signs"] = list(self.flags.values()) or record.get("danger_signs", [])
        self.saved_records.append(record)
        self.state = "saved"

        lines = [self.t("saved")]
        if record["next_visit_date"]:
            lines.append("- " + self.t("fu_next", value=record["next_visit_date"]))
        if record["vaccinations_due"]:
            lines.append("- " + self.t("fu_vacc", value=", ".join(record["vaccinations_due"])))
        if record["flagged"]:
            lines.append("- " + self.t("fu_referral"))
        return "\n".join(lines)

    def _next_prompt(self, field: str) -> str:
        args = dict(self.problems.get(field) or {})
        code = args.pop("code", QUESTION_KEYS[field])
        return self.t(code, **args)

    def pending_prompt(self) -> str:
        """What to say when a save is requested before the record is complete."""
        last = self._ask_again_for
        if last and self.record.get(last) in (None, "", []):
            return self._next_prompt(last)
        missing = self._missing()
        return self._next_prompt(missing) if missing else self.t("ask_save")

    def save_now(self) -> str | None:
        """Explicit save from a button. None when details are still missing."""
        if self.state == "saved":
            return self.t("already_saved")
        if self._missing():
            return None
        if not self.saved_records:
            self._save()
        return self.t("saved")

    def _merge(self, base: dict, delta: dict) -> dict:
        """Merge extracted fields without letting silence wipe what we have."""
        merged = {**EMPTY_RECORD, **base}
        for key, value in (delta or {}).items():
            if key not in merged:
                continue
            if key == "danger_signs":
                if value:
                    merged[key] = list(value)
                continue
            if value is None:
                continue
            if key == "vaccinations_due":
                if value:
                    merged[key] = value
                continue
            merged[key] = value
        return merged

    # ---------- main entry ----------
    async def handle(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return self.t("did_not_catch")

        self.transcript.append(text)

        if self.state == "saved":
            return self.t("already_saved")

        switch_note = self._follow_language(text)

        # 0) check conversational pause / wait phrases ("one minute", "oka nimisham", "ruko")
        if self._is_pause(text) and not re.search(r"\d", text):
            return f"{switch_note} {self.t('take_your_time')}".strip() if switch_note else self.t("take_your_time")

        if self.state == "readback":
            if self._is_confirm(text):
                return self._save()
            if self._is_negative(text) and not re.search(r"\d", text):
                # Plain "no" - ask what to correct. A correction that carries
                # a number ("no, weight 2.8") falls through and is extracted.
                self.state = "collecting"
                self._ask_again_for = None
                return self.t("ask_change")

        replies = []
        if switch_note:
            replies.append(switch_note)

        before = dict(self.record)

        # 1) danger signs first - deterministic, no LLM
        hits = check_danger_signs(text, self.record.get("visit_type"))

        # 2) extract fields
        extract_failed = False
        conversational_reply = ""
        try:
            delta = await extract(text, self.record)
            if isinstance(delta, dict):
                conversational_reply = str(delta.pop("reply", "") or "").strip()
        except Exception as exc:  # noqa: BLE001 - degrade to "say it again"
            print("extract error:", exc)
            extract_failed = True
            delta = {}

        # Resolve beneficiary name to existing beneficiary ID if found
        raw_bid = delta.get("beneficiary_id")
        if raw_bid and hasattr(storage, "find_beneficiary_by_name"):
            found = storage.find_beneficiary_by_name(str(raw_bid))
            if found:
                delta["beneficiary_id"] = found["beneficiary_id"]

        merged = self._merge(before, delta)

        if not hits:
            hits = check_danger_signs(text, merged.get("visit_type"))

        # 3) clinical validation envelopes
        cleaned, problems = validation.validate_record(merged)
        cleaned["danger_signs"] = list(merged.get("danger_signs") or [])
        self.record = cleaned
        self.problems = problems

        for hit in hits:
            if hit["id"] not in self.flags:
                label = i18n.danger_label(self.language, hit["id"], hit["label"])
                self.flags[hit["id"]] = label
                replies.append(self.t("refer", label=label))
        for sign in self.record.get("danger_signs") or []:
            if sign not in self.flags.values() and not hits:
                self.flags[sign] = sign
                replies.append(self.t("refer", label=sign))

        # 4) acknowledge what was just heard
        filled = [
            field for field in ORDER
            if field in FIELD_LABELS
            and self.record.get(field) != before.get(field)
            and self.record.get(field) not in (None, "", [])
        ]
        summary = self._summary(filled)
        if summary:
            self._ask_again_for = None
            replies.append(self.t("ack", summary=summary))

        if extract_failed:
            replies.append(self.t("did_not_catch"))
            missing = self._missing()
            if missing:
                replies.append(self._next_prompt(missing))
            return " ".join(replies).strip()

        # 5) re-ask a rejected value, ask the next field, or read back
        problem_field = next((f for f in ORDER if f in self.problems), None)
        if problem_field:
            self._ask_again_for = problem_field
            replies.append(self._next_prompt(problem_field))
        else:
            missing = self._missing()
            if missing:
                if (
                    not summary
                    and not hits
                    and self._ask_again_for == missing
                ):
                    replies.append(self.t("nothing_heard"))
                if missing == "vaccinations_due":
                    self.asked_vaccines = True
                self._ask_again_for = missing
                self.state = "collecting"
                if conversational_reply and not hits and not summary:
                    return f"{switch_note} {conversational_reply}".strip() if switch_note else conversational_reply
                elif conversational_reply and not hits:
                    return f"{switch_note} {conversational_reply}".strip() if switch_note else conversational_reply
                replies.append(self._next_prompt(missing))
            else:
                self.state = "readback"
                self._ask_again_for = None
                replies.append(self._readback())

        return " ".join(part for part in replies if part).strip()

    # ---------- payload ----------
    def to_visit_payload(self) -> dict:
        record = dict(self.record)
        record["flagged"] = bool(self.flags)
        record["danger_signs"] = list(self.flags.values()) or record.get("danger_signs", [])
        return record

    def transcript_text(self) -> str:
        return "\n".join(self.transcript)

"""Book sources for question generation."""

from __future__ import annotations

import random
import re

from .essential1 import ESSENTIAL_1_UNITS

BOOKS = {
    "essential1": {
        "id": "essential1",
        "title": "4000 Essential English Words 1",
        "short": "Essential 1",
        "units": ESSENTIAL_1_UNITS,
    },
}


def list_books():
    return list(BOOKS.values())


def get_book(book_id: str):
    return BOOKS.get(book_id)


def get_unit(book_id: str, unit: int):
    book = get_book(book_id)
    if not book:
        return None
    for u in book["units"]:
        if int(u["unit"]) == int(unit):
            return u
    return None


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _mask_example(example: str, word: str) -> str:
    """Replace target word in example with ___ (case-insensitive, word boundary)."""
    ex = _clean(example)
    w = _clean(word)
    if not ex or not w:
        return ""
    pattern = re.compile(rf"\b{re.escape(w)}\b", flags=re.IGNORECASE)
    masked, n = pattern.subn("___", ex, count=1)
    if n == 0:
        # fallback: simple replace
        masked = ex.replace(w, "___", 1)
        if masked == ex:
            return ""
    return masked


def build_question_items(book_id: str, unit: int, qtype: str):
    """Build question items compatible with db.add_questions_bulk.

    qtype:
      - vocab: Uzbek/meaning -> English word (MCQ + typing word)
      - gap:   example sentence with blank -> word
      - definition: English definition -> word
    """
    u = get_unit(book_id, unit)
    if not u:
        return []
    words = [w for w in u.get("words", []) if _clean(w.get("word"))]
    if not words:
        return []

    all_words = [_clean(w["word"]) for w in words]
    items = []

    for idx, entry in enumerate(words):
        word = _clean(entry["word"])
        definition = _clean(entry.get("definition"))
        uz = _clean(entry.get("uz"))
        example = _clean(entry.get("example"))

        if qtype == "definition":
            if not definition:
                continue
            prompt = definition
            answer = word
        elif qtype == "gap":
            prompt = _mask_example(example, word)
            if not prompt:
                continue
            answer = word
        else:  # vocab
            prompt = uz or definition
            if not prompt:
                continue
            answer = word

        # distractors: other words from same unit
        pool = [w for w in all_words if w.lower() != word.lower()]
        random.shuffle(pool)
        distractors = pool[:3]
        # pad if unit has <4 words
        while len(distractors) < 3:
            distractors.append(f"option{len(distractors)+1}")

        items.append(
            {
                "uz": prompt,
                "en": answer,
                "options": [answer, *distractors],
            }
        )

    return items


def available_question_types(book_id: str, unit: int):
    """Return qtypes that can be generated for this unit."""
    u = get_unit(book_id, unit)
    if not u:
        return []
    words = u.get("words", [])
    has_def = any(_clean(w.get("definition")) for w in words)
    has_gap = any(_mask_example(w.get("example", ""), w.get("word", "")) for w in words)
    has_vocab = any(_clean(w.get("uz")) or _clean(w.get("definition")) for w in words)
    types = []
    if has_vocab:
        types.append("vocab")
    if has_gap:
        types.append("gap")
    if has_def:
        types.append("definition")
    return types

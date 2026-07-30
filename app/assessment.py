"""Research & Assessment Engine.

Parses the active case's evidence_log narrative text, flags keywords, and
matches them against statute_reference entries to surface laws the landlord
may be violating.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

from sqlalchemy.orm import Session

from app.models import Case, EvidenceLog, StatuteReference


# Canonical keyword lexicon used for flagging. Each entry maps to a display
# label and a list of raw-word patterns that count as a hit in narrative text.
KEYWORD_LEXICON: dict[str, list[str]] = {
    "mold": ["mold", "mould", "fungus", "mildew"],
    "heat": ["heat", "heating", "radiator", "cold", "thermostat", "furnace"],
    "water": ["water", "leak", "plumbing", "pipe", "flooding", "sewage"],
    "deposit": ["deposit", "security deposit", "withheld deposit"],
    "pests": ["roach", "roaches", "bedbug", "bed bug", "rat", "mice", "vermin", "insect"],
    "locks": ["lock", "locks", "changed locks", "locked out", "deadbolt"],
    "harassment": ["harass", "harassment", "intimidat", "threat", "retaliat"],
    "repairs": ["repair", "repairs", "broken", "fix", "maintenance", "unrepaired"],
    "entry": ["entered", "entry", "no notice", "entered without notice", "intrusion"],
    "electricity": ["electric", "power", "outlet", "wiring", "lights out"],
    "rent": ["rent", "overcharge", "illegal increase", "fees"],
    "eviction": ["evict", "eviction", "notice to quit", " unlawful detainer"],
}


def _flatten_evidence(evidence: Iterable[EvidenceLog]) -> str:
    return " \n ".join((e.narrative_text or "") for e in evidence).lower()


def flag_keywords(text: str) -> list[dict]:
    """Return a list of {keyword, count, samples} for keywords found in text."""
    lowered = text.lower()
    hits: list[dict] = []
    for key, patterns in KEYWORD_LEXICON.items():
        count = 0
        first_match = None
        for pat in patterns:
            # word-boundary match so "rat" does not hit "radiator", etc.
            for m in re.finditer(rf"(?<!\w){re.escape(pat)}(?!\w)", lowered):
                count += 1
                if first_match is None:
                    first_match = m
        if count > 0:
            sample = ""
            if first_match:
                start = max(0, first_match.start() - 40)
                end = min(len(lowered), first_match.end() + 60)
                sample = text[start:end].replace("\n", " ").strip()
            hits.append({"keyword": key, "count": count, "sample": sample})
    hits.sort(key=lambda h: h["count"], reverse=True)
    return hits


def assess_case(db: Session, case_id: int) -> dict:
    """Run the assessment for a case and return matched statutes + flags."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return {"error": "case not found"}

    evidence = db.query(EvidenceLog).filter(EvidenceLog.case_id == case_id).all()
    corpus = _flatten_evidence(evidence)
    flags = flag_keywords(corpus)

    # Match flags against statute keyword_tags
    statutes = db.query(StatuteReference).all()
    matched: list[dict] = []
    flagged_keys = {f["keyword"] for f in flags}
    for st in statutes:
        st_keys = set(st.keywords())
        overlap = flagged_keys & st_keys
        if overlap:
            matched.append({
                "statute": st.to_dict(),
                "matched_keywords": sorted(overlap),
            })
    # rank by number of matched keywords
    matched.sort(key=lambda m: len(m["matched_keywords"]), reverse=True)

    return {
        "case_id": case_id,
        "case_title": case.title,
        "evidence_count": len(evidence),
        "flags": flags,
        "matched_statutes": matched,
    }


def search_statutes(db: Session, query: str | None = None, jurisdiction: str | None = None) -> list[dict]:
    q = db.query(StatuteReference)
    if jurisdiction:
        q = q.filter(StatuteReference.jurisdiction.ilike(f"%{jurisdiction}%"))
    if query:
        like = f"%{query.lower()}%"
        q = q.filter(
            (StatuteReference.law_citation_title.ilike(f"%{query}%"))
            | (StatuteReference.keyword_tags.ilike(like))
            | (StatuteReference.legal_text_body.ilike(f"%{query}%"))
        )
    return [s.to_dict() for s in q.order_by(StatuteReference.jurisdiction, StatuteReference.law_citation_title).all()]

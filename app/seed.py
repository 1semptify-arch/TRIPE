"""Seed the database with structured mock cases, evidence, and statutes.

All case-specific seed values are loaded from app/case_config.py so the same
codebase can be reused for different cases or jurisdictions.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Case, CaseStatus, EvidenceLog, StatuteReference
from app.case_config import SEED_CASES, CASE_JURISDICTION, CASE_TENANT_NAME


def _env_evidence(idx: int, default: str) -> str:
    return os.getenv(f"TRIPE_CASE_EVIDENCE_{idx}", default)


def seed(db: Session) -> None:
    if db.query(Case).count() > 0:
        return  # already seeded

    base = datetime.utcnow() - timedelta(days=40)

    # ---- Cases ----
    cases = []
    for cfg in SEED_CASES:
        cases.append(Case(
            title=cfg["title"],
            landlord_name=cfg["landlord_name"],
            property_address=cfg["property_address"],
            status=CaseStatus.Escalating,
        ))
    db.add_all(cases)
    db.flush()

    c1, c2, c3 = cases[0], cases[1], cases[2]

    # ---- Evidence for case1 ----
    c1_evidence = [
        EvidenceLog(case_id=c1.id, event_timestamp=base + timedelta(days=1),
                    issue_type="Maintenance",
                    narrative_text=_env_evidence(1, f"Discovered black mold spreading along the bathroom wall. Reported it to {c1.landlord_name} the same day by phone."),
                    file_path_metadata="photos/mold_bathroom_01.jpg"),
        EvidenceLog(case_id=c1.id, event_timestamp=base + timedelta(days=5),
                    issue_type="Maintenance",
                    narrative_text=_env_evidence(2, "Heat failed entirely during cold snap. Furnace not working; indoor temperature dropped. No response from landlord after three calls."),
                    file_path_metadata="receipts/thermometer_reading.png"),
        EvidenceLog(case_id=c1.id, event_timestamp=base + timedelta(days=9),
                    issue_type="Harassment",
                    narrative_text=_env_evidence(3, f"Landlord entered the unit without any notice while {CASE_TENANT_NAME} was at work to 'inspect' the complaint. No written notice was given."),
                    file_path_metadata=""),
        EvidenceLog(case_id=c1.id, event_timestamp=base + timedelta(days=14),
                    issue_type="Financial",
                    narrative_text=_env_evidence(4, "Withheld a portion of rent for space heaters and a dehumidifier to mitigate the mold and heat failure. Landlord threatened to charge late fees."),
                    file_path_metadata="receipts/heater_purchase.pdf"),
    ]

    # ---- Evidence for case2 ----
    c2_evidence = [
        EvidenceLog(case_id=c2.id, event_timestamp=base + timedelta(days=2),
                    issue_type="Financial",
                    narrative_text=_env_evidence(5, f"Moved out and returned keys. Landlord {c2.landlord_name} has not returned the security deposit or provided an itemized list within the required time."),
                    file_path_metadata="lease/moveout_letter.pdf"),
        EvidenceLog(case_id=c2.id, event_timestamp=base + timedelta(days=20),
                    issue_type="Harassment",
                    narrative_text=_env_evidence(6, f"Sent written demand for return of the deposit. Landlord {c2.landlord_name} replied with threats to file an eviction if {CASE_TENANT_NAME} pursued it."),
                    file_path_metadata="letters/demand_letter.pdf"),
    ]

    # ---- Evidence for case3 ----
    c3_evidence = [
        EvidenceLog(case_id=c3.id, event_timestamp=base + timedelta(days=3),
                    issue_type="Harassment",
                    narrative_text=_env_evidence(7, f"Landlord {c3.landlord_name} entered the unit without notice a second time this month, claiming to check 'plumbing'. No repair was actually performed."),
                    file_path_metadata=""),
        EvidenceLog(case_id=c3.id, event_timestamp=base + timedelta(days=7),
                    issue_type="Harassment",
                    narrative_text=_env_evidence(8, "After complaining about the unlawful entry, landlord began retaliatory threats and posted a notice to quit on the door the next week."),
                    file_path_metadata="photos/notice_to_quit.jpg"),
    ]
    db.add_all(c1_evidence + c2_evidence + c3_evidence)

    # ---- Statutes ----
    statutes = [
        StatuteReference(
            jurisdiction=CASE_JURISDICTION,
            keyword_tags="mold,repairs,habitable,warranty of habitability",
            law_citation_title=os.getenv("TRIPE_STATUTE_REPAIR", "Residential Tenants' Right to Repair Act"),
            legal_text_body="If a landlord fails to make repairs that materially affect health or safety within the period required after written notice, a tenant may have the repair made and deduct the cost from rent. Conditions such as mold and lack of heat fall within the warranty of habitability.",
        ),
        StatuteReference(
            jurisdiction=CASE_JURISDICTION,
            keyword_tags="heat,habitable,warranty of habitability,repairs",
            law_citation_title=os.getenv("TRIPE_STATUTE_HEAT", "Warranty of Habitability — Heat"),
            legal_text_body="A landlord must supply heat capable of maintaining a minimum indoor temperature. Failure to provide heat during cold months is a breach of the implied warranty of habitability and may justify rent withholding or repair-and-deduct remedies.",
        ),
        StatuteReference(
            jurisdiction=CASE_JURISDICTION,
            keyword_tags="entry,harassment,notice,locks",
            law_citation_title=os.getenv("TRIPE_STATUTE_ENTRY", "Entry and Notice; Tenant Right to Privacy"),
            legal_text_body="A landlord may enter a dwelling unit only after providing reasonable notice except in emergencies. Repeated entry without notice constitutes a breach of the tenant's right to quiet enjoyment and may support damages.",
        ),
        StatuteReference(
            jurisdiction=CASE_JURISDICTION,
            keyword_tags="deposit,security deposit,financial,rent",
            law_citation_title=os.getenv("TRIPE_STATUTE_DEPOSIT", "Security Deposit Return Act"),
            legal_text_body="A landlord must return a tenant's security deposit, minus any itemized deductions, within the required period after lease termination. Failure to provide an itemized list or to return the deposit may entitle the tenant to damages and attorney's fees.",
        ),
        StatuteReference(
            jurisdiction=CASE_JURISDICTION,
            keyword_tags="harassment,retaliation,eviction,rent",
            law_citation_title=os.getenv("TRIPE_STATUTE_RETALIATION", "Retaliatory Eviction Act"),
            legal_text_body="It is unlawful for a landlord to evict, threaten to evict, or otherwise retaliate against a tenant because the tenant complained to a governmental authority about a code violation or exercised a legal right. Retaliation creates a rebuttable presumption in the tenant's favor.",
        ),
        StatuteReference(
            jurisdiction=CASE_JURISDICTION,
            keyword_tags="water,plumbing,repairs,habitable",
            law_citation_title=os.getenv("TRIPE_STATUTE_PLUMBING", "Property Maintenance Code — Plumbing & Sanitation"),
            legal_text_body="A landlord must maintain plumbing and water systems in safe, working condition. Unrepaired leaks, sewage, or lack of water constitute a breach of habitability standards.",
        ),
        StatuteReference(
            jurisdiction=CASE_JURISDICTION,
            keyword_tags="pests,vermin,repairs,habitable",
            law_citation_title=os.getenv("TRIPE_STATUTE_PESTS", "Property Maintenance Code — Pest Control"),
            legal_text_body="A landlord must keep a dwelling free from rodent and insect infestation. Failure to remediate roach, bedbug, or rodent infestations is a breach of the warranty of habitability.",
        ),
        StatuteReference(
            jurisdiction=CASE_JURISDICTION,
            keyword_tags="electricity,repairs,habitable",
            law_citation_title=os.getenv("TRIPE_STATUTE_ELECTRICAL", "Property Maintenance Code — Electrical Service"),
            legal_text_body="A landlord must maintain electrical systems, outlets, and lighting in safe working order. Loss of electrical service affecting health or safety is a breach of habitability.",
        ),
        StatuteReference(
            jurisdiction="Federal",
            keyword_tags="harassment,retaliation",
            law_citation_title="42 U.S.C. § 3617 — Fair Housing Act Interference & Intimidation",
            legal_text_body="It is unlawful to coerce, intimidate, threaten, or interfere with any person in the exercise or enjoyment of fair housing rights. Pattern of harassment may support a federal claim.",
        ),
    ]
    db.add_all(statutes)
    db.commit()

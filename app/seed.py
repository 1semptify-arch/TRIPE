"""Seed the database with structured mock cases, evidence, and statutes."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Case, CaseStatus, EvidenceLog, StatuteReference


def seed(db: Session) -> None:
    if db.query(Case).count() > 0:
        return  # already seeded

    base = datetime.utcnow() - timedelta(days=40)

    # ---- Cases ----
    case1 = Case(
        title="Mold & Heat Failure — 142 Elm St",
        landlord_name="Northgate Holdings LLC",
        property_address="142 Elm St, Apt 3B, Springfield, IL 62704",
        status=CaseStatus.Escalating,
    )
    case2 = Case(
        title="Withheld Security Deposit — 88 Oak Ave",
        landlord_name="Riverside Property Management",
        property_address="88 Oak Ave, Unit 12, Springfield, IL 62702",
        status=CaseStatus.Researching,
    )
    case3 = Case(
        title="Retaliatory Entry & Harassment — 9 Maple Ct",
        landlord_name="Cedarbrook Realty Trust",
        property_address="9 Maple Ct, Springfield, IL 62701",
        status=CaseStatus.Recording,
    )
    db.add_all([case1, case2, case3])
    db.flush()

    # ---- Evidence for case1 (mold + heat) ----
    c1_evidence = [
        EvidenceLog(case_id=case1.id, event_timestamp=base + timedelta(days=1),
                    issue_type="Maintenance",
                    narrative_text="Discovered black mold spreading along the bathroom wall and behind the radiator. Reported it to Northgate Holdings the same day by phone.",
                    file_path_metadata="photos/mold_bathroom_01.jpg"),
        EvidenceLog(case_id=case1.id, event_timestamp=base + timedelta(days=5),
                    issue_type="Maintenance",
                    narrative_text="Heat failed entirely during cold snap. Furnace not working; indoor temperature dropped to 48F. No response from landlord after three calls.",
                    file_path_metadata="receipts/thermometer_reading.png"),
        EvidenceLog(case_id=case1.id, event_timestamp=base + timedelta(days=9),
                    issue_type="Harassment",
                    narrative_text="Landlord entered the unit without any notice while I was at work to 'inspect' the mold complaint. No written notice was given.",
                    file_path_metadata=""),
        EvidenceLog(case_id=case1.id, event_timestamp=base + timedelta(days=14),
                    issue_type="Financial",
                    narrative_text="Withheld $40 from rent for space heaters and dehumidifier to mitigate the mold and heat failure. Landlord threatened to charge late fees.",
                    file_path_metadata="receipts/heater_purchase.pdf"),
    ]
    # ---- Evidence for case2 (deposit) ----
    c2_evidence = [
        EvidenceLog(case_id=case2.id, event_timestamp=base + timedelta(days=2),
                    issue_type="Financial",
                    narrative_text="Moved out of 88 Oak Ave and returned keys. Landlord Riverside Property Management has not returned the $1,800 security deposit or provided any itemized list within 30 days.",
                    file_path_metadata="lease/moveout_letter.pdf"),
        EvidenceLog(case_id=case2.id, event_timestamp=base + timedelta(days=20),
                    issue_type="Harassment",
                    narrative_text="Sent written demand for return of the deposit. Landlord replied with threats to file an eviction on the prior tenancy if I pursued it.",
                    file_path_metadata="letters/demand_letter.pdf"),
    ]
    # ---- Evidence for case3 (entry + harassment) ----
    c3_evidence = [
        EvidenceLog(case_id=case3.id, event_timestamp=base + timedelta(days=3),
                    issue_type="Harassment",
                    narrative_text="Landlord Cedarbrook Realty entered my unit without notice a second time this month, claiming to check 'plumbing'. No repair was actually performed.",
                    file_path_metadata=""),
        EvidenceLog(case_id=case3.id, event_timestamp=base + timedelta(days=7),
                    issue_type="Harassment",
                    narrative_text="After I complained about the unlawful entry, landlord began retaliatory threats and posted a notice to quit on my door the next week.",
                    file_path_metadata="photos/notice_to_quit.jpg"),
    ]
    db.add_all(c1_evidence + c2_evidence + c3_evidence)

    # ---- Statutes ----
    statutes = [
        StatuteReference(
            jurisdiction="Illinois",
            keyword_tags="mold,repairs,habitable,warranty of habitability",
            law_citation_title="765 ILCS 742 — Residential Tenants' Right to Repair Act",
            legal_text_body="If a landlord fails to make repairs that materially affect health or safety within 14 days after written notice, a tenant may have the repair made and deduct the cost (up to specified limits) from rent. Conditions such as mold and lack of heat fall within the warranty of habitability.",
        ),
        StatuteReference(
            jurisdiction="Illinois",
            keyword_tags="heat,habitable,warranty of habitability,repairs",
            law_citation_title="Chicago Municipal Code § 7-28-030 (applied by analogy) / IL Warranty of Habitability",
            legal_text_body="A landlord must supply heat capable of maintaining a minimum indoor temperature. Failure to provide heat during cold months is a breach of the implied warranty of habitability and may justify rent withholding or repair-and-deduct remedies.",
        ),
        StatuteReference(
            jurisdiction="Illinois",
            keyword_tags="entry,harassment,notice,locks",
            law_citation_title="765 ILCS 705 — Entry and Notice; Tenant Right to Privacy",
            legal_text_body="A landlord may enter a dwelling unit only after providing reasonable notice (generally 48 hours) except in emergencies. Repeated entry without notice constitutes a breach of the tenant's right to quiet enjoyment and may support damages.",
        ),
        StatuteReference(
            jurisdiction="Illinois",
            keyword_tags="deposit,security deposit,financial,rent",
            law_citation_title="765 ILCS 710/1 — Security Deposit Return Act",
            legal_text_body="A landlord must return a tenant's security deposit, minus any itemized deductions, within 30 days of lease termination. Failure to provide an itemized list or to return the deposit may entitle the tenant to damages and attorney's fees.",
        ),
        StatuteReference(
            jurisdiction="Illinois",
            keyword_tags="harassment,retaliation,eviction,rent",
            law_citation_title="765 ILCS 720 — Retaliatory Eviction Act",
            legal_text_body="It is unlawful for a landlord to evict, threaten to evict, or otherwise retaliate against a tenant because the tenant complained to a governmental authority about a code violation or exercised a legal right. Retaliation creates a rebuttable presumption in the tenant's favor.",
        ),
        StatuteReference(
            jurisdiction="Illinois",
            keyword_tags="water,plumbing,repairs,habitable",
            law_citation_title="IL Property Maintenance Code — Plumbing & Sanitation",
            legal_text_body="A landlord must maintain plumbing and water systems in safe, working condition. Unrepaired leaks, sewage, or lack of water constitute a breach of habitability standards.",
        ),
        StatuteReference(
            jurisdiction="Illinois",
            keyword_tags="pests,vermin,repairs,habitable",
            law_citation_title="IL Property Maintenance Code — Pest Control",
            legal_text_body="A landlord must keep a dwelling free from rodent and insect infestation. Failure to remediate roach, bedbug, or rodent infestations is a breach of the warranty of habitability.",
        ),
        StatuteReference(
            jurisdiction="Illinois",
            keyword_tags="electricity,repairs,habitable",
            law_citation_title="IL Property Maintenance Code — Electrical Service",
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

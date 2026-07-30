"""Action & Generation Tools.

Compiles complete Markdown/HTML document text strings for:
  - Official Complaint (form letter / formal request to remedy a lease violation)
  - Press Release (media-ready alert detailing landlord negligence)
  - Attorney Packet (structured chronological index of all recorded evidence)
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable

from app.models import Case, EvidenceLog, GeneratedAction, ActionType


def _fmt_ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M") if dt else "—"


def _evidence_summary_lines(evidence: Iterable[EvidenceLog]) -> list[str]:
    lines = []
    for i, e in enumerate(evidence, 1):
        lines.append(
            f"{i}. **[{_fmt_ts(e.event_timestamp)}] — {e.issue_type}**  \n"
            f"{e.narrative_text}"
            + (f"  \n_Attachment: {e.file_path_metadata}_" if e.file_path_metadata else "")
        )
    return lines


def generate_official_complaint(case: Case, evidence: list[EvidenceLog], tenant_name: str = "Tenant of Record") -> str:
    today = datetime.utcnow().strftime("%B %d, %Y")
    top_issues = ", ".join(sorted({e.issue_type for e in evidence})) or "lease violations"
    body = "\n\n".join(_evidence_summary_lines(evidence)) or "_No incidents recorded yet._"

    return f"""# OFFICIAL COMPLAINT & REQUEST TO REMEDY LEASE VIOLATIONS

**Date:** {today}

**From:** {tenant_name}
**To:** {case.landlord_name}
**Re:** Property — {case.property_address}
**Case:** {case.title}

---

Dear {case.landlord_name},

This letter constitutes a formal written request that you remedy the following
ongoing lease violations and conditions at the above-referenced property. The
issues below — categorized as {top_issues} — have been documented and are
preserved as a chronological record of events.

## Recorded Incidents

{body}

## Demand

Pursuant to the applicable tenant-protection statutes and the warranty of
habitability implied in my lease, I hereby demand that you:

1. Take prompt, documented action to correct each condition described above.
2. Provide a written response within **14 days** outlining the remediation plan
   and timeline for each item.
3. Cease any conduct that constitutes harassment, retaliation, or unlawful
   entry in connection with these complaints.

Failure to remedy these conditions may result in escalation to the appropriate
housing enforcement agency, administrative complaint, and/or civil action.

Sincerely,

_________________________
{tenant_name}
"""


def generate_press_release(case: Case, evidence: list[EvidenceLog], tenant_name: str = "Tenant of Record") -> str:
    today = datetime.utcnow().strftime("%B %d, %Y")
    counts: dict[str, int] = {}
    for e in evidence:
        counts[e.issue_type] = counts.get(e.issue_type, 0) + 1
    breakdown = "; ".join(f"{k}: {v}" for k, v in sorted(counts.items())) or "multiple violations"
    latest = evidence[-1] if evidence else None
    lede = (
        f"Most recently, on {_fmt_ts(latest.event_timestamp)}, the tenant reported: "
        f"\"{(latest.narrative_text or '').strip()[:240]}\""
        if latest
        else "The tenant reports an ongoing pattern of unresolved housing violations."
    )

    return f"""# FOR IMMEDIATE RELEASE

**{case.title}: Tenant Calls Attention to Pattern of Landlord Negligence**

**Date:** {today}
**Location:** {case.property_address}
**Landlord of Record:** {case.landlord_name}

---

{lede}

A tenant at {case.property_address} is raising the alarm over a sustained
pattern of unresolved housing violations by landlord {case.landlord_name}. The
tenant has compiled a documented evidence record spanning {len(evidence)}
recorded incident(s) — {breakdown}.

"This is about basic safety and the right to a livable home," said
{tenant_name}. "When a landlord refuses to address serious conditions and
instead lets them pile up, tenants have no choice but to go on the record."

The tenant's evidence log — preserved chronologically — is available to
reporters and housing advocates upon request. The matter is being escalated
through the appropriate housing enforcement channels.

**Contact for press inquiries:**
{tenant_name}
Tenant of Record — {case.property_address}

---
*Press release prepared {today} via the Tenants' Rights Integrated Protections Environment (TRIPE).*
"""


def generate_attorney_packet(case: Case, evidence: list[EvidenceLog], tenant_name: str = "Tenant of Record") -> str:
    today = datetime.utcnow().strftime("%B %d, %Y")
    index_rows = []
    for i, e in enumerate(evidence, 1):
        index_rows.append(
            f"| {i} | {_fmt_ts(e.event_timestamp)} | {e.issue_type} | "
            f"{(e.narrative_text or '').replace('|', '/')[:160]} | "
            f"{e.file_path_metadata or '—'} |"
        )
    index_table = (
        "| # | Date / Time | Issue Type | Narrative (excerpt) | Attachment |\n"
        "|---|-------------|------------|---------------------|------------|\n"
        + "\n".join(index_rows)
    ) if index_rows else "_No evidence recorded._"

    full_log = "\n\n".join(_evidence_summary_lines(evidence)) or "_No evidence recorded._"

    return f"""# ATTORNEY PACKET — EVIDENCE INDEX & CHRONOLOGY

**Prepared:** {today}
**Case:** {case.title}
**Tenant of Record:** {tenant_name}
**Landlord:** {case.landlord_name}
**Property:** {case.property_address}
**Total Recorded Incidents:** {len(evidence)}

---

## 1. Executive Summary

This packet indexes and chronologically orders all recorded evidence for the
above-referenced matter. It is intended to provide counsel with an at-a-glance
index of incidents, followed by the full narrative record. Each entry is
preserved with its original timestamp, issue category, narrative, and any
associated attachment metadata.

## 2. Chronological Index

{index_table}

## 3. Full Narrative Record

{full_log}

## 4. Next Steps Requested of Counsel

1. Review the indexed incidents for actionable claims (warranty of
   habitability, retaliation, illegal entry, deposit withholding, etc.).
2. Advise on preservation of the attached evidence and any additional
   discovery needed.
3. Recommend escalation pathway (agency complaint, civil filing, settlement
   demand).

---
*Packet generated {today} via TRIPE. This index is a summary of the tenant's
recorded evidence log and is not itself a legal filing.*
"""


GENERATORS = {
    ActionType.Official_Complaint: generate_official_complaint,
    ActionType.Press_Release: generate_press_release,
    ActionType.Attorney_Packet: generate_attorney_packet,
}


def build_document(action_type: ActionType, case: Case, evidence: list[EvidenceLog], tenant_name: str) -> str:
    fn = GENERATORS.get(action_type)
    if not fn:
        raise ValueError(f"Unknown action type: {action_type}")
    return fn(case, evidence, tenant_name)

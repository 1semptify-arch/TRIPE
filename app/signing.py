"""In-app signing engine.

Produces a deterministic SHA-256 cryptographic signature over the locked
document content + signer identity + timestamp, so any later edit to the
document content would invalidate the signature. Marks signed_status = True.
"""
from __future__ import annotations

import hashlib
from datetime import datetime

from app.models import GeneratedAction


def compute_signature(document_content: str, signed_by: str, signed_at: datetime) -> str:
    payload = f"{document_content}\n||SIGNED-BY:{signed_by}||AT:{signed_at.isoformat()}||"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sign_action(action: GeneratedAction, signed_by: str) -> GeneratedAction:
    """Lock the action against further editing and attach a signature hash."""
    if not signed_by or not signed_by.strip():
        raise ValueError("A signer name is required to sign a document.")
    if action.signed_status:
        return action  # already locked
    now = datetime.utcnow()
    action.signed_status = True
    action.signed_by = signed_by.strip()
    action.signed_at = now
    action.signature_hash = compute_signature(action.document_content, action.signed_by, now)
    return action


def verify_signature(action: GeneratedAction) -> bool:
    """Return True if the stored signature still matches the document content."""
    if not action.signed_status or not action.signature_hash or not action.signed_at:
        return False
    expected = compute_signature(action.document_content, action.signed_by or "", action.signed_at)
    return expected == action.signature_hash

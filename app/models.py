"""SQLAlchemy ORM models for TRIPE."""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from app.database import Base


class CaseStatus(enum.Enum):
    Recording = "Recording"
    Researching = "Researching"
    Escalating = "Escalating"
    Resolved = "Resolved"


class ActionType(enum.Enum):
    Official_Complaint = "Official_Complaint"
    Press_Release = "Press_Release"
    Attorney_Packet = "Attorney_Packet"


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    landlord_name = Column(String(255), nullable=False)
    property_address = Column(Text, nullable=False)
    status = Column(SAEnum(CaseStatus), default=CaseStatus.Recording, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    evidence = relationship(
        "EvidenceLog",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="EvidenceLog.event_timestamp",
    )
    actions = relationship(
        "GeneratedAction",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="GeneratedAction.timestamp.desc()",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "landlord_name": self.landlord_name,
            "property_address": self.property_address,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "evidence_count": len(self.evidence) if self.evidence else 0,
        }


class EvidenceLog(Base):
    __tablename__ = "evidence_log"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    event_timestamp = Column(DateTime, nullable=False)
    issue_type = Column(String(64), nullable=False)  # Maintenance, Harassment, Financial, ...
    narrative_text = Column(Text, nullable=False)
    file_path_metadata = Column(Text, nullable=True)  # path / description of photos/receipts
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    case = relationship("Case", back_populates="evidence")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "case_id": self.case_id,
            "event_timestamp": self.event_timestamp.isoformat() if self.event_timestamp else None,
            "issue_type": self.issue_type,
            "narrative_text": self.narrative_text,
            "file_path_metadata": self.file_path_metadata,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }


class StatuteReference(Base):
    __tablename__ = "statute_reference"

    id = Column(Integer, primary_key=True, index=True)
    jurisdiction = Column(String(128), nullable=False, index=True)
    keyword_tags = Column(Text, nullable=False)  # comma-separated keywords
    law_citation_title = Column(String(255), nullable=False)
    legal_text_body = Column(Text, nullable=False)

    def keywords(self) -> list[str]:
        return [k.strip().lower() for k in (self.keyword_tags or "").split(",") if k.strip()]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "jurisdiction": self.jurisdiction,
            "keyword_tags": self.keyword_tags,
            "law_citation_title": self.law_citation_title,
            "legal_text_body": self.legal_text_body,
        }


class GeneratedAction(Base):
    __tablename__ = "generated_actions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(SAEnum(ActionType), nullable=False)
    document_content = Column(Text, nullable=False)
    signed_status = Column(Boolean, default=False, nullable=False)
    signature_hash = Column(String(128), nullable=True)  # SHA-256 of locked content + signer
    signed_by = Column(String(255), nullable=True)
    signed_at = Column(DateTime, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    case = relationship("Case", back_populates="actions")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "case_id": self.case_id,
            "action_type": self.action_type.value if self.action_type else None,
            "document_content": self.document_content,
            "signed_status": self.signed_status,
            "signature_hash": self.signature_hash,
            "signed_by": self.signed_by,
            "signed_at": self.signed_at.isoformat() if self.signed_at else None,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

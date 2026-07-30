"""TRIPE — Tenants' Rights Integrated Protections Environment.

FastAPI application: IDE-like workspace for recording evidence, researching
tenant statutes, generating legal packets, and governing escalation.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.config import APP_HOST, APP_PORT
from app.database import engine, Base, get_db
from app import models
from app import assessment as assess_mod
from app.generators import build_document
from app.signing import sign_action, verify_signature
from app.seed import seed as seed_db

app = FastAPI(title="TRIPE — Tenants' Rights Integrated Protections Environment")

Base.metadata.create_all(bind=engine)

# Seed on startup (idempotent).
from app.database import SessionLocal  # noqa: E402
_seed_session = SessionLocal()
try:
    seed_db(_seed_session)
finally:
    _seed_session.close()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _parse_dt(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("T", " "))
    except Exception:
        try:
            return datetime.fromisoformat(value)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid timestamp: {value}")


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def workspace_page(request: Request, db: Session = Depends(get_db)):
    cases = db.query(models.Case).order_by(models.Case.created_at.desc()).all()
    return templates.TemplateResponse(
        "workspace.html",
        {"request": request, "cases": [c.to_dict() for c in cases]},
    )


@app.get("/workspace", response_class=HTMLResponse)
def workspace_alias(request: Request, db: Session = Depends(get_db)):
    return workspace_page(request, db)


@app.get("/health")
def health():
    return {"status": "ok", "app": "TRIPE"}


# ---------------------------------------------------------------------------
# MODULE 1 — Record Keeping & Evidence Engine
# ---------------------------------------------------------------------------
@app.post("/workspace/record")
def record_evidence(
    case_id: int = Form(...),
    event_timestamp: str = Form(...),
    issue_type: str = Form(...),
    narrative_text: str = Form(...),
    file_path_metadata: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    entry = models.EvidenceLog(
        case_id=case_id,
        event_timestamp=_parse_dt(event_timestamp),
        issue_type=issue_type.strip() or "Maintenance",
        narrative_text=narrative_text.strip(),
        file_path_metadata=(file_path_metadata or "").strip() or None,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return JSONResponse(
        status_code=201,
        content={
            "ok": True,
            "message": "Evidence recorded",
            "entry": entry.to_dict(),
        },
    )


# ---------------------------------------------------------------------------
# MODULE 2 — Research & Assessment Engine
# ---------------------------------------------------------------------------
@app.get("/workspace/research")
def research(
    q: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    db: Session = Depends(get_db),
):
    results = assess_mod.search_statutes(db, query=q, jurisdiction=jurisdiction)
    return {"query": q, "jurisdiction": jurisdiction, "count": len(results), "results": results}


@app.get("/workspace/assessment/{case_id}")
def assessment_endpoint(case_id: int, db: Session = Depends(get_db)):
    return assess_mod.assess_case(db, case_id)


# ---------------------------------------------------------------------------
# MODULE 3 — Action & Generation Tools
# ---------------------------------------------------------------------------
@app.post("/workspace/generate")
def generate_action(
    case_id: int = Form(...),
    action_type: str = Form(...),
    tenant_name: str = Form("Tenant of Record"),
    db: Session = Depends(get_db),
):
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    try:
        atype = models.ActionType(action_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid action_type: {action_type}")
    evidence = db.query(models.EvidenceLog).filter(models.EvidenceLog.case_id == case_id).all()
    content = build_document(atype, case, evidence, tenant_name)
    action = models.GeneratedAction(
        case_id=case_id,
        action_type=atype,
        document_content=content,
        signed_status=False,
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return JSONResponse(
        status_code=201,
        content={
            "ok": True,
            "message": f"{atype.value} generated",
            "action": action.to_dict(),
        },
    )


@app.post("/workspace/sign/{action_id}")
def sign_document(
    action_id: int,
    signed_by: str = Form(...),
    confirm: str = Form(...),
    db: Session = Depends(get_db),
):
    action = db.query(models.GeneratedAction).filter(models.GeneratedAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    if confirm.strip().lower() not in ("yes", "true", "on", "1"):
        raise HTTPException(status_code=400, detail="You must confirm signing by checking the box.")
    if action.signed_status:
        return {"ok": True, "message": "Already signed", "action": action.to_dict()}
    sign_action(action, signed_by)
    db.commit()
    db.refresh(action)
    return {
        "ok": True,
        "message": "Document signed and locked",
        "action": action.to_dict(),
        "signature_valid": verify_signature(action),
    }


# ---------------------------------------------------------------------------
# JSON API surface for the IDE panes
# ---------------------------------------------------------------------------
@app.get("/api/tree")
def api_tree(db: Session = Depends(get_db)):
    cases = db.query(models.Case).order_by(models.Case.created_at.desc()).all()
    tree = []
    for c in cases:
        ev = db.query(models.EvidenceLog).filter(models.EvidenceLog.case_id == c.id).all()
        actions = db.query(models.GeneratedAction).filter(models.GeneratedAction.case_id == c.id).all()
        tree.append({
            "case": c.to_dict(),
            "evidence": [e.to_dict() for e in ev],
            "actions": [a.to_dict() for a in actions],
        })
    templates_list = [
        {"name": "Official Complaint", "action_type": "Official_Complaint"},
        {"name": "Press Release", "action_type": "Press_Release"},
        {"name": "Attorney Packet", "action_type": "Attorney_Packet"},
    ]
    return {"cases": tree, "templates": templates_list}


@app.get("/api/case/{case_id}")
def api_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    evidence = db.query(models.EvidenceLog).filter(models.EvidenceLog.case_id == case_id).all()
    actions = db.query(models.GeneratedAction).filter(models.GeneratedAction.case_id == case_id).all()
    return {
        "case": case.to_dict(),
        "evidence": [e.to_dict() for e in evidence],
        "actions": [a.to_dict() for a in actions],
    }


@app.get("/api/statutes")
def api_statutes(q: Optional[str] = None, jurisdiction: Optional[str] = None, db: Session = Depends(get_db)):
    return {"results": assess_mod.search_statutes(db, query=q, jurisdiction=jurisdiction)}


@app.get("/api/assessment/{case_id}")
def api_assessment(case_id: int, db: Session = Depends(get_db)):
    return assess_mod.assess_case(db, case_id)


@app.get("/api/action/{action_id}")
def api_action(action_id: int, db: Session = Depends(get_db)):
    action = db.query(models.GeneratedAction).filter(models.GeneratedAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    d = action.to_dict()
    d["signature_valid"] = verify_signature(action) if action.signed_status else None
    return d


@app.post("/api/cases")
def create_case(
    title: str = Form(...),
    landlord_name: str = Form(...),
    property_address: str = Form(...),
    status: str = Form("Recording"),
    db: Session = Depends(get_db),
):
    try:
        st = models.CaseStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    case = models.Case(
        title=title.strip(),
        landlord_name=landlord_name.strip(),
        property_address=property_address.strip(),
        status=st,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return JSONResponse(status_code=201, content={"ok": True, "case": case.to_dict()})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=APP_HOST, port=APP_PORT, reload=True)

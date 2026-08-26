# TRIPE — Tenants' Rights Integrated Protections Environment

An IDE-like workspace (inspired by VS Code / Devin) for tenants to record
evidence, research local tenant statutes, generate legal packets, and govern
their escalation process. Built with **Python + FastAPI + PostgreSQL + Jinja2
+ plain CSS**.

## Layout

- **Left Sidebar (Explorer):** Active Cases, Evidence Folder, Templates tree.
- **Center Pane (Workspace):** Record Evidence form, Document Preview, Generate.
- **Right Sidebar (Guidance & Reference):** searchable statute directory +
  automated Assessment Tool that flags keywords in the evidence log and matches
  them against statutes to surface likely-violated laws.
- **Bottom Panel (Action Console):** live status output of every action
  (e.g. "Press Release generated", "Document signed & locked").

## Modules

1. **Record Keeping & Evidence Engine** — `POST /workspace/record` builds a
   chronological event tree per case.
2. **Research & Assessment Engine** — `GET /workspace/research` (searchable
   legal directory) + `GET /workspace/assessment/{case_id}` (keyword → statute
   matcher that populates the right sidebar).
3. **Action & Generation Tools** — `POST /workspace/generate` compiles
   Official Complaint / Press Release / Attorney Packet from case + evidence
   data. `POST /workspace/sign/{action_id}` attaches a SHA-256 cryptographic
   signature, locks the document (`signed_status = True`), and verifies
   integrity.

## Run (local)

PostgreSQL is already configured. The app uses its own DB `tripe` / user
`tripe_user` (password `tripe_pass`) — see `.env`.

```powershell
cd "C:\master-repo\sources\app-bradley-collection\tripe"
.\venv\Scripts\python.exe -m pip install -r requirements.txt   # first time
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Open http://127.0.0.1:8001 — tables are created and seeded with mock cases,
evidence, and statutes automatically on first startup.

## Key endpoints

| Method | Path | Purpose |
|---|---|---|
| GET  | `/` | IDE workspace page |
| POST | `/workspace/record` | add evidence log entry |
| GET  | `/workspace/research?q=` | search statutes |
| GET  | `/workspace/assessment/{case_id}` | run assessment |
| POST | `/workspace/generate` | compile a document |
| POST | `/workspace/sign/{action_id}` | sign & lock a document |
| GET  | `/api/tree` | explorer tree (cases/evidence/actions/templates) |
| GET  | `/api/case/{id}` | case detail + evidence + actions |
| GET  | `/api/action/{id}` | single generated action (incl. signature check) |
| POST | `/api/cases` | create a new case |

## Data model

`cases` · `evidence_log` · `statute_reference` · `generated_actions`
(see `app/models.py`).

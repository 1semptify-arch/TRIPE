# TRIPE — project notes for agents

Tenants' Rights Integrated Protections Environment. Self-contained FastAPI app
living in `tripe/` (separate from the unrelated `Case Command Center` app in
the parent directory).

## Stack
Python 3.13 · FastAPI · SQLAlchemy 2 · PostgreSQL 16 · Jinja2 · plain CSS/JS.

## Database
- DB: `tripe`, user: `tripe_user`, password: `tripe_pass`, host: localhost:5432.
- DSN lives in `tripe/.env` as `DATABASE_URL`.
- Tables are created on startup via `Base.metadata.create_all`; seed runs
  idempotently on startup (`app/seed.py` — only seeds if `cases` is empty).
- To reset to a clean seed state:
  `psql -U tripe_user -d tripe -c "DELETE FROM generated_actions; DELETE FROM evidence_log WHERE id >= 9;"`
  (or just `DELETE FROM cases;` to wipe everything and let the seed re-run).

## Run
```powershell
cd "E:\master-repo\sources\app-bradley-collection\tripe"
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```
Open http://127.0.0.1:8001. Port 8001 is TRIPE's; the Case Command Center
uses 8000. Don't run both on the same port.

## Verify (smoke test the full pipeline)
```powershell
$Base="http://127.0.0.1:8001"
(Invoke-WebRequest "$Base/health").Content                              # {"status":"ok","app":"TRIPE"}
(Invoke-WebRequest "$Base/api/tree").Content | ConvertFrom-Json         # 3 cases, 3 templates
(Invoke-WebRequest "$Base/workspace/assessment/1").Content              # flags + matched statutes
# generate + sign:
$form="case_id=1&action_type=Attorney_Packet&tenant_name=Bradley Smith"
$g = (Invoke-WebRequest "$Base/workspace/generate" -Method POST -Body $form -ContentType "application/x-www-form-urlencoded").Content | ConvertFrom-Json
$form="signed_by=Bradley Smith&confirm=yes"
$s = (Invoke-WebRequest "$Base/workspace/sign/$($g.action.id)" -Method POST -Body $form -ContentType "application/x-www-form-urlencoded").Content | ConvertFrom-Json
$s.action.signed_status   # True
$s.signature_valid        # True
```

## Layout / modules (matches the spec)
- Left sidebar (Explorer): Active Cases / Evidence Folder / Templates tree.
- Center: Record Evidence form, Document Preview, Generate tab.
- Right sidebar: statute search + Assessment Tool (keyword → statute matcher).
- Bottom: Action Console (timestamped status lines).
- Modules: `app/assessment.py` (research/assessment engine),
  `app/generators.py` (Official Complaint / Press Release / Attorney Packet),
  `app/signing.py` (SHA-256 signature, locks `signed_status = True`).

## Gotchas
- PowerShell variable names are case-insensitive — don't use `$B` for base URL
  and `$b` for form bodies in the same script; they collide.
- The IronBee DevTools browser MCP (`ironbee-dt-browser`) referenced in
  `.cursor/rules/ironbee-devtools-use.mdc` is NOT registered in this session's
  MCP servers, and the rule forbids using any other browser agent as a
  substitute. Verify at the HTTP/HTML layer instead.
- `psycopg2-binary` must be `>=2.9.10` for Python 3.13 wheels
  (2.9.9 has no cp313 wheel and fails to build).

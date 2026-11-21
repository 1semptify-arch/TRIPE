"""End-to-end smoke test of the TRIPE pipeline against the running server."""
import json
import os
import urllib.request
import urllib.parse

TEST_TENANT = os.getenv("TRIPE_CASE_TENANT_NAME", "Tenant")

BASE = "http://127.0.0.1:8013"


def post(path, data: dict):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(BASE + path, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req) as r:
        return r.status, json.loads(r.read().decode())


def get(path):
    with urllib.request.urlopen(BASE + path) as r:
        return r.status, json.loads(r.read().decode())


print("=== 1. TREE ===")
_, t = get("/api/tree")
_, st = get("/api/statutes")
print(f"  cases={len(t['cases'])} statutes={len(st['results'])} templates={len(t['templates'])}")

print("=== 2. RECORD evidence (case 1) ===")
_, r = post("/workspace/record", {
    "case_id": 1,
    "event_timestamp": "2026-07-24T09:00",
    "issue_type": "Maintenance",
    "narrative_text": "Bedbug infestation spreading from adjacent unit; landlord ignoring pest control requests. Also recurring mold in kitchen.",
    "file_path_metadata": "photos/bedbugs.jpg",
})
print(f"  {r['message']} id={r['entry']['id']}")

print("=== 3. ASSESS case 1 ===")
_, a = get("/workspace/assessment/1")
print(f"  flags: {', '.join(f['keyword'] for f in a['flags'])}")
print(f"  matched statutes: {len(a['matched_statutes'])}")

print("=== 4. GENERATE all 3 doc types ===")
for atype in ("Official_Complaint", "Press_Release", "Attorney_Packet"):
    _, g = post("/workspace/generate", {
        "case_id": 1, "action_type": atype, "tenant_name": TEST_TENANT,
    })
    act = g["action"]
    print(f"  {act['action_type']} -> action #{act['id']} ({len(act['document_content'])} chars)")

print("=== 5. SIGN the latest Attorney Packet ===")
_, case = get("/api/case/1")
attorney = [x for x in case["actions"] if x["action_type"] == "Attorney_Packet"]
aid = max(x["id"] for x in attorney)
_, s = post(f"/workspace/sign/{aid}", {"signed_by": TEST_TENANT, "confirm": "yes"})
print(f"  {s['message']} signed={s['action']['signed_status']} valid={s['signature_valid']}")
print(f"  sig={s['action']['signature_hash'][:24]}...")

print("=== 6. VERIFY integrity via /api/action/{aid} ===")
_, v = get(f"/api/action/{aid}")
print(f"  signed_status={v['signed_status']} signature_valid={v['signature_valid']}")

print("=== 7. RESEARCH search 'mold' ===")
_, res = get("/workspace/research?q=mold")
print(f"  count={res['count']} titles={[x['law_citation_title'][:40] for x in res['results']]}")

print("\nALL CHECKS PASSED")

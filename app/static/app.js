/* TRIPE workspace controller — vanilla JS driving the IDE panes via JSON APIs */
(function () {
  "use strict";
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const state = { caseId: null, tree: null, actions: [] };

  // ---- console ----
  const consoleLog = $("#console-log");
  function log(message, kind = "info") {
    const t = new Date().toLocaleTimeString();
    const line = document.createElement("div");
    line.className = `console-line ${kind}`;
    line.innerHTML = `<span class="t">[${t}]</span> <span class="m">${esc(message)}</span>`;
    consoleLog.appendChild(line);
    consoleLog.scrollTop = consoleLog.scrollHeight;
  }
  $("#clear-console").addEventListener("click", () => { consoleLog.innerHTML = ""; });

  // ---- tabs ----
  $$(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      $$(".tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      $$(".tab-body").forEach((b) => b.classList.add("hidden"));
      $("#tab-" + tab.dataset.tab).classList.remove("hidden");
    });
  });

  // ---- tree ----
  async function loadTree() {
    const res = await fetch("/api/tree");
    const data = await res.json();
    state.tree = data;

    // cases
    const casesEl = $("#tree-cases");
    if (!data.cases.length) {
      casesEl.innerHTML = `<div class="tree-empty">no cases — click "+ case"</div>`;
    } else {
      casesEl.innerHTML = data.cases.map(({ case: c }) =>
        `<div class="tree-item" data-case="${c.id}">
           <span class="ic">▣</span><span>${esc(c.title)}</span>
           <span class="badge">${c.evidence_count}ev</span>
         </div>`).join("");
    }

    // evidence folder (per active case)
    renderEvidenceInTree();

    // templates
    $("#tree-templates").innerHTML = data.templates.map((t) =>
      `<div class="tree-item" data-template="${t.action_type}">
         <span class="ic act">▤</span><span>${esc(t.name)}</span>
       </div>`).join("");

    // wire case clicks
    $$("#tree-cases .tree-item").forEach((el) =>
      el.addEventListener("click", () => selectCase(parseInt(el.dataset.case, 10))));
    // template clicks -> jump to generate tab
    $$("#tree-templates .tree-item").forEach((el) =>
      el.addEventListener("click", () => {
        const sel = $("#generate-form select[name=action_type]");
        if (sel) sel.value = el.dataset.template;
        $$(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === "generate"));
        $$(".tab-body").forEach((b) => b.classList.add("hidden"));
        $("#tab-generate").classList.remove("hidden");
      }));
  }

  function renderEvidenceInTree() {
    const el = $("#tree-evidence");
    if (!state.caseId) { el.innerHTML = `<div class="tree-empty">select a case</div>`; return; }
    const node = state.tree.cases.find((n) => n.case.id === state.caseId);
    if (!node) { el.innerHTML = `<div class="tree-empty">select a case</div>`; return; }
    if (!node.evidence.length) {
      el.innerHTML = `<div class="tree-empty">no evidence yet</div>`;
    } else {
      el.innerHTML = node.evidence.map((e) =>
        `<div class="tree-sub" title="${esc(e.narrative_text)}">
           <span class="ic ev">•</span> ${esc(e.event_timestamp.replace("T", " "))} — ${esc(e.issue_type)}
         </div>`).join("");
    }
  }

  // ---- select case ----
  async function selectCase(id) {
    state.caseId = id;
    $$("#tree-cases .tree-item").forEach((el) =>
      el.classList.toggle("active", parseInt(el.dataset.case, 10) === id));
    $("#record-case-id").value = id;
    $("#generate-case-id").value = id;
    $("#run-assessment").disabled = false;

    const res = await fetch(`/api/case/${id}`);
    const data = await res.json();
    state.actions = data.actions;

    const c = data.case;
    $("#active-case-chip").textContent = `case #${c.id}: ${c.title}`;
    $("#case-detail").innerHTML = `
      <dl>
        <dt>Title</dt><dd>${esc(c.title)}</dd>
        <dt>Landlord</dt><dd>${esc(c.landlord_name)}</dd>
        <dt>Property</dt><dd>${esc(c.property_address)}</dd>
        <dt>Status</dt><dd><span class="status-pill status-${esc(c.status)}">${esc(c.status)}</span></dd>
        <dt>Evidence</dt><dd>${data.evidence.length} recorded incident(s)</dd>
        <dt>Actions</dt><dd>${data.actions.length} generated document(s)</dd>
      </dl>`;
    renderEvidenceInTree();
    refreshPreviewSelect();
    log(`Loaded case #${c.id} — "${c.title}" [${c.status}]`, "info");
  }

  // ---- preview select ----
  function refreshPreviewSelect() {
    const sel = $("#preview-action-select");
    const cur = sel.value;
    sel.innerHTML = `<option value="">— select a generated document —</option>` +
      state.actions.map((a) =>
        `<option value="${a.id}">${esc(a.action_type)} #${a.id} ${a.signed_status ? "✓ signed" : ""}</option>`).join("");
    if (cur && state.actions.some((a) => String(a.id) === cur)) sel.value = cur;
  }

  $("#preview-action-select").addEventListener("change", async (e) => {
    const id = parseInt(e.target.value, 10);
    if (!id) { $("#preview-content").innerHTML = `<div class="tree-empty">Generate or select a document to preview.</div>`; $("#sign-card").classList.add("hidden"); return; }
    const res = await fetch(`/api/action/${id}`);
    const a = await res.json();
    $("#preview-status").textContent = a.signed_status ? "SIGNED & LOCKED" : "UNSIGNED";
    $("#preview-status").style.color = a.signed_status ? "var(--green)" : "var(--yellow)";
    let sigBlock = "";
    if (a.signed_status) {
      sigBlock = `<div class="sig-block">
        <div><strong>Signed by:</strong> ${esc(a.signed_by)}</div>
        <div><strong>Signed at:</strong> ${esc(a.signed_at)}</div>
        <div><strong>Signature (SHA-256):</strong> <span class="ok">${esc(a.signature_hash)}</span></div>
        <div><strong>Integrity:</strong> <span class="ok">${a.signature_valid ? "VALID — content unchanged" : "INVALID — content tampered"}</span></div>
      </div>`;
    }
    $("#preview-content").innerHTML = `<pre style="margin:0">${esc(a.document_content)}</pre>${sigBlock}`;
    if (a.signed_status) {
      $("#sign-card").classList.add("hidden");
    } else {
      $("#sign-card").classList.remove("hidden");
      $("#sign-action-id").value = id;
    }
  });

  // ---- record form ----
  $("#record-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!state.caseId) { log("Select a case before recording evidence.", "err"); return; }
    const fd = new FormData(e.target);
    const res = await fetch("/workspace/record", { method: "POST", body: fd });
    const data = await res.json();
    if (res.ok) {
      log(`Evidence recorded → case #${data.entry.case_id} [${data.entry.issue_type}] @ ${data.entry.event_timestamp}`, "ok");
      e.target.reset();
      await loadTree();
      await selectCase(state.caseId);
    } else {
      log(`Record failed: ${data.detail || res.status}`, "err");
    }
  });

  // ---- generate form ----
  $("#generate-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!state.caseId) { log("Select a case before generating.", "err"); return; }
    const fd = new FormData(e.target);
    const res = await fetch("/workspace/generate", { method: "POST", body: fd });
    const data = await res.json();
    if (res.ok) {
      log(`${data.action.action_type} generated → action #${data.action.id} (case #${data.action.case_id})`, "ok");
      await loadTree();
      await selectCase(state.caseId);
      // jump to preview and select the new doc
      $$(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === "preview"));
      $$(".tab-body").forEach((b) => b.classList.add("hidden"));
      $("#tab-preview").classList.remove("hidden");
      $("#preview-action-select").value = String(data.action.id);
      $("#preview-action-select").dispatchEvent(new Event("change"));
    } else {
      log(`Generate failed: ${data.detail || res.status}`, "err");
    }
  });

  // ---- sign form ----
  $("#sign-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = $("#sign-action-id").value;
    if (!id) { log("No document selected to sign.", "err"); return; }
    const fd = new FormData(e.target);
    const res = await fetch(`/workspace/sign/${id}`, { method: "POST", body: fd });
    const data = await res.json();
    if (res.ok) {
      log(`Document #${id} signed & locked by ${data.action.signed_by} — SHA-256 ${data.action.signature_hash.slice(0, 16)}…`, "ok");
      $("#sign-result").innerHTML = `<div class="console-line ok"><span class="m">Locked. Signature: ${esc(data.action.signature_hash)}</span></div>`;
      await loadTree();
      await selectCase(state.caseId);
      $("#preview-action-select").value = String(id);
      $("#preview-action-select").dispatchEvent(new Event("change"));
    } else {
      log(`Sign failed: ${data.detail || res.status}`, "err");
    }
  });

  // ---- statute search ----
  let statuteTimer;
  $("#statute-search").addEventListener("input", (e) => {
    clearTimeout(statuteTimer);
    const q = e.target.value.trim();
    statuteTimer = setTimeout(async () => {
      const url = q ? `/api/statutes?q=${encodeURIComponent(q)}` : "/api/statutes";
      const res = await fetch(url);
      const data = await res.json();
      renderStatutes(data.results, q);
    }, 200);
  });
  function renderStatutes(list, q) {
    const el = $("#statute-results");
    if (!list.length) { el.innerHTML = `<div class="tree-empty">no statutes match</div>`; return; }
    el.innerHTML = list.map((s) => {
      const tags = s.keyword_tags.split(",").map((t) => t.trim()).filter(Boolean);
      const ql = (q || "").toLowerCase();
      const tagHtml = tags.map((t) =>
        `<span class="tag ${ql && t.toLowerCase().includes(ql) ? "match" : ""}">${esc(t)}</span>`).join("");
      return `<div class="statute-card">
        <div class="juris">${esc(s.jurisdiction)}</div>
        <div class="title">${esc(s.law_citation_title)}</div>
        <div class="body">${esc(s.legal_text_body)}</div>
        <div class="tags">${tagHtml}</div>
      </div>`;
    }).join("");
  }

  // ---- assessment ----
  $("#run-assessment").addEventListener("click", async () => {
    if (!state.caseId) return;
    $("#run-assessment").disabled = true;
    log(`Running assessment on case #${state.caseId}…`, "info");
    const res = await fetch(`/api/assessment/${state.caseId}`);
    const data = await res.json();
    $("#run-assessment").disabled = false;
    renderAssessment(data);
    log(`Assessment complete: ${data.flags.length} keyword flag(s), ${data.matched_statutes.length} matched statute(s)`, data.matched_statutes.length ? "ok" : "warn");
  });

  function renderAssessment(data) {
    const el = $("#assessment-results");
    if (data.error) { el.innerHTML = `<div class="assess-empty">${esc(data.error)}</div>`; return; }
    let html = "";
    if (!data.flags.length) {
      html += `<div class="assess-empty">No keywords flagged in evidence log.</div>`;
    } else {
      html += `<div style="margin-bottom:6px;color:var(--muted);font-size:11px;font-family:var(--mono)">FLAGGED KEYWORDS</div>`;
      html += data.flags.map((f) =>
        `<div class="flag-row"><span class="kw">${esc(f.keyword)}</span><span class="cnt">${f.count}×</span></div>`).join("");
    }
    if (data.matched_statutes.length) {
      html += `<div style="margin:10px 0 6px;color:var(--muted);font-size:11px;font-family:var(--mono)">LIKELY VIOLATED LAWS</div>`;
      html += data.matched_statutes.map((m) => {
        const s = m.statute;
        const tags = m.matched_keywords.map((k) => `<span class="tag match">${esc(k)}</span>`).join("");
        return `<div class="statute-card">
          <div class="juris">${esc(s.jurisdiction)}</div>
          <div class="title">${esc(s.law_citation_title)}</div>
          <div class="body">${esc(s.legal_text_body)}</div>
          <div class="tags">${tags}</div>
        </div>`;
      }).join("");
    }
    el.innerHTML = html || `<div class="assess-empty">No matching statutes.</div>`;
  }

  // ---- new case modal ----
  const modal = $("#case-modal");
  $("#new-case-btn").addEventListener("click", () => modal.classList.remove("hidden"));
  $("#case-modal-cancel").addEventListener("click", () => modal.classList.add("hidden"));
  $("#case-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const res = await fetch("/api/cases", { method: "POST", body: fd });
    const data = await res.json();
    if (res.ok) {
      log(`Created case #${data.case.id} — "${data.case.title}"`, "ok");
      modal.classList.add("hidden");
      e.target.reset();
      await loadTree();
      selectCase(data.case.id);
    } else {
      log(`Create case failed: ${data.detail || res.status}`, "err");
    }
  });

  // ---- init ----
  (async function init() {
    log("TRIPE workspace initialized.", "ok");
    await loadTree();
    // load initial statute list
    const res = await fetch("/api/statutes");
    const data = await res.json();
    renderStatutes(data.results, "");
    log(`Loaded ${state.tree.cases.length} case(s) and ${data.results.length} statute reference(s).`, "info");
    // auto-select first case
    if (state.tree.cases.length) selectCase(state.tree.cases[0].case.id);
  })();
})();

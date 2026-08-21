"""A self-contained human-approval page: one HTML file, data inlined.

No server, no fetch, no CDN — it works from file:// on any machine, which is
exactly where an approval gate gets used. Keyboard-driven (j/k move, a approve,
r reject), decisions persist in localStorage, and the export box produces the
JSON the writer consumes as `expected_pre`-carrying approvals.
"""

import html
import json
from pathlib import Path

_PAGE = """<!doctype html>
<meta charset="utf-8">
<title>__TITLE__</title>
<style>
  body { font: 14px/1.5 system-ui, sans-serif; margin: 2rem; max-width: 60rem; }
  table { border-collapse: collapse; width: 100%; }
  td, th { border: 1px solid #ccc; padding: .4rem .6rem; text-align: left; }
  tr.current { outline: 3px solid #4a90d9; }
  tr.approve td:first-child { background: #e2f2e2; }
  tr.reject td:first-child { background: #f6dcdc; }
  textarea { width: 100%; height: 8rem; margin-top: 1rem; }
  .hint { color: #666; }
</style>
<h1>__TITLE__</h1>
<p class="hint">j/k: move &middot; a: approve &middot; r: reject &middot; decisions persist in this browser</p>
<table id="t"><tr><th>decision</th><th>record</th><th>field</th><th>current</th><th>proposed</th></tr></table>
<button onclick="exportDecisions()">Export decisions JSON</button>
<textarea id="out" placeholder="approved changes appear here; paste into your run"></textarea>
<script>
const CHANGES = __DATA__;
const KEY = "review:__TITLE__";
const state = JSON.parse(localStorage.getItem(KEY) || "{}");
let current = 0;
const table = document.getElementById("t");
CHANGES.forEach((c, i) => {
  const fields = Object.keys(c.payload);
  fields.forEach((f, j) => {
    const tr = table.insertRow(-1);
    tr.dataset.idx = i;
    if (j === 0) {
      tr.insertCell(-1).textContent = state[c.record_id] || "";
      const id = tr.insertCell(-1); id.textContent = c.record_id;
    } else { tr.insertCell(-1); tr.insertCell(-1); }
    tr.insertCell(-1).textContent = f;
    tr.insertCell(-1).textContent = JSON.stringify(c.pre[f]);
    tr.insertCell(-1).textContent = JSON.stringify(c.payload[f]);
  });
});
function paint() {
  [...table.rows].forEach(r => {
    if (r.dataset.idx === undefined) return;
    const c = CHANGES[r.dataset.idx];
    r.className = (Number(r.dataset.idx) === current ? "current " : "") + (state[c.record_id] || "");
    if (r.cells[1].textContent) r.cells[0].textContent = state[c.record_id] || "";
  });
  localStorage.setItem(KEY, JSON.stringify(state));
}
document.addEventListener("keydown", e => {
  if (e.key === "j") current = Math.min(current + 1, CHANGES.length - 1);
  if (e.key === "k") current = Math.max(current - 1, 0);
  if (e.key === "a") state[CHANGES[current].record_id] = "approve";
  if (e.key === "r") state[CHANGES[current].record_id] = "reject";
  paint();
});
function exportDecisions() {
  const approved = CHANGES.filter(c => state[c.record_id] === "approve")
    .map(c => ({record_id: c.record_id, payload: c.payload, expected_pre: c.pre}));
  document.getElementById("out").value = JSON.stringify(approved, null, 2);
}
paint();
</script>
"""


def build_page(changes: list[dict], title: str = "Pending writes") -> str:
    # Each change: {"record_id", "payload", "pre"} — pre becomes expected_pre on
    # export, so what the human approved is what the writer will insist on.
    page = _PAGE.replace("__TITLE__", html.escape(title))
    return page.replace("__DATA__", json.dumps(changes))


def write_page(path, changes: list[dict], title: str = "Pending writes") -> None:
    Path(path).write_text(build_page(changes, title), encoding="utf-8")

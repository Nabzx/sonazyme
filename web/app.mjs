// Sonazyme Lab. Presentation only: every value shown here comes from a run
// manifest or from a target artefact, and nothing is computed in this file.

import { listRuns, openRun } from "./lib/api.mjs";
import { displayMetric, notice, stages } from "./lib/data.mjs";
import { TraceViewer } from "./lib/viewer.mjs";

const $ = id => document.getElementById(id);
const el = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};
const clamp01 = value => Math.min(1, Math.max(0, value));
// Ease out, so everything arrives and settles rather than stopping dead.
const settle = value => 1 - Math.pow(1 - clamp01(value), 3);
const between = (now, from, to) => clamp01((now - from) / (to - from));

/* ------------------------------------------------------------------ act 3 */
// Ten seconds, five beats: ping, detect, design, dose, clear.

const OVERHEAD_SECONDS = 10;
const BEATS = [0, 2.1, 3.8, 5.6, 7.6];
const PIPE = { left: 60, right: 1120, labX: 749 };

function overhead(now) {
  const pulse = $("oh-pulse");
  const patch = $("oh-patch");
  const flag = $("oh-flag");
  const lab = $("oh-lab");
  const labDot = $("oh-lab-dot");
  const dose = $("oh-dose");
  const confirm = $("oh-confirm");
  if (!pulse) return;

  // 1. the pulse travels the loop
  const sweep = between(now, 0.1, 2.0);
  pulse.setAttribute("opacity", sweep > 0 && sweep < 1 ? "1" : "0");
  pulse.setAttribute("transform", `translate(${PIPE.left + sweep * (PIPE.right - PIPE.left - 26)} 0)`);

  // 2. it comes back changed, and the fouled patch is where it changed
  const found = between(now, 2.0, 2.9);
  const cleared = between(now, 7.6, 9.0);
  patch.setAttribute("opacity", String(settle(found) * (1 - settle(cleared))));
  flag.setAttribute("opacity", String(settle(between(now, 2.3, 3.0)) * (1 - between(now, 7.4, 8.0))));

  // 3. the enzyme is designed in the module beside the loop
  const designing = between(now, 3.7, 4.4);
  lab.setAttribute("opacity", String(settle(designing) * (1 - between(now, 9.2, 9.9))));
  const pulseDot = 0.25 + 0.55 * Math.abs(Math.sin((now - 3.7) * 3.4));
  labDot.setAttribute("opacity", now > 3.7 && now < 5.8 ? String(pulseDot) : "0.25");

  // 4. it is dosed into the loop and carried downstream
  const dosing = between(now, 5.6, 7.4);
  dose.setAttribute("opacity", dosing > 0 && dosing < 1 ? String(1 - between(now, 7.0, 7.4)) : "0");
  const travel = PIPE.labX - 120 + settle(dosing) * 320;
  dose.setAttribute("transform", `translate(${travel} 0)`);

  // 5. a confirming ping over clean wall
  const check = between(now, 8.4, 9.8);
  confirm.setAttribute("opacity", check > 0 && check < 1 ? "1" : "0");
  confirm.setAttribute("transform", `translate(${PIPE.left + check * (PIPE.right - PIPE.left - 6)} 0)`);

  const active = BEATS.reduce((index, start, i) => (now >= start ? i : index), 0);
  for (const chip of document.querySelectorAll(".beat")) {
    chip.dataset.on = String(Number(chip.dataset.beat) === active);
  }
}

/* ------------------------------------------------------------------ act 1 */
// The problem, on its own loop: the film forms, biocide clears the surface,
// the matrix stays, the film returns.

const PROBLEM_SECONDS = 12;
const CAPTIONS = [
  [0, "1 · the film forms"],
  [3.4, "2 · biocide is dosed"],
  [6.0, "3 · the cells die, the matrix stays"],
  [8.4, "4 · the film grows back on the same anchor"],
];

function problemScene(now) {
  const matrix = $("ps-matrix");
  const cells = $("ps-cells");
  const biocide = $("ps-biocide");
  const caption = $("ps-caption");
  if (!matrix) return;

  const grown = settle(between(now, 0.3, 3.0));
  const regrown = settle(between(now, 8.4, 11.0));
  const killed = between(now, 4.2, 5.4);

  matrix.setAttribute("opacity", String(Math.max(grown, 0.85)));
  cells.setAttribute("opacity", String(Math.max(grown * (1 - killed), regrown)));

  const dosing = between(now, 3.4, 5.2);
  biocide.setAttribute("width", String(dosing > 0 && dosing < 1 ? 540 * settle(dosing) : 0));
  biocide.setAttribute("opacity", String(0.14 * (1 - between(now, 5.0, 5.6))));

  const line = CAPTIONS.reduce((found, [at, text]) => (now >= at ? text : found), CAPTIONS[0][1]);
  if (caption.textContent !== line) caption.textContent = line;
}

function startScenes() {
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduced) {
    overhead(9.5);
    problemScene(7.0);
    return;
  }
  const started = performance.now();
  const frame = stamp => {
    const seconds = (stamp - started) / 1000;
    overhead(seconds % OVERHEAD_SECONDS);
    problemScene(seconds % PROBLEM_SECONDS);
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
}

/* ---------------------------------------------------------------- reveals */

function revealOnScroll() {
  const items = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window)) {
    items.forEach(item => (item.dataset.shown = "true"));
    return;
  }
  const watcher = new IntersectionObserver(
    entries => entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.dataset.shown = "true";
        watcher.unobserve(entry.target);
      }
    }),
    { rootMargin: "-10% 0px -10% 0px" },
  );
  items.forEach(item => watcher.observe(item));
}

/* ------------------------------------------------------------ provenance */
// An evidence record is {basis, value, source, reason}. The basis decides the
// tag, and a record with no value says so rather than being left blank.

function evidenceTag(record) {
  const basis = record?.basis;
  // Identity read straight from the manifest, not an evidence claim.
  if (basis === "code") return el("span", "tag", "From run");
  if (basis === "literature" || basis === "measurement") {
    const tag = el("span", "tag tag--cited", "Cited");
    if (record.source) tag.title = record.source;
    return tag;
  }
  if (basis === "assumption") return el("span", "tag tag--assumed", "Assumed");
  return el("span", "tag", "Not supplied");
}

function evidenceValue(record) {
  const value = record?.value;
  if (Array.isArray(value)) return value.join(", ");
  if (value === undefined || value === null) return "not supplied";
  return String(value);
}

function addRow(parent, label, record) {
  const row = el("div", "row");
  row.append(el("span", "row__label", label));
  const value = el("span", "row__value");
  value.append(el("span", null, evidenceValue(record)), " ", evidenceTag(record));
  if (record?.reason) row.title = record.reason;
  row.append(value);
  parent.append(row);
}

/* ---------------------------------------------------------------- the run */

function renderLedger(manifest) {
  const ledger = $("ledger");
  ledger.replaceChildren();
  for (const stage of stages) {
    const entry = [...manifest.entries].reverse().find(item => item.stage === stage);
    const row = el("div", "ledger__item");
    row.dataset.status = entry ? entry.status : "absent";
    const pip = el("span", "pip");
    pip.dataset.status = entry ? entry.status : "absent";
    row.append(pip, el("span", "ledger__name", stage));
    row.append(el("span", "ledger__producer",
      entry ? `${entry.producer.name} · ${entry.producer.version}` : "not run"));
    if (entry?.reason) row.title = entry.reason;
    ledger.append(row);
  }
}

function renderMetrics(manifest, rows) {
  let shown = 0;
  for (const entry of manifest.entries) {
    for (const metric of entry.metrics) {
      const display = displayMetric(metric, entry);
      if (!display) continue;
      const row = el("div", "row");
      row.append(el("span", "row__label", display.name));
      const value = el("span", "row__value");
      value.append(el("span", null, `${display.value} ${display.unit}`), " ",
        el("span", "tag", display.citation));
      row.append(value);
      rows.append(row);
      shown += 1;
    }
  }
  return shown;
}

async function renderRun() {
  const rows = $("run-rows");
  const shortlist = $("shortlist");
  const emptyViewer = $("viewer-empty");
  const detail = $("viewer-empty-detail");

  let runs;
  try {
    runs = await listRuns();
  } catch {
    rows.append(el("p", "stage__empty", "The local run service is not running. Start it with: python -m sonazyme.api"));
    emptyViewer.hidden = false;
    return;
  }

  const available = (runs.runs || []).filter(run => run.key && !run.reason);
  if (!available.length) {
    rows.append(el("div", "row", "No saved run to read yet."));
    emptyViewer.hidden = false;
    return;
  }

  const source = await openRun(available[0]);
  const manifest = source.manifest;

  // The target artefact is the file the run was given, in its original format.
  // The resolved record, with its evidence, is what `sense` wrote.
  const sensed = manifest.entries.find(entry => entry.stage === "sense" && entry.status === "succeeded");
  if (!sensed || !sensed.artefacts.length) {
    rows.append(el("div", "row", "This run has no sense record to read."));
    emptyViewer.hidden = false;
    return;
  }
  const target = await source.json(sensed.artefacts[0]);

  addRow(rows, "run", { basis: "code", value: manifest.run_id });
  addRow(rows, "status", { basis: "code", value: manifest.status });
  addRow(rows, "target", { basis: "code", value: target.target?.name });
  addRow(rows, "loop", target.target?.loop);
  addRow(rows, "community", target.community);
  const anchor = (target.anchor || [])[0];
  if (anchor) {
    addRow(rows, "anchor", anchor.component);
    addRow(rows, "enzyme family", anchor.enzyme_family);
  }
  for (const [key, label] of [["temperature_c", "temperature"], ["ph", "pH"],
    ["chemistry", "chemistry"], ["residence_time_s", "contact time"]]) {
    addRow(rows, label, target.envelope?.[key]);
  }
  renderMetrics(manifest, rows);

  renderLedger(manifest);

  const ranked = manifest.entries.find(entry => entry.stage === "rank" && entry.status === "succeeded");
  shortlist.replaceChildren(el("p", "row__label", ranked
    ? "Shortlist entries are listed above with the model behind each number."
    : "No ranked shortlist in this run. The design, fold and score stages have not run, so there is nothing to rank and nothing is shown in their place."));

  const folded = manifest.entries.find(entry => entry.stage === "fold" && entry.status === "succeeded");
  if (!folded || !folded.artefacts.length) {
    emptyViewer.hidden = false;
    $("viewer-reset").disabled = true;
    detail.textContent = "The fold stage has not run in this run, so there are no predicted coordinates to show. This panel stays empty rather than showing a stand-in protein.";
    return;
  }

  const viewer = new TraceViewer($("viewer"));
  $("viewer-reset").addEventListener("click", () => viewer.reset());
  try {
    const structure = await source.json(folded.artefacts[0]);
    viewer.set(structure.points || [], structure.active_site || [], structure.changed || []);
  } catch {
    emptyViewer.hidden = false;
    detail.textContent = "The predicted structure in this run could not be verified against its digest, so it is not drawn.";
  }
}

/* ------------------------------------------------------------------ start */

$("notice").textContent = notice;
revealOnScroll();
startScenes();
renderRun();

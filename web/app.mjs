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
  // If the observer never fires, for any reason, nothing stays invisible on stage.
  setTimeout(() => items.forEach(item => (item.dataset.shown = "true")), 2500);
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

/* ------------------------------------------------------- the loop survey */
// A simulated survey (ADR-0013). Every number here is the forward model's,
// and the panel says so rather than implying an instrument.

const MAX_FILM_UM = 500;

const SVG = "http://www.w3.org/2000/svg";
const svg = (tag, attributes) => {
  const node = document.createElementNS(SVG, tag);
  for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, String(value));
  return node;
};

// The bar is drawn with attributes rather than inline style: the dashboard is
// served under a content security policy that forbids inline styles.
function pipeBar(section, estimate) {
  const height = 26;
  const frame = svg("svg", { viewBox: `0 0 100 ${height}`, class: "pipe", preserveAspectRatio: "none" });
  frame.append(svg("rect", { x: 0, y: 0, width: 100, height, rx: 3, class: "pipe__water" }));
  const thickness = estimate?.film_thickness_um;
  if (typeof thickness === "number") {
    const share = value => Math.min(height, (value / MAX_FILM_UM) * height);
    const filled = share(thickness);
    frame.append(
      svg("rect", {
        x: 0,
        y: height - filled,
        width: 100,
        height: filled,
        class: "pipe__film",
        "data-layer": estimate.layer || "undetermined",
      }),
    );
    const [low, high] = estimate.interval_um || [thickness, thickness];
    frame.append(
      svg("line", {
        x1: 0, x2: 100,
        y1: height - share(high), y2: height - share(high),
        class: "pipe__interval",
      }),
      svg("line", {
        x1: 0, x2: 100,
        y1: height - share(low), y2: height - share(low),
        class: "pipe__interval",
      }),
    );
  }
  if (section.sensor) {
    frame.append(svg("rect", { x: 4, y: 0, width: 14, height: 3, class: "pipe__sensor" }));
  }
  return frame;
}

function sectionRow(section, observation) {
  const row = el("div", "section-row");
  const label = el("div");
  label.append(el("div", "section-row__name", section.id));
  label.append(el("div", "section-row__role", section.role));
  row.append(label);

  const estimate = observation?.estimate || {};
  row.append(pipeBar(section, estimate));

  const thickness = estimate.film_thickness_um;
  const value = el("div", "section-row__estimate");
  if (typeof thickness === "number") {
    const [low, high] = estimate.interval_um || [thickness, thickness];
    value.append(el("div", null, `${thickness} um`));
    value.append(el("div", "section-row__role", `${low} to ${high}`));
  } else {
    value.dataset.undetermined = "true";
    value.textContent = "undetermined";
    if (estimate.reason) value.title = estimate.reason;
  }
  row.append(value);
  return row;
}

function renderLoopMap(loop, reading) {
  const host = $("loopmap");
  host.replaceChildren();
  if (!loop || !reading) {
    host.append(el("p", "empty", "No survey in this run."));
    return;
  }
  const byId = new Map(reading.observation.map(item => [item.section_id, item]));
  const head = el("div", "section-row");
  head.append(
    el("div", "section-row__role", loop.name),
    el("div", "section-row__role", "estimated layer on the inner wall"),
    el("div", "section-row__role", "thickness"),
  );
  host.append(head);
  for (const section of loop.section) host.append(sectionRow(section, byId.get(section.id)));
  host.append(el("p", "section-row__role", reading.basis_reason));
}

function renderBeforeAfter(loop, before, after) {
  const host = $("survey");
  host.replaceChildren();
  if (!before) {
    host.append(el("p", "empty",
      "No acoustic survey in this run. A reading would say where the film is and how sure the model is about it."));
    return;
  }
  host.append(el("p", "empty", before.basis_reason));
  if (!after) return;
  const panel = el("div", "beforeafter");
  const first = new Map(before.observation.map(item => [item.section_id, item]));
  const second = new Map(after.observation.map(item => [item.section_id, item]));
  const show = item => {
    const value = item?.estimate?.film_thickness_um;
    return typeof value === "number" ? `${value} um` : "undetermined";
  };
  for (const section of loop.section) {
    const a = first.get(section.id);
    const b = second.get(section.id);
    if (!a || !b) continue;
    if (a.estimate.film_thickness_um === null && b.estimate.film_thickness_um === null) continue;
    const row = el("div", "beforeafter__row");
    row.append(el("span", null, section.id));
    row.append(el("span", "beforeafter__value", show(a)));
    row.append(el("span", "beforeafter__arrow", "\u2192"));
    row.append(el("span", "beforeafter__value beforeafter__value--after", show(b)));
    panel.append(row);
  }
  if (panel.childElementCount) {
    host.append(panel);
    host.append(el("p", "section-row__role",
      "Two simulated surveys of the same loop. Nothing here says a treatment caused the change."));
  }
}

/* -------------------------------------------------------------- variants */
// Designs as the run recorded them. A rejected variant stays visible with its
// reason, because a search that only shows winners is not showing a search.

function renderVariants(manifest) {
  const host = $("variants");
  host.replaceChildren();
  const designed = manifest.entries.filter(entry => entry.stage === "design");
  if (!designed.length) {
    host.append(el("p", "empty",
      "No design stage in this run. When Tamarind Bio returns variants they appear here as they are scored, rejects included."));
    return 0;
  }
  for (const entry of designed) {
    const row = el("div", "variant");
    row.dataset.status = entry.status;
    const pip = el("span", "pip");
    pip.dataset.status = entry.status;
    const mutations = entry.parameters?.mutations;
    row.append(pip, el("span", "variant__mutations",
      Array.isArray(mutations) && mutations.length ? mutations.join(" + ") : entry.id));
    const metric = entry.metrics.map(item => displayMetric(item, entry)).find(Boolean);
    row.append(el("span", "row__value", metric ? `${metric.value} ${metric.unit}` : ""));
    if (entry.status !== "succeeded" && entry.reason) {
      row.append(el("span", "variant__reason", entry.reason));
    }
    host.append(row);
  }
  return designed.length;
}

/* ------------------------------------------------------ the walkthrough */
// Four steps over the same run. A step with no data in this run says so
// rather than being skipped or filled in.

const STEPS = [
  { name: "The loop", caption: () => captions.loop },
  { name: "The chassis", caption: () => captions.chassis },
  { name: "The designs", caption: () => captions.designs },
  { name: "The pick", caption: () => captions.pick },
];

const captions = {
  loop: ["Reading the loop", "Loading the run."],
  chassis: ["The enzyme we start from", "Loading the run."],
  designs: ["Designs, scored", "Loading the run."],
  pick: ["The pick, and what it trades", "Loading the run."],
};

let currentStep = 0;
let playing = false;
let timer = null;

function paintStep(index) {
  currentStep = (index + STEPS.length) % STEPS.length;
  for (const button of document.querySelectorAll(".step")) {
    const step = Number(button.dataset.step);
    button.dataset.on = String(step === currentStep);
    button.dataset.done = String(step < currentStep);
  }
  const viewport = $("viewport");
  if (viewport) viewport.dataset.view = currentStep === 0 ? "loop" : "structure";
  const box = $("stage-caption");
  if (!box) return;
  const [title, body] = STEPS[currentStep].caption();
  box.dataset.swapping = "true";
  setTimeout(() => {
    box.replaceChildren(el("strong", null, title), el("p", null, body));
    box.dataset.swapping = "false";
  }, 160);
}

function setPlaying(next) {
  playing = next;
  const button = $("step-play");
  button.dataset.playing = String(playing);
  button.textContent = playing ? "Pause" : "Play";
  clearInterval(timer);
  if (playing) timer = setInterval(() => paintStep(currentStep + 1), 6500);
}

function walkthrough() {
  const viewport = document.querySelector(".stage__viewport");
  const box = el("div", "stage__caption");
  box.id = "stage-caption";
  viewport.append(box);

  for (const button of document.querySelectorAll(".step")) {
    button.addEventListener("click", () => { setPlaying(false); paintStep(Number(button.dataset.step)); });
  }
  $("step-next").addEventListener("click", () => { setPlaying(false); paintStep(currentStep + 1); });
  $("step-back").addEventListener("click", () => { setPlaying(false); paintStep(currentStep - 1); });
  $("step-play").addEventListener("click", () => setPlaying(!playing));
  paintStep(0);
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

  rows.replaceChildren();
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
  const designCount = renderVariants(manifest);

  // Simulated loop surveys, in the order the run recorded them (ADR-0013).
  const surveys = manifest.entries.filter(
    entry => entry.stage === "sense" && entry.status === "succeeded"
      && entry.producer.name.includes("acoustic") && entry.artefacts.length,
  );
  const readings = [];
  for (const entry of surveys) {
    try {
      readings.push({ entry, record: await source.json(entry.artefacts[0]) });
    } catch {
      // A reading that cannot be verified is simply not shown.
    }
  }
  const loopMap = surveys.length ? surveys[0].parameters.loop : null;
  renderLoopMap(loopMap, readings[0]?.record);
  renderBeforeAfter(loopMap, readings[0]?.record, readings[1]?.record);

  // The walkthrough says what this run actually holds, step by step.
  const anchorValue = anchor ? evidenceValue(anchor.component) : "not named";
  const supplied = ["temperature_c", "ph", "chemistry", "residence_time_s"]
    .filter(key => target.envelope?.[key]?.basis && target.envelope[key].basis !== "unknown").length;
  const fouled = (readings[0]?.record.observation || []).filter(
    item => typeof item.estimate.film_thickness_um === "number",
  ).length;
  captions.loop = readings.length
    ? [
        `${loopMap.name}, simulated survey`,
        `${fouled} of ${loopMap.section.length} sections return a layer the model can size. `
          + "Every number here is from the forward model, not from an instrument.",
      ]
    : [
    `${target.target?.name || "This run"}`,
    `Anchor: ${anchorValue}. ${supplied
      ? `${supplied} of four envelope values supplied.`
      : "No envelope value is supplied, so nothing here claims the conditions inside a loop."}`,
  ];

  const chassisEntry = manifest.entries.find(entry => entry.stage === "chassis" && entry.status === "succeeded");
  let chassisRecord = null;
  if (chassisEntry?.artefacts.length) {
    try { chassisRecord = await source.json(chassisEntry.artefacts[0]); } catch { chassisRecord = null; }
  }
  captions.chassis = chassisRecord
    ? [chassisRecord.name || "The chassis",
       `${chassisRecord.selection_reason || "Selected for this anchor."}${
         chassisRecord.design_ready === false ? " Not marked design ready." : ""}`]
    : ["No chassis in this run", "The chassis stage has not run, so there is nothing to start from."];

  captions.designs = designCount
    ? [`${designCount} design${designCount === 1 ? "" : "s"} in this run`,
       "Each carries its mutation set and the model that scored it. Rejected designs stay listed with their reason."]
    : ["No designs yet",
       "The design stage has not run. When it does, variants arrive here as they are scored, and the ones that fail the active-site check stay visible with their reason."];

  paintStep(currentStep);

  const ranked = manifest.entries.find(entry => entry.stage === "rank" && entry.status === "succeeded");
  captions.pick = ranked
    ? ["The pick", "Ranked on stability, activity and confidence, with the trade-off shown rather than blended away."]
    : ["Nothing ranked yet",
       "Design, fold and score have not run, so there is no shortlist. The panel stays empty rather than showing a placeholder candidate."];
  paintStep(currentStep);

  shortlist.replaceChildren(el("p", "empty", ranked
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
walkthrough();
renderRun();

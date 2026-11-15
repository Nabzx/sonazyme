// The demo: the original enzyme and the variants that came out of the run.
// Everything here is read from the saved run through the API. No structure,
// score or sequence is written into this file.
import { listRuns, openRun } from "./api.mjs";
import { TraceViewer } from "./viewer.mjs";

// Residue classes, for reading the sequence rather than for any claim about it.
const CLASS = new Map();
for (const [name, letters] of [
  ["acidic", "DE"],
  ["basic", "KRH"],
  ["polar", "STNQY"],
  ["hydro", "AVLIMFW"],
  ["special", "CGP"],
]) {
  for (const letter of letters) CLASS.set(letter, name);
}

const SNAPSHOT_SPAN = 7;

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function metricsOf(entry) {
  const found = new Map();
  for (const metric of entry.metrics || []) found.set(metric.name, metric);
  return found;
}

function number(metric, digits = 2) {
  if (!metric || typeof metric.value !== "number") return null;
  return metric.value.toFixed(digits);
}

// The fold entries, split into the parent and the variants, by what the run
// recorded as changed rather than by anything guessed from the name.
function foldEntries(manifest) {
  const folds = manifest.entries.filter(e => e.stage === "fold" && e.status === "succeeded");
  return {
    parent: folds.find(e => !(e.parameters?.changed || []).length) ?? folds[0],
    variants: folds.filter(e => (e.parameters?.changed || []).length),
  };
}

function renderSequence(target, sequence, { site = [], start = 1, changed = [] } = {}) {
  target.replaceChildren();
  const marked = new Set(site);
  const edited = new Set(changed);
  for (let index = 0; index < sequence.length; index += 1) {
    const position = start + index;
    const letter = sequence[index];
    const node = el("span", "fasta__aa", letter);
    node.dataset.class = CLASS.get(letter) || "other";
    if (marked.has(position)) node.dataset.role = "site";
    if (edited.has(position)) node.dataset.role = "changed";
    node.title = `${letter}${position}`;
    target.append(node);
  }
}

// A window of the chain around the substitution, so the change is readable.
function snapshot(record, position) {
  const points = record.points;
  const first = points[0]?.position ?? 1;
  const index = position - first;
  const from = Math.max(0, index - SNAPSHOT_SPAN);
  const to = Math.min(record.sequence.length, index + SNAPSHOT_SPAN + 1);
  const wrap = el("div", "snap");
  if (from > 0) wrap.append(el("span", "snap__ellipsis", "…"));
  for (let i = from; i < to; i += 1) {
    const letter = record.sequence[i];
    const node = el("span", "snap__aa", letter);
    node.dataset.class = CLASS.get(letter) || "other";
    if (first + i === position) node.dataset.role = "changed";
    node.title = `${letter}${first + i}`;
    wrap.append(node);
  }
  if (to < record.sequence.length) wrap.append(el("span", "snap__ellipsis", "…"));
  return wrap;
}

function card(entry, record, label) {
  const figure = el("figure", "variant");
  const stage = el("div", "variant__stage");
  const canvas = el("canvas", "variant__canvas");
  canvas.tabIndex = 0;
  canvas.setAttribute("role", "img");
  canvas.setAttribute("aria-label", `Predicted structure of ${label}. Drag to turn it.`);
  stage.append(canvas);
  figure.append(stage);

  const caption = el("figcaption", "variant__foot");
  caption.append(el("p", "variant__name", label));

  const found = metricsOf(entry);
  const ddg = number(found.get("thermompnn_ddg"));
  const rmsd = number(found.get("backbone_rmsd_to_wild_type"));
  const site = number(found.get("catalytic_rmsd_to_wild_type"));
  const plddt = found.get("plddt");

  const stats = el("dl", "variant__stats");
  for (const [key, value, unit] of [
    ["ddG", ddg, "kcal/mol"],
    ["Backbone", rmsd, "Å"],
    ["Active site", site, "Å"],
    ["pLDDT", plddt ? (plddt.value * 100).toFixed(0) : null, ""],
  ]) {
    if (value === null) continue;
    stats.append(el("dt", "variant__k", key));
    stats.append(el("dd", "variant__v", unit ? `${value} ${unit}` : value));
  }
  caption.append(stats);
  figure.append(caption);
  return { figure, canvas };
}

export async function mountDemo(root) {
  const gallery = root.querySelector('[data-demo="gallery"]');
  const wildCanvas = root.querySelector('[data-demo="wildtype"]');
  const fasta = root.querySelector('[data-demo="fasta"]');
  const countNode = root.querySelector('[data-demo="residue-count"]');
  const provenance = root.querySelector('[data-demo="wt-provenance"]');

  const { runs } = await listRuns();
  if (!runs.length) throw new Error("No saved run is available to read.");
  const run = await openRun(runs[0]);
  const { parent, variants } = foldEntries(run.manifest);
  if (!parent) throw new Error("The saved run holds no folded structure.");

  const parentRecord = await run.json(parent.artefacts[0]);
  const site = parentRecord.active_site || [];

  // The original enzyme.
  if (wildCanvas) {
    const viewer = new TraceViewer(wildCanvas);
    viewer.set(parentRecord.points, site, []);
  }
  if (fasta) {
    const first = parentRecord.points[0]?.position ?? 1;
    renderSequence(fasta, parentRecord.sequence, { site, start: first });
  }
  if (countNode) countNode.textContent = String(parentRecord.residue_count);
  if (provenance) {
    provenance.textContent = `${parentRecord.producer.name} ${parentRecord.producer.version}`;
  }

  // The variants, in the order the run recorded them.
  if (!gallery) return;
  gallery.replaceChildren();
  if (!variants.length) {
    gallery.append(el("p", "variants__loading", "This run holds no variant structures."));
    return;
  }
  for (const entry of variants) {
    const record = await run.json(entry.artefacts[0]);
    const position = (entry.parameters.changed || [])[0];
    const index = record.points.findIndex(point => point.position === position);
    const mutant = index >= 0 ? record.sequence[index] : "?";
    const parentIndex = parentRecord.points.findIndex(point => point.position === position);
    const wild = parentIndex >= 0 ? parentRecord.sequence[parentIndex] : "?";
    const label = `${wild}${position}${mutant}`;

    const { figure, canvas } = card(entry, record, label);
    figure.querySelector(".variant__foot").append(snapshot(record, position));
    gallery.append(figure);
    const viewer = new TraceViewer(canvas);
    viewer.set(record.points, site, [position]);
  }
}

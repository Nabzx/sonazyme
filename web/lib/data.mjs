// Presentation guards only. This module computes no scientific score.
export const stages = ["sense", "chassis", "design", "fold", "score", "rank", "explain"];
export const notice = "No Sonazyme wet-lab result. Predictions are not measurements.";
const nonempty = value => typeof value === "string" && value.trim().length > 0;

export function references(manifest) {
  return [manifest.target, ...manifest.entries.flatMap(entry => entry.artefacts)];
}

export function validateReference(ref) {
  if (!ref || !/^[a-f0-9]{64}$/.test(ref.sha256) || ref.path !== `artefacts/${ref.sha256}` ||
      !Number.isSafeInteger(ref.size_bytes) || ref.size_bytes < 0) {
    throw new Error("Invalid artefact reference");
  }
}

export function validateManifest(manifest) {
  if (!manifest || manifest.schema_version !== 1 || !nonempty(manifest.run_id) ||
      !["running", "finished"].includes(manifest.status) || !Array.isArray(manifest.entries)) {
    throw new Error("Unsupported or incomplete run manifest");
  }
  validateReference(manifest.target);
  const ids = new Set();
  for (const entry of manifest.entries) {
    if (!nonempty(entry.id) || ids.has(entry.id) || !stages.includes(entry.stage) ||
        !["succeeded", "failed", "rejected"].includes(entry.status) ||
        !entry.producer || !nonempty(entry.producer.name) || !nonempty(entry.producer.version) ||
        !["code", "model"].includes(entry.producer.kind) ||
        !Array.isArray(entry.inputs) || entry.inputs.some(id => !ids.has(id)) ||
        !Array.isArray(entry.artefacts) || !Array.isArray(entry.metrics) ||
        !entry.parameters || typeof entry.parameters !== "object" || Array.isArray(entry.parameters)) {
      throw new Error("Invalid stage record or missing provenance");
    }
    if (entry.status !== "succeeded" && (!nonempty(entry.reason) || entry.metrics.length)) {
      throw new Error("Failed entries require a reason and cannot carry success metrics");
    }
    entry.artefacts.forEach(validateReference);
    ids.add(entry.id);
  }
  return manifest;
}

export function displayMetric(metric, entry) {
  if (entry.status !== "succeeded") return null;
  // No scoring evidence format is agreed yet. A version string alone never
  // authorises a stability score on the dashboard.
  if (entry.stage === "score") return null;
  if (!metric || typeof metric.value !== "number" || !Number.isFinite(metric.value) ||
      !nonempty(metric.name) || !nonempty(metric.unit)) return null;
  if (metric.basis === "prediction") {
    const model = entry.producer;
    if (model.kind !== "model" || !nonempty(model.name) || !nonempty(model.version) ||
        metric.source?.name !== model.name || metric.source?.version !== model.version ||
        metric.source?.kind !== "model") return null;
    return { ...metric, label: "Prediction", citation: `${model.name} · ${model.version}` };
  }
  if (metric.basis === "measurement" && nonempty(metric.source)) {
    return { ...metric, label: "Cited measurement", citation: metric.source };
  }
  return null;
}

export function evidenceValue(record) {
  const allowed = ["unknown", "assumption", "literature", "guidance", "measurement"];
  if (!record || !allowed.includes(record.basis)) return { basis: "missing", value: "Not recorded", detail: "No evidence record" };
  if (record.basis === "unknown") return { basis: "unknown", value: "Not established", detail: record.reason || "No reason recorded" };
  if (record.basis === "assumption" && !nonempty(record.reason)) return { basis: "missing", value: "Withheld", detail: "Assumption reason missing" };
  if (["literature", "guidance", "measurement"].includes(record.basis) && !nonempty(record.source)) return { basis: "missing", value: "Withheld", detail: "Source missing" };
  if (!("value" in record)) return { basis: "missing", value: "Not recorded", detail: "Value missing" };
  const value = Array.isArray(record.value) ? (record.value.length ? record.value.join(" · ") : "None listed") : String(record.value);
  return { basis: record.basis, value, detail: record.reason || record.source, source: record.source };
}

export function latestEntry(manifest, stage) {
  return [...manifest.entries].reverse().find(entry => entry.stage === stage) || null;
}

export function safeLink(value) {
  try {
    const url = new URL(value);
    return ["https:", "http:"].includes(url.protocol) ? url.href : null;
  } catch { return null; }
}

export function parseTrace(text, sequence) {
  if (typeof sequence !== "string" || !/^[ACDEFGHIKLMNPQRSTVWY]+$/.test(sequence)) throw new Error("Structure input sequence is missing");
  const amino = { ALA:"A", ARG:"R", ASN:"N", ASP:"D", CYS:"C", GLN:"Q", GLU:"E", GLY:"G", HIS:"H", ILE:"I", LEU:"L", LYS:"K", MET:"M", PHE:"F", PRO:"P", SER:"S", THR:"T", TRP:"W", TYR:"Y", VAL:"V" };
  const points = new Map();
  let models = 0;
  for (const line of text.split(/\r?\n/)) {
    if (line.startsWith("MODEL ") && ++models > 1) throw new Error("Multiple structure models are not supported");
    if (!line.startsWith("ATOM  ") || line[21] !== "A" || line.slice(12, 16).trim() !== "CA") continue;
    const position = Number(line.slice(22, 26));
    const xyz = [30, 38, 46].map(start => Number(line.slice(start, start + 8)));
    if (line[16] !== " " || line[26] !== " " || !Number.isInteger(position) || position < 1 ||
        position > sequence.length || sequence[position - 1] !== amino[line.slice(17, 20)] ||
        points.has(position) || xyz.some(value => !Number.isFinite(value))) {
      throw new Error("Coordinates do not match the recorded sequence");
    }
    points.set(position, { position, xyz });
  }
  if (points.size !== sequence.length) throw new Error("Incomplete alpha-carbon trace");
  return [...points.values()].sort((a, b) => a.position - b.position);
}

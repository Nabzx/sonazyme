import { references, validateManifest, validateReference } from "./data.mjs";

const decoder = new TextDecoder("utf-8", { fatal: true });
export async function checkedJSON(response) {
  if (!response.ok) throw new Error(response.status === 409 ? "The saved run could not be verified. Check its manifest and artefacts." : "Could not read the local run service.");
  return response.json();
}

export async function listRuns() {
  return checkedJSON(await fetch("/api/runs", { cache: "no-store" }));
}

export async function verifyBytes(bytes, ref) {
  validateReference(ref);
  if (bytes.byteLength !== ref.size_bytes) throw new Error("Artefact length mismatch");
  if (!globalThis.crypto?.subtle) throw new Error("Use the local dashboard URL to verify artefacts securely.");
  const hash = [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))].map(v => v.toString(16).padStart(2, "0")).join("");
  if (hash !== ref.sha256) throw new Error("Artefact digest mismatch");
  return new Uint8Array(bytes);
}

function source(manifest, read, metadata, snapshotURL = null) {
  const refs = new Map(references(manifest).map(ref => [ref.sha256, ref]));
  const cached = new Map();
  async function bytes(ref) {
    const canonical = refs.get(ref.sha256);
    if (!canonical || canonical.path !== ref.path || canonical.size_bytes !== ref.size_bytes) throw new Error("Artefact is not referenced by this manifest");
    if (!cached.has(ref.sha256)) cached.set(ref.sha256, read(ref).then(data => verifyBytes(data, ref)));
    return cached.get(ref.sha256);
  }
  return {
    manifest, metadata, snapshotURL, bytes,
    text: async ref => decoder.decode(await bytes(ref)),
    json: async ref => JSON.parse(decoder.decode(await bytes(ref))),
  };
}

export async function openRun(run) {
  const base = `/api/runs/${encodeURIComponent(run.key)}`;
  const manifest = validateManifest(await checkedJSON(await fetch(`${base}/manifest`, { cache: "no-store" })));
  return source(manifest, async ref => {
    const response = await fetch(`${base}/artefacts/${ref.sha256}`, { cache: "no-store" });
    if (!response.ok) throw new Error("An artefact is missing or cannot be verified");
    return response.arrayBuffer();
  }, { file_modified_at: run.file_modified_at }, `${base}/snapshot`);
}

export async function openSnapshot(snapshot) {
  if (!snapshot || snapshot.kind !== "sonazyme-snapshot" || snapshot.schema_version !== 1 ||
      !snapshot.artefacts || typeof snapshot.artefacts !== "object") throw new Error("Unsupported snapshot file");
  const manifest = validateManifest(snapshot.manifest);
  const result = source(manifest, async ref => {
    const encoded = snapshot.artefacts[ref.sha256];
    if (typeof encoded !== "string") throw new Error("Snapshot is missing a referenced artefact");
    return Uint8Array.from(atob(encoded), character => character.charCodeAt(0)).buffer;
  }, snapshot.metadata || {});
  // An uploaded snapshot is accepted only after checking its entire chain.
  await Promise.all(references(manifest).map(ref => result.bytes(ref)));
  return result;
}

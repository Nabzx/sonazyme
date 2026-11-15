const $ = (selector, root) => root.querySelector(selector);
const structureCache = new Map();
const BLUE = [33, 102, 172];
const WHITE = [247, 247, 247];
const RED = [178, 24, 43];

function confidenceColour(value) {
  const score = Math.max(0, Math.min(100, value));
  const from = score < 50 ? BLUE : WHITE;
  const to = score < 50 ? WHITE : RED;
  const amount = score < 50 ? score / 50 : (score - 50) / 50;
  const hex = from.reduce((result, channel, index) => {
    const mixed = Math.round(channel + (to[index] - channel) * amount);
    return result + mixed.toString(16).padStart(2, "0");
  }, "");
  return Number.parseInt(hex, 16);
}

async function responseError(response) {
  let body;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (body && typeof body.error === "string") return body.error;
  return `Could not read the local structure service (HTTP ${response.status}).`;
}

async function structureText(structure) {
  if (!structureCache.has(structure.id)) {
    const request = fetch(`/local-structures/${structure.id}`, { cache: "no-store" }).then(
      async (response) => {
        if (!response.ok) throw new Error(await responseError(response));
        return response.text();
      },
    );
    structureCache.set(structure.id, request);
    request.catch(() => structureCache.delete(structure.id));
  }
  return structureCache.get(structure.id);
}

export async function mountLocalStructures(root = document) {
  const panel = $("[data-local-structures]", root);
  if (!panel) return;

  const groupSelect = $("[data-local-structure-group]", panel);
  const fileSelect = $("[data-local-structure-file]", panel);
  const status = $("[data-local-structure-status]", panel);
  const loading = $("[data-local-structure-loading]", panel);
  const errorNode = $("[data-local-structure-error]", panel);
  const confidenceNote = $("[data-local-structure-confidence]", panel);
  const viewerNode = $("[data-local-structure-viewer]", panel);
  const groupsByName = new Map();
  let viewer = null;
  let activeRequest = 0;

  function showError(error) {
    errorNode.textContent = error instanceof Error ? error.message : String(error);
    errorNode.hidden = false;
    loading.hidden = true;
  }

  function clearViewer() {
    viewer?.removeAllModels();
    viewer?.render();
  }

  function getViewer() {
    const library = window["3Dmol"] || window.$3Dmol;
    if (!library?.createViewer) {
      throw new Error("The local 3Dmol library could not load. Reload the page and try again.");
    }
    if (!viewer) {
      viewer = library.createViewer(viewerNode, { backgroundColor: "white" });
      new ResizeObserver(() => {
        viewer.resize();
        viewer.render();
      }).observe(viewerNode);
    }
    return viewer;
  }

  function describeConfidence(values) {
    if (!values.length) {
      confidenceNote.textContent =
        "No usable per-atom B-factor values were found. The structure uses a neutral colour.";
      return;
    }
    const low = Math.min(...values);
    const high = Math.max(...values);
    confidenceNote.textContent =
      `Colouring uses stored per-atom B-factor values (${low.toFixed(1)}–${high.toFixed(1)}). ` +
      "Values are not recalculated.";
  }

  async function showStructure(group, structure) {
    const requestId = ++activeRequest;
    errorNode.hidden = true;
    loading.hidden = false;
    status.textContent = `Loading ${structure.name} from ${group.name}…`;
    clearViewer();
    try {
      const text = await structureText(structure);
      if (requestId !== activeRequest) return;
      const currentViewer = getViewer();
      const model = currentViewer.addModel(text, structure.format);
      const atoms = model.selectedAtoms({});
      if (!atoms.length) throw new Error("The selected file contains no readable atoms.");
      const confidenceValues = atoms
        .map((atom) => atom.b)
        .filter((value) => Number.isFinite(value) && value >= 0 && value <= 100);
      const hasConfidence = confidenceValues.length > 0;
      model.setStyle(
        {},
        {
          cartoon: hasConfidence
            ? {
                colorfunc: (atom) =>
                  Number.isFinite(atom.b) && atom.b >= 0 && atom.b <= 100
                    ? confidenceColour(atom.b)
                    : 0x64748b,
              }
            : { color: 0x64748b },
        },
      );
      currentViewer.setBackgroundColor("white");
      currentViewer.zoomTo();
      currentViewer.render();
      describeConfidence(confidenceValues);
      status.textContent = `${group.name} · ${structure.name} · local prediction`;
      loading.hidden = true;
    } catch (error) {
      if (requestId !== activeRequest) return;
      clearViewer();
      showError(error);
      status.textContent = `Could not display ${structure.name} from ${group.name}.`;
    }
  }

  function loadGroup(groupName) {
    const group = groupsByName.get(groupName);
    if (!group) return;
    fileSelect.replaceChildren();
    fileSelect.disabled = group.structures.length === 0;
    for (const structure of group.structures) {
      const option = document.createElement("option");
      option.value = structure.id;
      option.textContent = structure.name;
      fileSelect.append(option);
    }
    const first = group.structures[0];
    if (first) void showStructure(group, first);
    else {
      clearViewer();
      showError("This folder contains no PDB or CIF structure files.");
      status.textContent = `No structures are available in ${group.name}.`;
    }
  }

  const response = await fetch("/local-structures.json", { cache: "no-store" });
  if (!response.ok) throw new Error(await responseError(response));
  const payload = await response.json();
  if (!Array.isArray(payload.groups)) {
    throw new Error("The local structure index has an unreadable format.");
  }
  const groups = payload.groups.filter(
    (group) =>
      group &&
      typeof group.name === "string" &&
      Array.isArray(group.structures) &&
      group.structures.every(
        (structure) =>
          structure &&
          typeof structure.id === "string" &&
          typeof structure.name === "string" &&
          (structure.format === "pdb" || structure.format === "cif"),
      ),
  );
  if (!groups.length) {
    groupSelect.disabled = true;
    fileSelect.disabled = true;
    loading.hidden = true;
    status.textContent = "No local PDB or CIF structure files were found.";
    return;
  }

  for (const group of groups) {
    groupsByName.set(group.name, group);
    const option = document.createElement("option");
    option.value = group.name;
    option.textContent = group.name;
    groupSelect.append(option);
  }
  groupSelect.disabled = false;
  groupSelect.addEventListener("change", () => loadGroup(groupSelect.value));
  fileSelect.addEventListener("change", () => {
    const group = groupsByName.get(groupSelect.value);
    const structure = group?.structures.find((item) => item.id === fileSelect.value);
    if (group && structure) void showStructure(group, structure);
  });
  loadGroup(groupSelect.value);
}

// The loop as a graph, running the world model live.
//
// Eight sections around the loop, eight cells along each one: sixty-four
// nodes, joined along the flow and across to their neighbours. Film grows on
// every node, warms the chips as it thickens, and a dose clears it where it
// lands and a little downstream.
//
// The policy choosing the doses is the one `scripts/loop_policy.py` learned,
// read from data/loop-policy.json. The dynamics are the same model it trained
// in, rewritten here so the page can run it at thirty frames a second.
import { clamp, colour, damp, lerp } from "./tokens.mjs";

const ROWS = 8; // sections around the loop
const COLS = 8; // cells along each section
const BASE_C = 62;
const HOT = 4;

function model(policy) {
  const sensors = new Set(policy?.sensors ?? [0, 2, 3, 4, 5, 6]);
  const levels = policy?.levels ?? 4;
  const table = policy?.table ?? null;
  const film = Array.from({ length: ROWS }, () => 0.45 + Math.random() * 0.35);
  const growth = Array.from({ length: ROWS }, (_, row) =>
    0.01 + 0.016 * Math.exp(-(((row - HOT) / 2.2) ** 2)) + Math.random() * 0.004);

  const level = (value) => Math.min(levels - 1, Math.floor(value * levels * 1.6));
  const temperature = () =>
    BASE_C + 34 * (0.55 * film[HOT] + 0.225 * (film[(HOT + 7) % ROWS] + film[(HOT + 1) % ROWS]));

  function choose() {
    if (!table) return null;
    const hot = Math.max(
      ...[-1, 0, 1]
        .map((offset) => (HOT + offset + ROWS) % ROWS)
        .filter((row) => sensors.has(row))
        .map((row) => film[row]),
    );
    const sensed = [...sensors].map((row) => [film[row], row]).sort((a, b) => b[0] - a[0]);
    const [worst, where] = sensed[0];
    const values = table[`${level(hot)},${level(worst)},${[...sensors].indexOf(where)}`];
    if (!values) return null;
    const best = values.indexOf(Math.max(...values));
    return best === 0 ? null : best - 1;
  }

  function step(dose) {
    if (dose !== null) {
      for (const [offset, clearing] of [[0, 0.72], [1, 0.34], [2, 0.12]]) {
        const row = (dose + offset) % ROWS;
        film[row] = Math.max(0, film[row] * (1 - clearing));
      }
    }
    for (let row = 0; row < ROWS; row += 1) {
      film[row] = Math.min(1, film[row] + growth[row] * (0.35 + film[row]) * (1 - film[row]));
    }
  }

  return { film, sensors, step, choose, temperature };
}

export function mountGraph(canvas, { reduced = false, policy = null } = {}) {
  const context = canvas.getContext("2d");
  if (!context) throw new Error("No 2D context for the loop graph");
  const loop = model(policy);
  const shown = new Float32Array(ROWS); // eased, so the drawing never jumps
  const flash = new Float32Array(ROWS); // a dose landing
  let elapsed = 0;
  let dosed = null;

  function draw(width, height) {
    const padX = 34;
    const padY = 26;
    const stepX = (width - padX * 2) / (COLS - 1);
    const stepY = (height - padY * 2) / (ROWS - 1);
    const at = (row, col) => [padX + col * stepX, padY + row * stepY];

    context.clearRect(0, 0, width, height);
    const edge = colour("--border");
    const flow = colour("--cobalt-hydro");
    const ochre = colour("--biofilm-ochre");
    const teal = colour("--teal-protein");
    const ink = colour("--ink-faint");

    // Edges: along the flow, and across to the neighbouring section.
    context.lineWidth = 1;
    for (let row = 0; row < ROWS; row += 1) {
      for (let col = 0; col < COLS; col += 1) {
        const [x, y] = at(row, col);
        if (col < COLS - 1) {
          const [x2, y2] = at(row, col + 1);
          context.strokeStyle = `rgba(${edge.r * 255 | 0}, ${edge.g * 255 | 0}, ${edge.b * 255 | 0}, 1)`;
          context.beginPath();
          context.moveTo(x, y);
          context.lineTo(x2, y2);
          context.stroke();
        }
        if (row < ROWS - 1) {
          const [x2, y2] = at(row + 1, col);
          context.strokeStyle = `rgba(${edge.r * 255 | 0}, ${edge.g * 255 | 0}, ${edge.b * 255 | 0}, 0.75)`;
          context.beginPath();
          context.moveTo(x, y);
          context.lineTo(x2, y2);
          context.stroke();
        }
      }
    }

    // What is moving: a pulse of water along every section.
    for (let row = 0; row < ROWS; row += 1) {
      const phase = (elapsed * 0.35 + row * 0.13) % 1;
      const col = phase * (COLS - 1);
      const [x, y] = at(row, col);
      context.fillStyle = `rgba(${flow.r * 255 | 0}, ${flow.g * 255 | 0}, ${flow.b * 255 | 0}, 0.5)`;
      context.beginPath();
      context.arc(x, y, 2.6, 0, Math.PI * 2);
      context.fill();
    }

    // Nodes: film as weight and colour, sensors ringed, a dose flashing teal.
    for (let row = 0; row < ROWS; row += 1) {
      const level = shown[row];
      const sensed = loop.sensors.has(row);
      for (let col = 0; col < COLS; col += 1) {
        const [x, y] = at(row, col);
        const local = clamp(level * (0.72 + 0.4 * Math.sin(col * 1.7 + row)));
        const radius = lerp(3.1, 8.4, local);
        const hit = flash[row] * (1 - Math.min(1, Math.abs(col - 1) / 4));
        context.fillStyle = hit > 0.02
          ? `rgba(${teal.r * 255 | 0}, ${teal.g * 255 | 0}, ${teal.b * 255 | 0}, ${0.35 + hit * 0.6})`
          : `rgba(${ochre.r * 255 | 0}, ${ochre.g * 255 | 0}, ${ochre.b * 255 | 0}, ${0.12 + local * 0.78})`;
        context.beginPath();
        context.arc(x, y, radius, 0, Math.PI * 2);
        context.fill();
        if (sensed && col === 0) {
          context.strokeStyle = `rgba(${flow.r * 255 | 0}, ${flow.g * 255 | 0}, ${flow.b * 255 | 0}, 0.9)`;
          context.lineWidth = 1.6;
          context.beginPath();
          context.arc(x, y, radius + 4.5, 0, Math.PI * 2);
          context.stroke();
          context.lineWidth = 1;
        }
      }
    }

    // One line of state, in the page's own mono.
    context.fillStyle = `rgba(${ink.r * 255 | 0}, ${ink.g * 255 | 0}, ${ink.b * 255 | 0}, 1)`;
    context.font = '10px ui-monospace, "Geist Mono", Menlo, monospace';
    context.fillText(`${loop.temperature().toFixed(1)} C`, padX - 24, 14);
    context.fillText(dosed === null ? "holding" : `dosing section ${dosed + 1}`, width - 112, 14);
  }

  let since = 0;
  function update(time, dt) {
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    const ratio = Math.min(devicePixelRatio || 1, 2);
    if (canvas.width !== Math.round(width * ratio)) {
      canvas.width = Math.round(width * ratio);
      canvas.height = Math.round(height * ratio);
    }
    context.setTransform(ratio, 0, 0, ratio, 0, 0);

    const step = reduced ? 0 : Math.min(0.05, dt);
    elapsed += step;
    since += step;
    // One decision an hour, an hour every 0.9 seconds.
    if (since > 0.9) {
      since = 0;
      dosed = loop.choose();
      loop.step(dosed);
      if (dosed !== null) for (const offset of [0, 1, 2]) flash[(dosed + offset) % ROWS] = 1;
    }
    for (let row = 0; row < ROWS; row += 1) {
      shown[row] = damp(shown[row], loop.film[row], 3.5, step || 0.016);
      flash[row] = damp(flash[row], 0, 2.2, step || 0.016);
    }
    draw(width, height);
  }

  return { update };
}

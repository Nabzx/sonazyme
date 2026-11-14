// The sonar bench. A probe the visitor drags along a cut-away pipe, the echo
// trace under it, and a fouling map that fills in as the probe passes.
// Every echo here is simulated from a made-up film profile. Nothing is measured.
import { clamp, damp, lerp, seeded, smooth, token } from "./tokens.mjs";

const BINS = 96;
const bump = (u, at, width) => Math.exp(-(((u - at) / width) ** 2));

// Film thickness along the pipe, 0 to 1. Invented, fixed, the same every visit.
export function film(u) {
  return clamp(bump(u, 0.63, 0.085) + bump(u, 0.72, 0.04) * 0.5 + bump(u, 0.27, 0.045) * 0.55 - 0.04);
}

export function mountSonar(canvas, { reduced = false, onChange = () => {} } = {}) {
  const context = canvas.getContext("2d");
  const random = seeded(11);
  const noise = Array.from({ length: 512 }, () => random() - 0.5);
  const c = {
    ink: token("--ink"),
    muted: token("--ink-muted"),
    faint: token("--ink-faint"),
    border: token("--border"),
    strong: token("--border-strong"),
    card: token("--card-surface"),
    water: token("--water"),
    ochre: token("--biofilm-ochre"),
    ochreTint: token("--ochre-tint"),
    mono: token("--mono"),
    shadow: token("--shadow-ink"),
  };
  const scanned = new Float32Array(BINS).fill(reduced ? 1 : 0);
  let position = reduced ? 0.63 : 0.12;
  let shown = position;
  let depth = film(position);
  let dragging = false;
  let touched = reduced;
  let intro = reduced ? 1 : -1; // -1 waiting, 0 to 1 sweeping, 1 done
  let width = 0;
  let height = 0;
  let clock = 0;
  let last = "";

  const box = () => {
    const pad = Math.max(18, width * 0.045);
    return { x0: pad, x1: width - pad, pad };
  };
  const toU = (clientX) => {
    const rect = canvas.getBoundingClientRect();
    const { x0, x1 } = box();
    return clamp((clientX - rect.left - x0 - 30) / (x1 - x0 - 60));
  };

  function move(u) {
    position = clamp(u);
    touched = true;
    intro = 1;
  }
  canvas.addEventListener("pointerdown", (event) => {
    dragging = true;
    canvas.setPointerCapture(event.pointerId);
    canvas.classList.add("is-dragging");
    move(toU(event.clientX));
  });
  canvas.addEventListener("pointermove", (event) => {
    if (dragging) move(toU(event.clientX));
  });
  const release = () => {
    dragging = false;
    canvas.classList.remove("is-dragging");
  };
  canvas.addEventListener("pointerup", release);
  canvas.addEventListener("pointercancel", release);
  canvas.addEventListener("keydown", (event) => {
    const stepBy = { ArrowLeft: -0.02, ArrowDown: -0.02, ArrowRight: 0.02, ArrowUp: 0.02, PageDown: -0.1, PageUp: 0.1 }[event.key];
    if (event.key === "Home") move(0);
    else if (event.key === "End") move(1);
    else if (stepBy) move(position + stepBy);
    else return;
    event.preventDefault();
  });

  function resize() {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    if (w === width && h === height) return;
    width = w;
    height = h;
    canvas.width = Math.round(w * ratio);
    canvas.height = Math.round(h * ratio);
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
  }

  function label(text, x, y, colourName = c.faint, align = "left") {
    context.font = `${width < 520 ? 9 : 10}px ${c.mono}`;
    context.fillStyle = colourName;
    context.textAlign = align;
    context.textBaseline = "middle";
    if ("letterSpacing" in context) context.letterSpacing = "1.4px";
    context.fillText(text.toUpperCase(), x, y);
  }

  function rounded(x, y, w, h, r) {
    context.beginPath();
    context.roundRect(x, y, w, h, r);
  }

  function update(time, dt) {
    resize();
    if (!width) return;
    clock = reduced ? 0 : time;

    // One gentle sweep on first view, to show what the probe does.
    if (intro >= 0 && intro < 1 && !touched) {
      intro = Math.min(1, intro + dt / 4.2);
      position = lerp(0.12, 0.6, smooth(intro));
    }
    shown = reduced ? position : damp(shown, position, 14, dt);
    depth = reduced ? film(shown) : damp(depth, film(shown), 10, dt);
    const bin = Math.round(shown * (BINS - 1));
    for (let i = Math.max(0, bin - 2); i <= Math.min(BINS - 1, bin + 2); i += 1) scanned[i] = 1;

    const state = depth > 0.12 ? "film" : "clean";
    const value = Math.round(shown * 100);
    if (`${state}${value}` !== last) {
      last = `${state}${value}`;
      onChange({ state, value });
    }

    const { x0, x1, pad } = box();
    const span = x1 - x0;
    const px = (u) => x0 + 30 + u * (span - 60);
    const probeX = px(shown);
    context.clearRect(0, 0, width, height);
    context.lineJoin = "round";
    context.lineCap = "round";

    // Pipe, cut away along its length.
    const top = height * 0.2;
    const bottom = height * 0.47;
    const wallT = Math.max(7, height * 0.018);
    const maxFilm = (bottom - top) * 0.26;
    context.fillStyle = c.water;
    context.fillRect(x0, top, span, bottom - top);
    context.fillStyle = c.strong;
    context.fillRect(x0, top - wallT, span, wallT);
    context.fillRect(x0, bottom, span, wallT);
    context.strokeStyle = c.faint;
    context.lineWidth = 1;
    for (const y of [top - wallT, top, bottom, bottom + wallT]) {
      context.beginPath();
      context.moveTo(x0, y + 0.5);
      context.lineTo(x1, y + 0.5);
      context.stroke();
    }
    // The film, in ochre, on both walls. Thicker on the floor of the pipe.
    for (const [edge, direction, scale] of [[bottom, -1, 1], [top, 1, 0.32]]) {
      context.beginPath();
      context.moveTo(x0, edge);
      for (let i = 0; i <= 120; i += 1) {
        const u = i / 120;
        const ripple = 1 + Math.sin(u * 90) * 0.08 + Math.sin(u * 37 + 1) * 0.07;
        context.lineTo(x0 + u * span, edge + direction * film((x0 + u * span - x0 - 30) / (span - 60)) * maxFilm * scale * ripple);
      }
      context.lineTo(x1, edge);
      context.closePath();
      context.fillStyle = c.ochre;
      context.globalAlpha = 0.78;
      context.fill();
      context.globalAlpha = 1;
    }
    label("Pipe wall", x0, top - wallT - 12);
    label("Water", x0 + 8, (top + bottom) / 2 + (width < 520 ? 14 : 0));

    // Pulses leaving the probe and coming back off the far side.
    const hitY = bottom - depth * maxFilm;
    context.save();
    context.beginPath();
    context.rect(x0, top, span, bottom - top);
    context.clip();
    for (let k = 0; k < 3; k += 1) {
      const phase = reduced ? 0.25 + k * 0.25 : (clock * 0.55 + k / 3) % 1;
      const down = phase < 0.5;
      const t = down ? phase * 2 : (phase - 0.5) * 2;
      const y = down ? lerp(top, hitY, t) : lerp(hitY, top, t);
      const spread = 16 + (down ? t : 1 - t * 0.4) * 26;
      const film_ = !down && depth > 0.12;
      context.strokeStyle = film_ ? c.ochre : c.ink;
      context.globalAlpha = (down ? 0.55 : 0.4) * Math.sin(t * Math.PI) ** 0.6;
      context.lineWidth = 1.4;
      context.beginPath();
      context.moveTo(probeX - spread, y + (down ? -5 : 5));
      context.quadraticCurveTo(probeX, y + (down ? 6 : -6), probeX + spread, y + (down ? -5 : 5));
      context.stroke();
    }
    context.restore();
    context.globalAlpha = 1;

    // The probe: a clamp-on transducer with a cable.
    const probeW = Math.max(46, Math.min(64, width * 0.07));
    const probeH = probeW * 0.62;
    const probeY = top - wallT - probeH - 2;
    context.strokeStyle = c.faint;
    context.lineWidth = 1.2;
    context.beginPath();
    context.moveTo(probeX, probeY);
    context.bezierCurveTo(probeX, probeY - 34, lerp(probeX, x1, 0.5), 2, x1, pad * 0.5);
    context.stroke();
    context.shadowColor = c.shadow;
    context.shadowBlur = 16;
    context.shadowOffsetY = 6;
    rounded(probeX - probeW / 2, probeY, probeW, probeH, 8);
    context.fillStyle = c.ink;
    context.fill();
    context.shadowColor = "transparent";
    context.fillStyle = c.muted;
    context.fillRect(probeX - probeW * 0.32, top - wallT - 3, probeW * 0.64, 3);
    context.strokeStyle = c.faint;
    context.lineWidth = 1;
    for (let g = -1; g <= 1; g += 1) {
      context.beginPath();
      context.moveTo(probeX + g * 6, probeY + probeH * 0.3);
      context.lineTo(probeX + g * 6, probeY + probeH * 0.7);
      context.stroke();
    }
    if (!touched && intro >= 1) label("Drag", probeX, probeY - 14, c.muted, "center");
    if (!touched && intro < 1) label("Drag the probe", probeX + probeW / 2 + 12, probeY + probeH / 2, c.muted);

    // A-scan: the echo trace on a graticule.
    const sx0 = x0;
    const sx1 = x1;
    const sy0 = height * 0.56;
    const sy1 = height * 0.84;
    const mid = (sy0 + sy1) / 2;
    rounded(sx0, sy0, sx1 - sx0, sy1 - sy0, 10);
    context.fillStyle = c.card;
    context.fill();
    context.strokeStyle = c.border;
    context.lineWidth = 1;
    context.stroke();
    context.beginPath();
    for (let i = 1; i < 12; i += 1) {
      const x = Math.round(lerp(sx0, sx1, i / 12)) + 0.5;
      context.moveTo(x, sy0 + 6);
      context.lineTo(x, sy1 - 6);
    }
    for (let j = 1; j < 4; j += 1) {
      const y = Math.round(lerp(sy0, sy1, j / 4)) + 0.5;
      context.moveTo(sx0 + 6, y);
      context.lineTo(sx1 - 6, y);
    }
    context.strokeStyle = c.border;
    context.globalAlpha = 0.7;
    context.stroke();
    context.globalAlpha = 1;

    const amp = (sy1 - sy0) * 0.4;
    const filmAt = 0.8 - depth * 0.17;
    const echoes = [
      { at: 0.07, size: 1, width: 0.016 },
      { at: 0.19, size: 0.5, width: 0.012 },
      { at: filmAt, size: depth * 0.62, width: 0.014 + depth * 0.012 },
      { at: 0.8, size: 0.72 * (1 - depth * 0.55), width: 0.013 },
    ];
    const signal = (t, index) => {
      let v = noise[(index * 3 + Math.floor(clock * 24) * 17) & 511] * 0.035;
      for (const e of echoes) v += e.size * bump(t, e.at, e.width) * Math.sin((t - e.at) * 300);
      return v;
    };
    const steps = Math.floor((sx1 - sx0 - 24) / 1.5);
    const trace = (from, to, stroke) => {
      context.beginPath();
      for (let i = Math.floor(from * steps); i <= Math.ceil(to * steps); i += 1) {
        const t = i / steps;
        const x = sx0 + 12 + t * (sx1 - sx0 - 24);
        const y = mid - signal(t, i) * amp;
        if (i === Math.floor(from * steps)) context.moveTo(x, y);
        else context.lineTo(x, y);
      }
      context.strokeStyle = stroke;
      context.lineWidth = 1.5;
      context.stroke();
    };
    const hasFilm = depth > 0.12;
    const f0 = filmAt - 0.045;
    const f1 = Math.min(filmAt + 0.04, 0.775);
    if (hasFilm) {
      trace(0, f0, c.ink);
      trace(f0, f1, c.ochre);
      trace(f1, 1, c.ink);
    } else {
      trace(0, 1, c.ink);
    }
    const tx = (t) => sx0 + 12 + t * (sx1 - sx0 - 24);
    label("Near wall", tx(0.19), sy0 + 14, c.faint, "center");
    label("Far wall", tx(0.8) + 4, sy0 + 14, c.faint, "left");
    if (hasFilm) label("Film", tx(filmAt) - 6, sy1 - 14, c.ochre, "right");
    label("Echo", sx0, sy0 - 12);
    label("Time", sx1, sy1 + 12, c.faint, "right");

    // Fouling map: fills in where the probe has been.
    const my0 = height * 0.915;
    const mh = Math.max(10, height * 0.03);
    const cellW = (span - 60) / BINS;
    rounded(x0, my0, span, mh, mh / 2);
    context.save();
    context.clip();
    context.fillStyle = c.card;
    context.fillRect(x0, my0, span, mh);
    for (let i = 0; i < BINS; i += 1) {
      if (!scanned[i]) continue;
      const level = film(i / (BINS - 1));
      context.fillStyle = c.ochre;
      context.globalAlpha = level < 0.06 ? 0 : 0.12 + level * 0.88;
      context.fillRect(x0 + 30 + i * cellW - 0.5, my0, cellW + 1, mh);
    }
    context.globalAlpha = 1;
    context.restore();
    rounded(x0, my0, span, mh, mh / 2);
    context.strokeStyle = c.strong;
    context.lineWidth = 1;
    context.stroke();
    context.strokeStyle = c.ink;
    context.lineWidth = 1.5;
    context.beginPath();
    context.moveTo(probeX, my0 - 5);
    context.lineTo(probeX, my0 + mh + 5);
    context.stroke();
    label("Fouling map", x0, my0 - 12);
  }

  return {
    update,
    enter() {
      if (intro < 0) intro = 0;
    },
  };
}

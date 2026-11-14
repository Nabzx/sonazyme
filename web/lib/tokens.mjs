// Reads design tokens from tokens.css, so scenes never name a colour.
import * as THREE from "../vendor/three.module.js";

export function token(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

export function colour(name) {
  return new THREE.Color(token(name));
}

export function fit(renderer, camera, canvas) {
  const w = canvas.clientWidth || 1;
  const h = canvas.clientHeight || 1;
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  const pw = Math.round(w * ratio);
  const ph = Math.round(h * ratio);
  if (canvas.width === pw && canvas.height === ph) return false;
  renderer.setPixelRatio(ratio);
  renderer.setSize(w, h, false);
  if (camera.isPerspectiveCamera) {
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  return true;
}

export const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const smooth = (v) => {
  const x = clamp(v);
  return x * x * (3 - 2 * x);
};
export const lerp = (a, b, t) => a + (b - a) * t;
export const damp = (a, b, rate, dt) => a + (b - a) * (1 - Math.exp(-rate * dt));

// Deterministic noise source, so every visit draws the same illustration.
export function seeded(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

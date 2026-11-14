// The enzyme, drawn from the real Boltz coordinates in data/enzyme.json.
// The fold is a real prediction and the cutting site is sourced from the
// literature. The engineered region, the heat wobble and the strand it cuts
// are illustrations, and the page says so beside the canvas.
import * as THREE from "../vendor/three.module.js";
import { clamp, colour, damp, fit, lerp, seeded, smooth, token } from "./tokens.mjs";

const SUB = 5; // beads drawn per residue, along a smooth curve through the chain
const STRAND = 52; // beads per strand of the thing the enzyme cuts

function catmull(a, b, c, d, t) {
  const t2 = t * t;
  const t3 = t2 * t;
  return 0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (3 * b - a - 3 * c + d) * t3);
}

// THE COBALT SET LIVES HERE, AND ONLY HERE.
// There is no sourced engineered region yet, so this is an illustration and
// the page tags it as one. When a design run gives real positions, add them to
// enzyme.json as engineered_region.positions (1-based) and this picks them up;
// then change the tag in index.html. Until then: the stretch of confident
// chain furthest from the cutting site, because design works away from it.
function engineeredRegion(data, at, siteCentre) {
  if (data.engineered_region?.positions?.length) return data.engineered_region.positions;
  const n = data.xyz.length;
  const span = 13;
  let best = 36;
  let bestScore = -1;
  for (let start = 36; start + span < n; start += 1) {
    let score = 0;
    for (let i = start; i < start + span; i += 1) score += at(i).distanceTo(siteCentre);
    if (score > bestScore) {
      bestScore = score;
      best = start;
    }
  }
  return Array.from({ length: span }, (_, i) => best + i + 1);
}

function prepare(data) {
  const n = data.xyz.length;
  // Centre on the well-predicted core, so the floppy leading tail does not
  // drag the fold off centre.
  const core = data.xyz.filter((_, i) => data.confidence[i] >= 85);
  const mid = [0, 1, 2].map((k) => core.reduce((s, p) => s + p[k], 0) / core.length);
  const fold = new Float32Array(n * 3);
  data.xyz.forEach((p, i) => {
    for (let k = 0; k < 3; k += 1) fold[i * 3 + k] = p[k] - mid[k];
  });
  const at = (i) => new THREE.Vector3(fold[i * 3], fold[i * 3 + 1], fold[i * 3 + 2]);

  // The cutting site is sourced: the catalytic residues in data.active_site,
  // 1-based, so residue 53 is xyz[52]. Exactly those are teal, nothing else.
  const site = new Float32Array(n);
  const siteCentre = new THREE.Vector3();
  const positions = data.active_site?.positions ?? [];
  for (const position of positions) {
    site[position - 1] = 1;
    siteCentre.add(at(position - 1));
  }
  siteCentre.divideScalar(Math.max(1, positions.length));

  const region = new Float32Array(n);
  for (const position of engineeredRegion(data, at, siteCentre)) region[position - 1] = 1;

  // How firmly each residue holds when the chain heats.
  const hold = new Float32Array(n);
  for (let i = 0; i < n; i += 1) {
    const near = 1 - clamp((at(i).distanceTo(siteCentre) - 7) / 9);
    hold[i] = Math.max(near, region[i] * 0.8);
  }
  return { n, fold, site, region, hold, siteCentre };
}

export function mountProtein(canvas, data, { mode = "hero", reduced = false } = {}) {
  const model = prepare(data);
  const { n } = model;
  const random = seeded(7);
  const background = colour("--sterile-white");
  const chain = colour("--chain");
  const teal = colour("--teal-protein");
  const cobalt = colour("--cobalt-hydro");
  const ochre = colour("--biofilm-ochre");

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(mode === "hero" ? background : colour("--card-surface"), 135, 215);
  const camera = new THREE.PerspectiveCamera(30, 1, 1, 400);
  camera.position.set(0, 0, 132);
  scene.add(new THREE.HemisphereLight(0xffffff, new THREE.Color(token("--border-strong")), 1.5));
  const key = new THREE.DirectionalLight(0xffffff, 1.9);
  key.position.set(-40, 60, 80);
  scene.add(key);

  const rig = new THREE.Group(); // placement on screen
  const spin = new THREE.Group(); // rotation
  rig.add(spin);
  scene.add(rig);

  // Chain
  const beads = (n - 1) * SUB + 1;
  const material = new THREE.MeshStandardMaterial({ roughness: 0.42, metalness: 0.02 });
  const mesh = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 14, 10), material, beads);
  mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  mesh.frustumCulled = false;
  spin.add(mesh);

  const scatter = new Float32Array(n * 3);
  const phase = new Float32Array(n * 3);
  for (let i = 0; i < n; i += 1) {
    const v = new THREE.Vector3(random() - 0.5, random() - 0.5, random() - 0.5).normalize();
    v.multiplyScalar(26 + random() * 30);
    scatter.set([v.x, v.y, v.z], i * 3);
    phase.set([random() * 6.28, random() * 6.28, random() * 6.28], i * 3);
  }
  const live = new Float32Array(n * 3);
  const radius = new Float32Array(n);
  for (let i = 0; i < n; i += 1) radius[i] = lerp(0.72, 1.18, clamp((data.confidence[i] - 45) / 45));

  // What the enzyme cuts: a short strand of the glue, in ochre.
  const outward = model.siteCentre.clone().normalize();
  const axis = new THREE.Vector3(0, 1, 0).cross(outward).normalize();
  const side = outward.clone().cross(axis).normalize();
  const strand = new THREE.InstancedMesh(
    new THREE.SphereGeometry(1, 10, 8),
    new THREE.MeshStandardMaterial({ roughness: 0.5, color: ochre }),
    STRAND * 2,
  );
  strand.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  strand.frustumCulled = false;
  strand.visible = mode === "card";
  spin.add(strand);

  if (mode === "card") {
    // Turn the cutting site towards the viewer, a little to one side.
    spin.quaternion.setFromUnitVectors(outward, new THREE.Vector3(0.62, 0.12, 0.77).normalize());
  }
  const rest = spin.quaternion.clone();

  const state = { assemble: mode === "hero" ? 1 : 0, site: mode === "hero" ? 1 : 0, region: 0, heat: 0, dock: 0 };
  const target = { ...state };
  const pointer = { x: 0, y: 0, tx: 0, ty: 0 };
  const dummy = new THREE.Object3D();
  const tint = new THREE.Color();
  const turn = new THREE.Quaternion();
  const euler = new THREE.Euler();
  let clock = 0;

  function place(w, h) {
    const wide = w / h > 1.15;
    if (mode === "hero") {
      camera.position.z = wide ? 150 : 235;
      const halfH = Math.tan((camera.fov * Math.PI) / 360) * camera.position.z;
      rig.position.set(wide ? halfH * (w / h) * 0.46 : 0, wide ? 0 : halfH * 0.4, 0);
    } else {
      camera.position.z = w / h > 0.95 ? 146 : 172;
      rig.position.set(4, w / h > 0.95 ? 3 : 9, 0);
    }
    // Depth haze follows the camera, so the fold never washes out.
    scene.fog.near = camera.position.z - 20;
    scene.fog.far = camera.position.z + 62;
  }

  function update(time, dt) {
    if (fit(renderer, camera, canvas) || clock === 0) place(canvas.clientWidth, canvas.clientHeight);
    clock = reduced ? 1 : time;
    const step = reduced ? 1 : dt;

    // Ease towards the targets. Folding runs at a steady pace so it reads.
    const gap = target.assemble - state.assemble;
    state.assemble += reduced ? gap : Math.sign(gap) * Math.min(Math.abs(gap), step / 2.6);
    for (const k of ["site", "region", "heat", "dock"]) {
      state[k] = reduced ? target[k] : damp(state[k], target[k], k === "dock" ? 2.2 : 4, step);
    }

    // Residue positions: scattered to folded, then the heat wobble on top.
    for (let i = 0; i < n; i += 1) {
      const a = smooth(state.assemble * 1.45 - (i / n) * 0.45);
      const shake = state.heat * (1 - model.hold[i]) * 3.4;
      for (let k = 0; k < 3; k += 1) {
        const j = i * 3 + k;
        const wobble =
          Math.sin(clock * 5.1 + phase[j] + i * 0.31) * 0.6 + Math.sin(clock * 8.3 + phase[j] * 1.7 + i * 0.12) * 0.4;
        live[j] = lerp(scatter[j], model.fold[j], a) + wobble * shake;
      }
    }

    // Beads along a smooth curve through the residues.
    let b = 0;
    for (let i = 0; i < n - 1; i += 1) {
      const i0 = Math.max(0, i - 1) * 3;
      const i1 = i * 3;
      const i2 = (i + 1) * 3;
      const i3 = Math.min(n - 1, i + 2) * 3;
      for (let s = 0; s < SUB; s += 1) {
        const t = s / SUB;
        dummy.position.set(
          catmull(live[i0], live[i1], live[i2], live[i3], t),
          catmull(live[i0 + 1], live[i1 + 1], live[i2 + 1], live[i3 + 1], t),
          catmull(live[i0 + 2], live[i1 + 2], live[i2 + 2], live[i3 + 2], t),
        );
        const r = t < 0.5 ? i : i + 1;
        paint(b, r);
        b += 1;
      }
    }
    dummy.position.set(live[(n - 1) * 3], live[(n - 1) * 3 + 1], live[(n - 1) * 3 + 2]);
    paint(b, n - 1);
    mesh.instanceMatrix.needsUpdate = true;
    mesh.instanceColor.needsUpdate = true;

    if (strand.visible) drawStrand();

    // Rotation and pointer parallax.
    pointer.x = damp(pointer.x, pointer.tx, 3, step);
    pointer.y = damp(pointer.y, pointer.ty, 3, step);
    if (mode === "hero") {
      euler.set(0.18 + pointer.y * 0.22, clock * 0.16 + pointer.x * 0.45, 0);
      spin.quaternion.setFromEuler(euler);
    } else {
      euler.set(Math.sin(clock * 0.23) * 0.07 + pointer.y * 0.18, Math.sin(clock * 0.31) * 0.26 + pointer.x * 0.3, 0);
      spin.quaternion.copy(turn.setFromEuler(euler)).multiply(rest);
    }
    renderer.render(scene, camera);
  }

  function paint(index, residue) {
    const size = radius[residue] * (1 + model.site[residue] * state.site * 0.38 + model.region[residue] * state.region * 0.16);
    dummy.scale.setScalar(size);
    dummy.updateMatrix();
    mesh.setMatrixAt(index, dummy.matrix);
    tint.copy(chain);
    if (model.region[residue]) tint.lerp(cobalt, state.region);
    if (model.site[residue]) tint.lerp(teal, state.site);
    mesh.setColorAt(index, tint);
  }

  // A two-stranded twist that slides into the cutting site and parts there.
  function drawStrand() {
    const d = smooth(state.dock);
    const cut = smooth((state.dock - 0.82) / 0.18);
    const origin = model.siteCentre.clone().addScaledVector(outward, lerp(46, 7.5, d));
    let b = 0;
    for (let s = 0; s < 2; s += 1) {
      for (let i = 0; i < STRAND; i += 1) {
        const u = i / (STRAND - 1) - 0.5;
        const angle = u * 9.5 + s * Math.PI + clock * 0.25;
        const along = u * 46 + Math.sign(u) * cut * 3.2;
        dummy.position
          .copy(origin)
          .addScaledVector(axis, along)
          .addScaledVector(side, Math.cos(angle) * 3.4)
          .addScaledVector(outward, Math.sin(angle) * 3.4 + Math.abs(u) * cut * 9);
        dummy.scale.setScalar(0.78 * smooth(state.dock * 6));
        dummy.updateMatrix();
        strand.setMatrixAt(b, dummy.matrix);
        b += 1;
      }
    }
    strand.instanceMatrix.needsUpdate = true;
  }

  return {
    update,
    set(next) {
      Object.assign(target, next);
    },
    point(x, y) {
      if (reduced) return;
      pointer.tx = x;
      pointer.ty = y;
    },
  };
}

// The enzyme, drawn from the real Boltz coordinates in data/enzyme.json.
// The fold is a real prediction and the cutting site is sourced from the
// literature. The engineered region, the heat wobble and the strand it cuts
// are illustrations, and the page says so beside the canvas.
import * as THREE from "../vendor/three.module.js";
import { clamp, colour, damp, fit, lerp, seeded, smooth, token } from "./tokens.mjs";

const SUB = 4; // samples per residue along the curve through the chain
const RADIAL = 9; // sides of the tube
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
  const chain = colour(mode === "hero" ? "--hero-chain" : "--chain");
  const chainPale = mode === "hero"
    ? colour("--hero-chain-pale")
    : colour("--card-surface").lerp(colour("--chain"), 0.35);
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

  // Chain, drawn as a tube swept along the curve. The topology is built once
  // and only the vertex positions, normals and colours move, so a frame
  // allocates nothing.
  const rings = (n - 1) * SUB + 1;
  const vertices = rings * RADIAL;
  const geometry = new THREE.BufferGeometry();
  const tubePosition = new Float32Array(vertices * 3);
  const tubeNormal = new Float32Array(vertices * 3);
  const tubeColour = new Float32Array(vertices * 3);
  geometry.setAttribute("position", new THREE.BufferAttribute(tubePosition, 3));
  geometry.setAttribute("normal", new THREE.BufferAttribute(tubeNormal, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(tubeColour, 3));
  const index = new Uint32Array((rings - 1) * RADIAL * 6);
  for (let r = 0, k = 0; r < rings - 1; r += 1) {
    for (let s = 0; s < RADIAL; s += 1) {
      const a = r * RADIAL + s;
      const b = r * RADIAL + ((s + 1) % RADIAL);
      const c = a + RADIAL;
      const d = b + RADIAL;
      index[k++] = a; index[k++] = c; index[k++] = b;
      index[k++] = b; index[k++] = c; index[k++] = d;
    }
  }
  geometry.setIndex(new THREE.BufferAttribute(index, 1));
  const material = new THREE.MeshStandardMaterial({
    roughness: 0.38,
    metalness: 0.03,
    vertexColors: true,
    flatShading: false,
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.frustumCulled = false;
  const heroBounds = new THREE.Box3().setFromArray(model.fold);
  const heroSphere = heroBounds.getBoundingSphere(new THREE.Sphere());
  if (mode === "hero") mesh.position.copy(heroSphere.center).negate();
  spin.add(mesh);

  // Scratch vectors, reused every frame.
  const curve = new Float32Array(rings * 3);
  const tangent = new THREE.Vector3();
  const normal = new THREE.Vector3(0, 1, 0);
  const binormal = new THREE.Vector3();
  const previous = new THREE.Vector3(0, 1, 0);
  const point = new THREE.Vector3();
  const offset = new THREE.Vector3();
  const COS = new Float32Array(RADIAL);
  const SIN = new Float32Array(RADIAL);
  for (let s = 0; s < RADIAL; s += 1) {
    COS[s] = Math.cos((s / RADIAL) * Math.PI * 2);
    SIN[s] = Math.sin((s / RADIAL) * Math.PI * 2);
  }

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
  // Thickness follows the model's own confidence: the uncertain leading tail
  // tapers away rather than swinging about at full weight.
  for (let i = 0; i < n; i += 1) {
    radius[i] = lerp(0.3, 1.3, clamp((data.confidence[i] - 50) / 38) ** 0.85);
  }

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
  const drift = { value: 0, target: 0 };
  let baseY = 0;
  const dummy = new THREE.Object3D();
  const tint = new THREE.Color();
  const turn = new THREE.Quaternion();
  const euler = new THREE.Euler();
  const heroProjection = new THREE.Matrix4();
  const heroProjectedPoint = new THREE.Vector3();
  let clock = 0;

  function centreHeroOutline() {
    // A centred 3D bounding box can still project off-centre when this
    // asymmetric chain rotates. Centre its visible outline in screen space.
    camera.clearViewOffset();
    camera.updateMatrixWorld();
    mesh.updateWorldMatrix(true, false);
    heroProjection.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse)
      .multiply(mesh.matrixWorld);
    let left = Infinity, right = -Infinity, bottom = Infinity, top = -Infinity;
    for (let index = 0; index < tubePosition.length; index += 3) {
      heroProjectedPoint.fromArray(tubePosition, index).applyMatrix4(heroProjection);
      left = Math.min(left, heroProjectedPoint.x);
      right = Math.max(right, heroProjectedPoint.x);
      bottom = Math.min(bottom, heroProjectedPoint.y);
      top = Math.max(top, heroProjectedPoint.y);
    }
    const width = canvas.clientWidth || 1;
    const height = canvas.clientHeight || 1;
    camera.setViewOffset(width, height, (left + right) * width / 4,
      -(bottom + top) * height / 4, width, height);
  }

  function place(w, h) {
    if (mode === "hero") {
      // Keep the complete trace centred in its own hero column, including the
      // long precursor tail, rather than positioning it against the viewport.
      const halfFov = Math.atan(Math.tan(camera.fov * Math.PI / 360) * Math.min(1, w / h));
      camera.position.z = (heroSphere.radius + 1.8) / Math.sin(halfFov) * 1.04;
      rig.position.set(0, 0, 0);
      baseY = rig.position.y;
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

    // Sample the curve through the residues, then sweep a tube along it.
    let b = 0;
    for (let i = 0; i < n - 1; i += 1) {
      const i0 = Math.max(0, i - 1) * 3;
      const i1 = i * 3;
      const i2 = (i + 1) * 3;
      const i3 = Math.min(n - 1, i + 2) * 3;
      for (let s = 0; s < SUB; s += 1) {
        const u = s / SUB;
        curve[b * 3] = catmull(live[i0], live[i1], live[i2], live[i3], u);
        curve[b * 3 + 1] = catmull(live[i0 + 1], live[i1 + 1], live[i2 + 1], live[i3 + 1], u);
        curve[b * 3 + 2] = catmull(live[i0 + 2], live[i1 + 2], live[i2 + 2], live[i3 + 2], u);
        b += 1;
      }
    }
    curve[b * 3] = live[(n - 1) * 3];
    curve[b * 3 + 1] = live[(n - 1) * 3 + 1];
    curve[b * 3 + 2] = live[(n - 1) * 3 + 2];

    previous.set(0, 1, 0);
    for (let r = 0; r < rings; r += 1) {
      const here = r * 3;
      const back = Math.max(0, r - 1) * 3;
      const ahead = Math.min(rings - 1, r + 1) * 3;
      tangent
        .set(curve[ahead] - curve[back], curve[ahead + 1] - curve[back + 1], curve[ahead + 2] - curve[back + 2])
        .normalize();
      // Carry the frame along the curve so the tube does not twist on itself.
      normal.copy(previous).addScaledVector(tangent, -previous.dot(tangent));
      if (normal.lengthSq() < 1e-6) normal.set(tangent.y, -tangent.x, 0);
      normal.normalize();
      previous.copy(normal);
      binormal.crossVectors(tangent, normal);

      const residue = Math.min(n - 1, Math.round(r / SUB));
      const thickness = widthAt(residue);
      point.set(curve[here], curve[here + 1], curve[here + 2]);
      shade(residue);
      for (let s = 0; s < RADIAL; s += 1) {
        const v = (r * RADIAL + s) * 3;
        offset.copy(normal).multiplyScalar(COS[s]).addScaledVector(binormal, SIN[s]);
        tubeNormal[v] = offset.x;
        tubeNormal[v + 1] = offset.y;
        tubeNormal[v + 2] = offset.z;
        tubePosition[v] = point.x + offset.x * thickness;
        tubePosition[v + 1] = point.y + offset.y * thickness;
        tubePosition[v + 2] = point.z + offset.z * thickness;
        tubeColour[v] = tint.r;
        tubeColour[v + 1] = tint.g;
        tubeColour[v + 2] = tint.b;
      }
    }
    geometry.attributes.position.needsUpdate = true;
    geometry.attributes.normal.needsUpdate = true;
    geometry.attributes.color.needsUpdate = true;

    if (strand.visible) drawStrand();

    // Rotation, pointer parallax, and the scroll drift in the hero.
    pointer.x = damp(pointer.x, pointer.tx, 3, step);
    pointer.y = damp(pointer.y, pointer.ty, 3, step);
    if (mode === "hero") {
      drift.value = reduced ? drift.target : damp(drift.value, drift.target, 6, step);
      rig.position.y = baseY + drift.value * 4;
      rig.position.z = drift.value * -8;
    }
    if (mode === "hero") {
      euler.set(0.18 + pointer.y * 0.22, clock * 0.16 + pointer.x * 0.45, 0);
      spin.quaternion.setFromEuler(euler);
    } else {
      euler.set(Math.sin(clock * 0.23) * 0.07 + pointer.y * 0.18, Math.sin(clock * 0.31) * 0.26 + pointer.x * 0.3, 0);
      spin.quaternion.copy(turn.setFromEuler(euler)).multiply(rest);
    }
    if (mode === "hero") centreHeroOutline();
    renderer.render(scene, camera);
  }

  // The cutting site swells a little as it lights up, so it reads as a place
  // on the chain rather than a stripe of colour.
  function widthAt(residue) {
    return (
      radius[residue] *
      (1 + model.site[residue] * state.site * 0.5 + model.region[residue] * state.region * 0.12)
    );
  }

  function shade(residue) {
    tint.copy(chainPale).lerp(chain, residue / n);
    if (model.region[residue]) tint.lerp(cobalt, state.region);
    if (model.site[residue]) tint.lerp(teal, state.site);
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
    // 0 at the top of the page, 1 once the hero has scrolled away.
    scroll(value) {
      drift.target = clamp(value);
    },
  };
}

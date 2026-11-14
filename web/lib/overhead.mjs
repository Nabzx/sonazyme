// The workflow, seen from above: racks, a cooling loop, the module beside the
// pipe. A depiction of the intended cycle, not a readout of anything.
import * as THREE from "../vendor/three.module.js";
import { clamp, colour, fit, lerp, smooth } from "./tokens.mjs";

const PIPE_Y = 0.42;
const CYCLE = 13;
// Start of each beat, as a fraction of the cycle: ping, detect, design, dose, clear.
const BEATS = [0, 0.17, 0.36, 0.56, 0.76];
const DOSE = 9;

function roundedLoop(points, radius) {
  const path = new THREE.CurvePath();
  const n = points.length;
  const corners = points.map((p, i) => {
    const before = points[(i - 1 + n) % n];
    const after = points[(i + 1) % n];
    return {
      in: p.clone().add(before.clone().sub(p).setLength(radius)),
      at: p,
      out: p.clone().add(after.clone().sub(p).setLength(radius)),
    };
  });
  corners.forEach((corner, i) => {
    path.add(new THREE.QuadraticBezierCurve3(corner.in, corner.at, corner.out));
    path.add(new THREE.LineCurve3(corner.out, corners[(i + 1) % n].in));
  });
  return path;
}

export function mountOverhead(canvas, { reduced = false, onBeat = () => {} } = {}) {
  const ink = colour("--ink");
  const card = colour("--card-surface");
  const line = colour("--border-strong");
  const steel = colour("--steel");
  const ochre = colour("--biofilm-ochre");
  const teal = colour("--teal-protein");

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 1, 200);
  camera.position.set(0, 44, 21);
  camera.lookAt(-0.5, 0, 0.4);

  scene.add(new THREE.HemisphereLight(0xffffff, colour("--border"), 1.15));
  const sun = new THREE.DirectionalLight(0xffffff, 2.05);
  sun.position.set(-14, 34, 10);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -26, right: 26, top: 22, bottom: -22, near: 1, far: 90 });
  sun.shadow.bias = -0.0004;
  sun.shadow.radius = 5;
  scene.add(sun);

  // Floor: only its shadows and a hairline grid show.
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(90, 70), new THREE.ShadowMaterial({ opacity: 0.24 }));
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  scene.add(floor);
  const grid = new THREE.GridHelper(72, 36, colour("--border"), colour("--border"));
  grid.position.y = 0.01;
  grid.material.transparent = true;
  grid.material.opacity = 0.7;
  scene.add(grid);

  const solid = new THREE.MeshStandardMaterial({ color: card, roughness: 0.85 });
  const edge = new THREE.LineBasicMaterial({ color: line });
  function block(w, h, d, x, z, material = solid) {
    const geometry = new THREE.BoxGeometry(w, h, d);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(x, h / 2, z);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(geometry), edge));
    scene.add(mesh);
    return mesh;
  }

  // Three rows of racks.
  const vent = new THREE.MeshStandardMaterial({ color: colour("--border"), roughness: 0.9 });
  for (const z of [-6, 0, 6]) {
    for (let i = 0; i < 10; i += 1) {
      const x = -6 + i * 2;
      block(1.62, 2.1, 1.25, x, z);
      const grille = new THREE.Mesh(new THREE.PlaneGeometry(1.1, 0.5), vent);
      grille.rotation.x = -Math.PI / 2;
      grille.position.set(x, 2.111, z);
      scene.add(grille);
    }
  }

  // The chiller the loop runs from.
  block(3.2, 2.5, 7.4, -14.2, 0);
  for (const z of [-2.2, 0, 2.2]) {
    const fan = new THREE.Mesh(new THREE.CylinderGeometry(0.85, 0.85, 0.12, 40), vent);
    fan.position.set(-14.2, 2.56, z);
    scene.add(fan);
    const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 0.16, 20), solid);
    hub.position.set(-14.2, 2.6, z);
    scene.add(hub);
  }

  // The cooling loop, snaking between the rows.
  const v = (x, z) => new THREE.Vector3(x, PIPE_Y, z);
  const loop = roundedLoop([v(-13.4, -9), v(14.4, -9), v(14.4, -3), v(-9.4, -3), v(-9.4, 3), v(14.4, 3), v(14.4, 9), v(-13.4, 9)], 1.3);
  const pipe = new THREE.Mesh(
    new THREE.TubeGeometry(loop, 720, 0.2, 12, true),
    new THREE.MeshStandardMaterial({ color: steel, roughness: 0.45, metalness: 0.25 }),
  );
  pipe.castShadow = true;
  scene.add(pipe);

  const samples = loop.getSpacedPoints(1200);
  const nearest = (x, z) => {
    let best = 0;
    let bestD = Infinity;
    samples.forEach((p, i) => {
      const d = (p.x - x) ** 2 + (p.z - z) ** 2;
      if (d < bestD) {
        bestD = d;
        best = i;
      }
    });
    return best / 1200;
  };
  const uModule = nearest(-4, 3);
  const uPatch = nearest(7, 3);
  const uEnd = nearest(13, 3);

  // The module beside the pipe, clamped on.
  const moduleBody = block(2.3, 1.0, 1.25, -4, 4.25, new THREE.MeshStandardMaterial({ color: ink, roughness: 0.6 }));
  const lampMaterial = new THREE.MeshStandardMaterial({ color: card, emissive: card, emissiveIntensity: 0 });
  const lampMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.26, 0.26, 0.08, 28), lampMaterial);
  lampMesh.position.set(0.65, 0.54, 0);
  moduleBody.add(lampMesh);
  const clamp_ = new THREE.Mesh(new THREE.TorusGeometry(0.32, 0.1, 10, 32), new THREE.MeshStandardMaterial({ color: ink, roughness: 0.6 }));
  clamp_.rotation.y = Math.PI / 2;
  clamp_.position.set(-4, PIPE_Y, 3);
  clamp_.castShadow = true;
  scene.add(clamp_);
  const arm = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.22, 0.75), moduleBody.material);
  arm.position.set(-4, PIPE_Y, 3.5);
  scene.add(arm);

  // The fouled patch: an ochre sleeve on the pipe.
  const sleeve = [];
  for (let i = 0; i <= 40; i += 1) sleeve.push(loop.getPointAt(uPatch - 0.014 + (i / 40) * 0.028));
  const patchMaterial = new THREE.MeshStandardMaterial({ color: ochre, emissive: ochre, emissiveIntensity: 0.1, roughness: 0.7, transparent: true });
  const patch = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(sleeve), 40, 0.31, 14, false), patchMaterial);
  scene.add(patch);
  const haloMaterial = new THREE.MeshBasicMaterial({ color: ochre, transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false });
  const halo = new THREE.Mesh(new THREE.RingGeometry(0.9, 1.0, 64), haloMaterial);
  halo.rotation.x = -Math.PI / 2;
  halo.position.copy(loop.getPointAt(uPatch)).setY(0.04);
  scene.add(halo);

  // The sonar pulse: rings that slide along the pipe.
  const RINGS = 7;
  const pulse = new THREE.InstancedMesh(new THREE.TorusGeometry(0.36, 0.05, 8, 32), new THREE.MeshBasicMaterial({ color: ink }), RINGS);
  pulse.frustumCulled = false;
  scene.add(pulse);

  // The enzyme dose, in teal.
  const dose = new THREE.InstancedMesh(
    new THREE.SphereGeometry(0.17, 14, 10),
    new THREE.MeshStandardMaterial({
      color: teal,
      emissive: teal,
      emissiveIntensity: 0.45,
      roughness: 0.35,
      depthTest: false,
      transparent: true,
      opacity: 0.92,
    }),
    DOSE,
  );
  dose.renderOrder = 4;
  dose.frustumCulled = false;
  scene.add(dose);

  const dummy = new THREE.Object3D();
  const tangent = new THREE.Vector3();
  const hidden = new THREE.Matrix4().makeScale(0, 0, 0);
  const X = new THREE.Vector3(0, 0, 1);
  let beat = -1;
  let started = null;

  function ring(index, u, size) {
    if (size <= 0.001) {
      pulse.setMatrixAt(index, hidden);
      return;
    }
    loop.getPointAt(((u % 1) + 1) % 1, dummy.position);
    loop.getTangentAt(((u % 1) + 1) % 1, tangent);
    dummy.quaternion.setFromUnitVectors(X, tangent.normalize());
    dummy.scale.setScalar(size);
    dummy.updateMatrix();
    pulse.setMatrixAt(index, dummy.matrix);
  }

  function frame() {
    if (!fit(renderer, camera, canvas) && camera.userData.ready) return;
    const aspect = canvas.clientWidth / canvas.clientHeight;
    const half = Math.max(11.6, 18.2 / aspect);
    Object.assign(camera, { left: -half * aspect, right: half * aspect, top: half, bottom: -half });
    camera.updateProjectionMatrix();
    camera.userData.ready = true;
  }

  function update(time) {
    frame();
    if (started === null) started = time;
    const t = reduced ? 0.66 : ((time - started) % CYCLE) / CYCLE;
    let now = 0;
    BEATS.forEach((start, i) => {
      if (t >= start) now = i;
    });
    if (now !== beat) {
      beat = now;
      onBeat(beat);
    }
    const within = (i) => clamp((t - BEATS[i]) / ((BEATS[i + 1] ?? 1) - BEATS[i]));
    const ping = within(0);
    const detect = within(1);
    const design = within(2);
    const dosing = within(3);
    const clear = within(4);

    // Fouling: back at the start of the cycle, gone once the dose has landed.
    const fouling = t < BEATS[4] ? smooth(ping * 5) : 1 - smooth(clear * 2.6);
    patchMaterial.opacity = fouling;
    patch.visible = fouling > 0.01;
    const flare = t >= BEATS[1] && t < BEATS[2] ? Math.sin(detect * Math.PI) : 0;
    patchMaterial.emissiveIntensity = 0.1 + flare * 0.9;
    patch.scale.setScalar(1);
    haloMaterial.opacity = flare > 0 ? (1 - detect) * 0.8 : 0;
    halo.scale.setScalar(1 + smooth(detect) * 3.4);

    // Pulse: out along the pipe, back as an echo, and once more to confirm.
    let head = null;
    let direction = 1;
    if (now === 0) head = lerp(uModule, uPatch, smooth(ping));
    else if (now === 1 && detect < 0.75) {
      head = lerp(uPatch, uModule, smooth(detect / 0.75));
      direction = -1;
    } else if (now === 4 && clear > 0.3) head = lerp(uModule, uEnd, smooth((clear - 0.3) / 0.6));
    for (let i = 0; i < RINGS; i += 1) {
      if (head === null) ring(i, 0, 0);
      else {
        const u = head - direction * i * 0.0035;
        const inside = direction > 0 ? u >= uModule : u <= uPatch;
        ring(i, u, inside ? (1 - i / RINGS) * (direction > 0 ? 1 : 0.7) : 0);
      }
    }
    pulse.instanceMatrix.needsUpdate = true;

    // Design: the dose assembles over the module. Dose: it runs to the patch.
    lampMaterial.emissiveIntensity = now === 2 ? 0.4 + Math.sin(design * Math.PI * 6) * 0.3 : now === 3 ? 0.5 : 0;
    for (let i = 0; i < DOSE; i += 1) {
      const k = i / DOSE;
      let size = 0;
      if (now === 2) {
        size = smooth(design * 1.6 * DOSE * 0.25 - i * 0.35);
        const a = k * Math.PI * 2 + design * 2.2;
        dummy.position.set(-4 + Math.cos(a) * 0.55, 1.75 + Math.sin(k * 9) * 0.12, 4.25 + Math.sin(a) * 0.55);
      } else if (now === 3) {
        const go = smooth(dosing * 1.5 - k * 0.5);
        const u = lerp(uModule, uPatch + (k - 0.5) * 0.02, go);
        loop.getPointAt(u, dummy.position);
        // Falls from the module into the bore, then runs along inside it.
        const lift = (1 - smooth(go * 5)) * 1.5;
        dummy.position.y = PIPE_Y + lift;
        if (go < 0.2) {
          const a = k * Math.PI * 2 + 2.2;
          dummy.position.x = lerp(-4 + Math.cos(a) * 0.55, dummy.position.x, smooth(go * 5));
          dummy.position.z = lerp(4.25 + Math.sin(a) * 0.55, dummy.position.z, smooth(go * 5));
        }
        size = 1;
      } else if (now === 4) {
        loop.getPointAt(uPatch + (k - 0.5) * 0.02, dummy.position);
        dummy.position.y = PIPE_Y;
        size = 1 - smooth(clear * 3);
      }
      dummy.quaternion.identity();
      dummy.scale.setScalar(size);
      dummy.updateMatrix();
      dose.setMatrixAt(i, dummy.matrix);
    }
    dose.instanceMatrix.needsUpdate = true;
    renderer.render(scene, camera);
  }

  return { update };
}

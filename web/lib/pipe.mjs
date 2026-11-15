// Inside the pipe. An illustration of how a film forms, survives a biocide
// dose and comes back. Nothing here is measured.
import * as THREE from "../vendor/three.module.js";
import { clamp, colour, damp, fit, lerp, seeded, smooth } from "./tokens.mjs";

const R = 3;
const LENGTH = 150;
const TRAVEL = 92;
const CLUSTERS = 96;
const PER_CLUSTER = 8;
const MOTES = 1400;

export function mountPipe(canvas, { reduced = false } = {}) {
  const random = seeded(31);
  const voidColour = colour("--pipe-void");
  const cellColour = colour("--pipe-cell");
  const deadColour = colour("--pipe-cell-dead");
  const ochre = colour("--biofilm-ochre");
  const wave = colour("--pipe-wave");

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setClearColor(voidColour);
  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(voidColour, 0.058);
  const camera = new THREE.PerspectiveCamera(72, 1, 0.05, 120);

  scene.add(new THREE.AmbientLight(0xffffff, 0.32));
  const lamp = new THREE.PointLight(0xffffff, 15, 0, 1.6);
  scene.add(lamp);
  const ahead = new THREE.PointLight(colour("--pipe-mote"), 22, 0, 1.8);
  scene.add(ahead);

  // Grain for the wall and a soft dot for the motes, drawn once in grey.
  // Only brightness is used, so no colour is named here.
  const grain = document.createElement("canvas");
  grain.width = grain.height = 256;
  const g2 = grain.getContext("2d");
  const pixels = g2.createImageData(256, 256);
  for (let y = 0; y < 256; y += 1) {
    let streak = 200;
    for (let x = 0; x < 256; x += 1) {
      streak = clamp(streak + (random() - 0.5) * 26, 150, 255);
      const value = streak - (random() < 0.02 ? 70 : 0) - random() * 18;
      pixels.data.set([value, value, value, 255], (y * 256 + x) * 4);
    }
  }
  g2.putImageData(pixels, 0, 0);
  const grainMap = new THREE.CanvasTexture(grain);
  grainMap.wrapS = grainMap.wrapT = THREE.RepeatWrapping;
  grainMap.repeat.set(6, 14);
  grainMap.colorSpace = THREE.SRGBColorSpace;

  const dot = document.createElement("canvas");
  dot.width = dot.height = 32;
  const d2 = dot.getContext("2d");
  const glow = d2.createRadialGradient(16, 16, 0, 16, 16, 16);
  glow.addColorStop(0, "rgba(255,255,255,1)");
  glow.addColorStop(1, "rgba(255,255,255,0)");
  d2.fillStyle = glow;
  d2.fillRect(0, 0, 32, 32);
  const dotMap = new THREE.CanvasTexture(dot);

  // The wall and its weld seams.
  const bore = new THREE.CylinderGeometry(R, R, LENGTH, 96, 36, true);
  // An installed pipe is not a perfect cylinder. A little deterministic
  // waviness in the bore catches the light and gives the wall a surface.
  const borePosition = bore.attributes.position;
  for (let i = 0; i < borePosition.count; i += 1) {
    const x = borePosition.getX(i);
    const y = borePosition.getY(i);
    const z = borePosition.getZ(i);
    const theta = Math.atan2(z, x);
    const ripple =
      Math.sin(theta * 5 + y * 0.42) * 0.014 +
      Math.sin(theta * 11 - y * 0.17) * 0.006 +
      Math.sin(y * 1.3) * 0.009;
    const scale = 1 + ripple;
    borePosition.setX(i, x * scale);
    borePosition.setZ(i, z * scale);
  }
  bore.computeVertexNormals();
  const wall = new THREE.Mesh(
    bore,
    new THREE.MeshStandardMaterial({
      color: colour("--pipe-wall"),
      map: grainMap,
      bumpMap: grainMap,
      bumpScale: 0.35,
      roughnessMap: grainMap,
      side: THREE.BackSide,
      roughness: 0.62,
      metalness: 0.32,
    }),
  );
  wall.rotation.x = Math.PI / 2;
  wall.position.z = -LENGTH / 2 + 12;
  scene.add(wall);

  const seams = Math.floor(LENGTH / 6);
  const ribs = new THREE.InstancedMesh(
    new THREE.TorusGeometry(R - 0.02, 0.045, 8, 72),
    new THREE.MeshStandardMaterial({ color: colour("--pipe-rib"), roughness: 0.5, metalness: 0.5 }),
    seams,
  );
  const dummy = new THREE.Object3D();
  for (let i = 0; i < seams; i += 1) {
    dummy.position.set(0, 0, 10 - i * 6);
    dummy.updateMatrix();
    ribs.setMatrixAt(i, dummy.matrix);
  }
  scene.add(ribs);

  // Where the film will be: clusters on the wall.
  const Y = new THREE.Vector3(0, 1, 0);
  const Z = new THREE.Vector3(0, 0, 1);
  const clusters = [];
  for (let i = 0; i < CLUSTERS; i += 1) {
    clusters.push({ theta: random() * Math.PI * 2, z: -4 - (i / CLUSTERS) * (TRAVEL + 26) - random() * 1.2, size: 0.34 + random() * 0.3 });
  }

  const BLOBS = 7;
  // One irregular lump, built once and instanced with its own rotation, so a
  // cluster reads as a mass rather than a row of balls.
  const lump = new THREE.SphereGeometry(1, 16, 12);
  const lumpPosition = lump.attributes.position;
  for (let i = 0; i < lumpPosition.count; i += 1) {
    const x = lumpPosition.getX(i);
    const y = lumpPosition.getY(i);
    const z = lumpPosition.getZ(i);
    const bulge =
      1 +
      Math.sin(x * 2.7 + 1.1) * 0.17 +
      Math.sin(y * 3.1 + 2.3) * 0.14 +
      Math.sin(z * 2.3 + 0.7) * 0.16;
    lumpPosition.setXYZ(i, x * bulge, y * bulge, z * bulge);
  }
  lump.computeVertexNormals();
  const glue = new THREE.InstancedMesh(
    lump,
    new THREE.MeshStandardMaterial({ color: ochre, emissive: ochre, emissiveIntensity: 0.32, roughness: 0.55 }),
    CLUSTERS * BLOBS,
  );
  glue.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  glue.frustumCulled = false;
  scene.add(glue);
  const blobs = [];
  for (const c of clusters) {
    for (let k = 0; k < BLOBS; k += 1) {
      const theta = c.theta + (k ? (random() - 0.5) * 0.42 : 0);
      const z = c.z + (k ? (random() - 0.5) * 1.5 : 0);
      const normal = new THREE.Vector3(Math.cos(theta), Math.sin(theta), 0);
      blobs.push({
        position: normal.clone().multiplyScalar(R - 0.02).setZ(z),
        quaternion: new THREE.Quaternion()
          .setFromUnitVectors(Z, normal)
          .multiply(new THREE.Quaternion().setFromAxisAngle(Z, random() * Math.PI * 2)),
        size: c.size * (k ? 0.4 + random() * 0.5 : 1),
        delay: random() * 0.5,
      });
    }
  }

  const CELLS = CLUSTERS * PER_CLUSTER;
  const cells = new THREE.InstancedMesh(
    new THREE.CapsuleGeometry(0.055, 0.17, 4, 10),
    new THREE.MeshStandardMaterial({ roughness: 0.4 }),
    CELLS,
  );
  cells.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  cells.frustumCulled = false;
  scene.add(cells);
  const cell = [];
  for (const c of clusters) {
    for (let k = 0; k < PER_CLUSTER; k += 1) {
      const theta = c.theta + (random() - 0.5) * 0.42;
      const z = c.z + (random() - 0.5) * 1.4;
      const normal = new THREE.Vector3(Math.cos(theta), Math.sin(theta), 0);
      const around = new THREE.Vector3(-Math.sin(theta), Math.cos(theta), 0);
      const lie = random() * Math.PI;
      const direction = around.multiplyScalar(Math.sin(lie)).addScaledVector(Z, Math.cos(lie));
      const phi = random() * Math.PI * 2;
      const r = Math.sqrt(random()) * R * 0.72;
      cell.push({
        wall: normal.clone().multiplyScalar(R - 0.14 - random() * 0.05).setZ(z),
        stream: new THREE.Vector3(Math.cos(phi) * r, Math.sin(phi) * r, z + 5 + random() * 9),
        qWall: new THREE.Quaternion().setFromUnitVectors(Y, direction),
        qStream: new THREE.Quaternion().setFromEuler(new THREE.Euler(random() * 6, random() * 6, random() * 6)),
        delay: random(),
        tumble: 0.4 + random(),
      });
    }
  }

  // Water: drifting motes.
  const motePositions = new Float32Array(MOTES * 3);
  const moteSpeed = new Float32Array(MOTES);
  for (let i = 0; i < MOTES; i += 1) {
    const phi = random() * Math.PI * 2;
    const r = Math.sqrt(random()) * (R - 0.15);
    motePositions.set([Math.cos(phi) * r, Math.sin(phi) * r, -random() * 60], i * 3);
    moteSpeed[i] = 0.5 + (1 - r / R) * 1.6;
  }
  const moteGeometry = new THREE.BufferGeometry();
  moteGeometry.setAttribute("position", new THREE.BufferAttribute(motePositions, 3));
  const motes = new THREE.Points(
    moteGeometry,
    new THREE.PointsMaterial({ color: colour("--pipe-mote"), size: 0.06, map: dotMap, transparent: true, opacity: 0.8, depthWrite: false }),
  );
  motes.frustumCulled = false;
  scene.add(motes);

  // The biocide front.
  const front = new THREE.Group();
  const veil = new THREE.Mesh(
    new THREE.CircleGeometry(R, 64),
    new THREE.MeshBasicMaterial({ color: wave, transparent: true, opacity: 0.1, side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending, fog: false }),
  );
  const rim = new THREE.Mesh(
    new THREE.TorusGeometry(R - 0.06, 0.05, 8, 96),
    new THREE.MeshBasicMaterial({ color: wave, fog: false }),
  );
  const flash = new THREE.PointLight(wave, 0, 0, 1.4);
  front.add(veil, rim, flash);
  scene.add(front);

  const q = new THREE.Quaternion();
  const tint = new THREE.Color();
  let progress = 0;
  let goal = progress;
  let clock = 0;

  function update(time, dt) {
    fit(renderer, camera, canvas);
    clock = reduced ? 0 : time;
    progress = reduced ? goal : damp(progress, goal, 6, dt);
    const b = progress * 5;
    const settle = (b - 0.8) / 1.1;
    const grow = (b - 1.9) / 1.0;
    const sweep = clamp((b - 3.05) / 0.85);
    const dosing = b > 3.05;
    const regrow = (b - 4.08) / 0.8;

    const camZ = 2 - progress * TRAVEL;
    camera.position.set(Math.sin(clock * 0.21) * 0.35, Math.cos(clock * 0.17) * 0.28 - 0.1, camZ);
    camera.rotation.set(Math.sin(clock * 0.13) * 0.02, Math.sin(clock * 0.19) * 0.03, Math.sin(clock * 0.11) * 0.05);
    lamp.position.set(0, 0.4, camZ + 0.5);
    ahead.position.set(0, 0, camZ - 14);

    const frontZ = camZ + 7 - sweep * 62 - clamp(regrow + 0.1) * 80;
    front.visible = dosing && sweep < 1;
    front.position.z = frontZ;
    flash.intensity = front.visible ? 60 * Math.sin(sweep * Math.PI) + 12 : 0;

    for (let i = 0; i < cell.length; i += 1) {
      const c = cell[i];
      const s = smooth(settle * 1.5 - c.delay * 0.5);
      const kill = dosing ? smooth((c.wall.z - frontZ) / 2.5) : 0;
      const back = smooth(regrow * 1.7 - c.delay * 0.7);
      const size = Math.max(1 - smooth((kill - 0.35) / 0.65), back);
      dummy.position.lerpVectors(c.stream, c.wall, s);
      if (s < 1) {
        dummy.position.x += Math.sin(clock * c.tumble + i) * 0.12 * (1 - s);
        dummy.position.y += Math.cos(clock * c.tumble * 0.8 + i) * 0.12 * (1 - s);
      }
      q.setFromAxisAngle(Y, clock * c.tumble * (1 - s)).premultiply(c.qStream);
      dummy.quaternion.slerpQuaternions(q, c.qWall, s);
      dummy.scale.setScalar(size);
      dummy.updateMatrix();
      cells.setMatrixAt(i, dummy.matrix);
      tint.copy(cellColour).lerp(deadColour, clamp(kill * 2.2) * (1 - back));
      cells.setColorAt(i, tint);
    }
    cells.instanceMatrix.needsUpdate = true;
    cells.instanceColor.needsUpdate = true;

    for (let i = 0; i < blobs.length; i += 1) {
      const g = blobs[i];
      const amount = Math.pow(smooth(grow * 1.5 - g.delay), 0.7) * (1 + clamp(regrow) * 0.12);
      dummy.position.copy(g.position);
      dummy.quaternion.copy(g.quaternion);
      dummy.scale.set(g.size * amount, g.size * amount, g.size * 0.34 * amount);
      dummy.updateMatrix();
      glue.setMatrixAt(i, dummy.matrix);
    }
    glue.instanceMatrix.needsUpdate = true;

    if (!reduced) {
      for (let i = 0; i < MOTES; i += 1) {
        let z = motePositions[i * 3 + 2] - moteSpeed[i] * dt;
        if (z < camZ - 60) z += 64;
        if (z > camZ + 4) z -= 64;
        motePositions[i * 3 + 2] = z;
      }
    } else {
      for (let i = 0; i < MOTES; i += 1) {
        const z = motePositions[i * 3 + 2];
        motePositions[i * 3 + 2] = camZ - ((((camZ - z) % 60) + 60) % 60);
      }
    }
    moteGeometry.attributes.position.needsUpdate = true;
    renderer.render(scene, camera);
  }

  return {
    update,
    progress(value) {
      // Scroll drives the beats in both modes. Under reduced motion the scene
      // simply does not animate between them: the clock stays still.
      goal = lerp(0, 1, clamp(value));
    },
  };
}

// The enzyme card: a short looping film of the process that produced the
// design, in six beats. Everything is a function of (beat, seconds into the
// beat), so the loop is seamless and a jump lands on a known frame.
//
// Real, from data/enzyme.json: the fold (Boltz prediction), the cutting site
// (literature), the eight designs and the positions each one changed
// (HyperMPNN), and the count of rejected proposals. Illustration: the motion,
// the cloud, the layering of the designs, the heat, the strand, and scoring
// shown as beads thrown off the cutting site. The page tags each beside the
// canvas.
import * as THREE from "../vendor/three.module.js";
import { clamp, colour, damp, fit, lerp, seeded, smooth, token } from "./tokens.mjs";

// Seconds per beat: read the film, pick the enzyme, build it, redesign it,
// score each one, the chosen one.
export const BEATS = [5, 5, 10.5, 7, 7.5, 7.5];

const SUB = 4; // samples per residue along the curve through the chain
const RADIAL = 9; // sides of the main tube
const GHOST_RADIAL = 6; // sides of a ghosted design
const STRAND = 64; // beads per strand of the thing the enzyme cuts
const LEAD = 18; // residues that fly in ahead of the growing chain

function catmull(a, b, c, d, t) {
  const t2 = t * t;
  const t3 = t2 * t;
  return 0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (3 * b - a - 3 * c + d) * t3);
}

// Scratch, shared by every tube. Nothing here survives a call.
const tangent = new THREE.Vector3();
const normal = new THREE.Vector3();
const binormal = new THREE.Vector3();
const carried = new THREE.Vector3();
const offset = new THREE.Vector3();
const tint = new THREE.Color();

// A tube swept along the curve through n residues. The topology is built once
// and only positions, normals and colours move, so a frame allocates nothing.
function makeTube(n, radial) {
  const rings = (n - 1) * SUB + 1;
  const count = rings * radial;
  const position = new Float32Array(count * 3);
  const normals = new Float32Array(count * 3);
  const colours = new Float32Array(count * 3);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(position, 3));
  geometry.setAttribute("normal", new THREE.BufferAttribute(normals, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colours, 3));
  const index = new Uint32Array((rings - 1) * radial * 6);
  for (let r = 0, k = 0; r < rings - 1; r += 1) {
    for (let s = 0; s < radial; s += 1) {
      const a = r * radial + s;
      const b = r * radial + ((s + 1) % radial);
      index[k++] = a; index[k++] = a + radial; index[k++] = b;
      index[k++] = b; index[k++] = a + radial; index[k++] = b + radial;
    }
  }
  geometry.setIndex(new THREE.BufferAttribute(index, 1));
  const curve = new Float32Array(rings * 3);
  const cos = new Float32Array(radial);
  const sin = new Float32Array(radial);
  for (let s = 0; s < radial; s += 1) {
    cos[s] = Math.cos((s / radial) * Math.PI * 2);
    sin[s] = Math.sin((s / radial) * Math.PI * 2);
  }

  // points: n * 3 residue positions. width(residue, ring) gives the radius,
  // shade(residue) leaves the colour in `tint`.
  function sweep(points, width, shade) {
    let b = 0;
    for (let i = 0; i < n - 1; i += 1) {
      const i0 = Math.max(0, i - 1) * 3;
      const i1 = i * 3;
      const i2 = (i + 1) * 3;
      const i3 = Math.min(n - 1, i + 2) * 3;
      for (let s = 0; s < SUB; s += 1) {
        const u = s / SUB;
        for (let k = 0; k < 3; k += 1) {
          curve[b * 3 + k] = catmull(points[i0 + k], points[i1 + k], points[i2 + k], points[i3 + k], u);
        }
        b += 1;
      }
    }
    for (let k = 0; k < 3; k += 1) curve[b * 3 + k] = points[(n - 1) * 3 + k];

    carried.set(0, 1, 0);
    for (let r = 0; r < rings; r += 1) {
      const here = r * 3;
      const back = Math.max(0, r - 1) * 3;
      const ahead = Math.min(rings - 1, r + 1) * 3;
      tangent
        .set(curve[ahead] - curve[back], curve[ahead + 1] - curve[back + 1], curve[ahead + 2] - curve[back + 2])
        .normalize();
      // Carry the frame along the curve so the tube does not twist on itself.
      normal.copy(carried).addScaledVector(tangent, -carried.dot(tangent));
      if (normal.lengthSq() < 1e-6) normal.set(tangent.y, -tangent.x, 0);
      normal.normalize();
      carried.copy(normal);
      binormal.crossVectors(tangent, normal);

      const residue = Math.min(n - 1, Math.round(r / SUB));
      const thickness = width(residue, r);
      shade(residue);
      for (let s = 0; s < radial; s += 1) {
        const v = (r * radial + s) * 3;
        offset.copy(normal).multiplyScalar(cos[s]).addScaledVector(binormal, sin[s]);
        normals[v] = offset.x;
        normals[v + 1] = offset.y;
        normals[v + 2] = offset.z;
        position[v] = curve[here] + offset.x * thickness;
        position[v + 1] = curve[here + 1] + offset.y * thickness;
        position[v + 2] = curve[here + 2] + offset.z * thickness;
        colours[v] = tint.r;
        colours[v + 1] = tint.g;
        colours[v + 2] = tint.b;
      }
    }
    geometry.attributes.position.needsUpdate = true;
    geometry.attributes.normal.needsUpdate = true;
    geometry.attributes.color.needsUpdate = true;
  }

  return { geometry, rings, sweep, perRing: radial * 6 };
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
  const sitePositions = data.active_site?.positions ?? [];
  const site = new Float32Array(n);
  const siteCentre = new THREE.Vector3();
  for (const position of sitePositions) {
    site[position - 1] = 1;
    siteCentre.add(at(position - 1));
  }
  siteCentre.divideScalar(Math.max(1, sitePositions.length));

  // The designs, as the run gave them. The chosen one is drawn on the main
  // chain; the others are the ghosts behind it.
  const mask = (positions) => {
    const out = new Float32Array(n);
    for (const position of positions) out[position - 1] = 1;
    return out;
  };
  const variants = data.variants ?? [];
  const chosenId = data.engineered_region?.variant;
  const chosen = variants.find((v) => v.id === chosenId);
  const region = mask(chosen?.changed_positions ?? data.engineered_region?.positions ?? []);
  const others = variants.filter((v) => v !== chosen).map((v) => mask(v.changed_positions));

  // How firmly each residue holds when the chain heats.
  const hold = new Float32Array(n);
  for (let i = 0; i < n; i += 1) {
    const near = 1 - clamp((at(i).distanceTo(siteCentre) - 7) / 9);
    hold[i] = Math.max(near, region[i] * 0.8);
  }
  return { n, fold, site, sitePositions, siteCentre, region, others, hold, rejected: data.design?.rejected_count ?? 0 };
}

export function mountFilm(canvas, data, { reduced = false, onBeat = () => {} } = {}) {
  const model = prepare(data);
  const { n } = model;
  const random = seeded(7);
  const surface = colour("--card-surface");
  const chain = colour("--chain");
  const chainPale = surface.clone().lerp(chain, 0.35);
  const teal = colour("--teal-protein");
  const cobalt = colour("--cobalt-hydro");
  const ochre = colour("--biofilm-ochre");

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(surface, 135, 215);
  const camera = new THREE.PerspectiveCamera(30, 1, 1, 600);
  scene.add(new THREE.HemisphereLight(0xffffff, new THREE.Color(token("--border-strong")), 1.5));
  const key = new THREE.DirectionalLight(0xffffff, 1.9);
  key.position.set(-40, 60, 80);
  scene.add(key);

  const rig = new THREE.Group(); // placement on screen
  const spin = new THREE.Group(); // rotation
  rig.add(spin);
  scene.add(rig);

  // Turn the cutting site towards the viewer, a little to one side. Anything
  // described in screen terms is carried into the fold's own frame with
  // `local`, so it stays put on screen whatever the fold's orientation.
  const outward = model.siteCentre.clone().normalize();
  const outwardWorld = new THREE.Vector3(0.62, 0.12, 0.77).normalize();
  const rest = new THREE.Quaternion().setFromUnitVectors(outward, outwardWorld);
  const restInverse = rest.clone().invert();
  const local = (x, y, z) => new THREE.Vector3(x, y, z).applyQuaternion(restInverse);

  // The chosen design: the main chain.
  const tube = makeTube(n, RADIAL);
  const mesh = new THREE.Mesh(
    tube.geometry,
    new THREE.MeshStandardMaterial({ roughness: 0.38, metalness: 0.03, vertexColors: true }),
  );
  mesh.frustumCulled = false;
  spin.add(mesh);

  // Thickness follows the model's own confidence: the uncertain leading tail
  // tapers away rather than swinging about at full weight.
  const radius = new Float32Array(n);
  for (let i = 0; i < n; i += 1) {
    radius[i] = lerp(0.3, 1.3, clamp((data.confidence[i] - 50) / 38) ** 0.85);
  }

  // The other designs: the same predicted shape, each with its own changed
  // positions in cobalt and the same untouched cutting site in teal. They do
  // not move, so each is swept once.
  const layer = local(-7.5, 3.1, -10); // one step back in the stack
  const ghosts = model.others.map((changed, k) => {
    const ghost = makeTube(n, GHOST_RADIAL);
    ghost.sweep(
      model.fold,
      (residue) => radius[residue] * (0.82 + model.site[residue] * 0.4),
      (residue) => {
        tint.copy(chainPale).lerp(chain, residue / n);
        if (changed[residue]) tint.copy(cobalt);
        if (model.site[residue]) tint.copy(teal);
      },
    );
    const material = new THREE.MeshStandardMaterial({
      roughness: 0.5,
      vertexColors: true,
      transparent: true,
      opacity: 0,
    });
    const ghostMesh = new THREE.Mesh(ghost.geometry, material);
    ghostMesh.frustumCulled = false;
    ghostMesh.visible = false;
    ghostMesh.renderOrder = 10 - k;
    spin.add(ghostMesh);
    return { mesh: ghostMesh, material };
  });

  // The enzyme before it is built: one bead per residue, as a cloud.
  const near = new Float32Array(n * 3);
  const far = new Float32Array(n * 3);
  const phase = new Float32Array(n * 3);
  const arrive = local(46, 30, 10);
  for (let i = 0; i < n; i += 1) {
    const v = new THREE.Vector3(random() - 0.5, random() - 0.5, random() - 0.5).normalize();
    v.multiplyScalar(15 + random() * 21);
    near.set([v.x, v.y, v.z], i * 3);
    v.multiplyScalar(2.3).add(arrive);
    far.set([v.x, v.y, v.z], i * 3);
    phase.set([random() * 6.28, random() * 6.28, random() * 6.28], i * 3);
  }
  const beads = new THREE.InstancedMesh(
    new THREE.SphereGeometry(1, 12, 10),
    new THREE.MeshStandardMaterial({ roughness: 0.45 }),
    n,
  );
  beads.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  beads.frustumCulled = false;
  for (let i = 0; i < n; i += 1) beads.setColorAt(i, tint.copy(chainPale).lerp(chain, 0.25 + (i / n) * 0.75));
  spin.add(beads);

  // What the enzyme cuts: a two-stranded twist of the glue, in ochre.
  const axis = local(0.92, 0.2, -0.3);
  axis.addScaledVector(outward, -axis.dot(outward)).normalize();
  const side = outward.clone().cross(axis).normalize();
  const strand = new THREE.InstancedMesh(
    new THREE.SphereGeometry(1, 10, 8),
    new THREE.MeshStandardMaterial({ roughness: 0.5, color: ochre }),
    STRAND * 2,
  );
  strand.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  strand.frustumCulled = false;
  spin.add(strand);
  const rungs = new THREE.InstancedMesh(
    new THREE.CylinderGeometry(1, 1, 1, 6),
    new THREE.MeshStandardMaterial({ roughness: 0.6, color: surface.clone().lerp(ochre, 0.55) }),
    STRAND / 2,
  );
  rungs.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  rungs.frustumCulled = false;
  spin.add(rungs);

  // The rejected proposals: one bead each, thrown at the cutting site and
  // thrown off it. The count is the real one.
  const rejects = new THREE.InstancedMesh(
    new THREE.SphereGeometry(1, 10, 8),
    new THREE.MeshStandardMaterial({ roughness: 0.55, color: colour("--ink-muted") }),
    Math.max(1, model.rejected),
  );
  rejects.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  rejects.frustumCulled = false;
  rejects.visible = false;
  spin.add(rejects);
  const gravity = local(0, -46, 0);
  const shots = Array.from({ length: model.rejected }, (_, j) => {
    const position = model.sitePositions[j % Math.max(1, model.sitePositions.length)] ?? 1;
    const hit = new THREE.Vector3().fromArray(model.fold, (position - 1) * 3).addScaledVector(outward, 2.2);
    const from = local(34 + random() * 30, 26 + random() * 22, 18 + random() * 24).add(hit);
    const away = local((random() - 0.35) * 30, 6 + random() * 16, 10 + random() * 14);
    return { hit, from, away };
  });

  const live = new Float32Array(n * 3);
  const stage = new THREE.Vector3(); // where the strand rests when it is alone
  const origin = new THREE.Vector3();
  const beadA = new THREE.Vector3();
  const beadB = new THREE.Vector3();
  const up = new THREE.Vector3(0, 1, 0);
  const dummy = new THREE.Object3D();
  const turn = new THREE.Quaternion();
  const euler = new THREE.Euler();
  const pointer = { x: 0, y: 0, tx: 0, ty: 0 };
  const base = { z: 146, x: 4, y: 3 };

  // The film.
  let beat = 0;
  let seconds = reduced ? BEATS[0] : 0;
  let playing = !reduced;
  let fresh = true; // true until the loop has come round, and after a jump
  let heat = 0;
  let heatTarget = 0;
  let clock = 0;
  let sized = false;
  const f = { present: 0, build: 1, cloud: 0, gather: 0, site: 0, region: 0, dock: 0, strand: 0, stage: 1, wide: 0, push: 0 };

  // Every parameter of the picture, from the beat and the seconds into it.
  // Each beat starts exactly where the one before it ended.
  function score() {
    const t = seconds;
    const e = (a, b) => smooth((t - a) / (b - a));
    f.present = 1; f.build = 1; f.cloud = 0; f.gather = 1; f.site = 1; f.region = 1;
    f.dock = 1; f.strand = 0; f.stage = 0; f.wide = 0; f.push = 0;
    if (beat === 0) {
      // The chosen design thins away and the camera eases back; the glue
      // strand grows in alone.
      f.present = fresh ? 0 : 1 - e(0, 1.5);
      f.push = fresh ? 0 : 1 - e(0.1, 2.3);
      f.strand = fresh ? e(0, 1.3) : e(1.1, 2.7);
      f.stage = 1; f.dock = 0;
    } else if (beat === 1) {
      f.present = 0; f.build = 0; f.site = 0; f.region = 0; f.dock = 0;
      f.strand = 1; f.stage = 1;
      f.cloud = e(0, 1.1); f.gather = e(0, 4.4);
    } else if (beat === 2) {
      const b = clamp((t - 1.2) / 6.2);
      f.build = lerp(b, smooth(b), 0.5);
      f.cloud = 1; f.region = 0; f.strand = 1;
      f.stage = 1 - e(0, 1.9);
      f.site = e(7.2, 8.2);
      f.dock = e(7.8, 10.1);
    } else if (beat === 3) {
      f.strand = 1 - e(0, 1.2);
      f.region = e(0.5, 1.7);
      f.wide = e(0.8, 3.4);
    } else if (beat === 4) {
      f.wide = 1;
    } else {
      f.wide = 1 - e(0, 2.4);
      f.push = e(0.7, 3.6);
    }
  }

  function place(w, h) {
    const wide = w / h > 0.95;
    base.z = wide ? 146 : 172;
    base.y = wide ? 3 : 9;
    stage.set(-base.x, 1 - base.y, 12).applyQuaternion(restInverse);
  }

  function update(time, dt) {
    if (fit(renderer, camera, canvas) || !sized) {
      place(canvas.clientWidth, canvas.clientHeight);
      sized = true;
    }
    clock = reduced ? 1 : time;
    if (playing && !reduced) {
      seconds += dt;
      if (seconds >= BEATS[beat]) {
        seconds -= BEATS[beat];
        beat = (beat + 1) % BEATS.length;
        fresh = false;
        onBeat(beat);
      }
    }
    score();
    heat = reduced ? heatTarget : damp(heat, beat === 5 ? heatTarget : 0, 4, dt);

    // The rejected proposals, and the jolt each one gives the cutting site.
    let kick = 0;
    rejects.visible = beat === 4 && model.rejected > 0;
    if (rejects.visible) {
      for (let j = 0; j < shots.length; j += 1) {
        const shot = shots[j];
        const t = seconds - (1.7 + j * 0.06);
        let size = 0;
        if (t > 0 && t < 2.4) {
          if (t < 0.7) {
            const p = t / 0.7;
            dummy.position.lerpVectors(shot.from, shot.hit, p * p);
            size = smooth(p * 3);
          } else {
            const fall = t - 0.7;
            dummy.position
              .copy(shot.hit)
              .addScaledVector(shot.away, fall)
              .addScaledVector(gravity, 0.5 * fall * fall);
            size = 1 - smooth((fall - 0.8) / 0.9);
            kick = Math.max(kick, 1 - fall / 0.3);
          }
        }
        dummy.quaternion.identity();
        dummy.scale.setScalar(1.25 * size);
        dummy.updateMatrix();
        rejects.setMatrixAt(j, dummy.matrix);
      }
      rejects.instanceMatrix.needsUpdate = true;
    }

    // Scoring passes over the family, front to back. Each design brightens as
    // it is read.
    const read = (k) => (beat === 4 ? smooth(1 - Math.abs(seconds - (0.5 + k * 0.42)) / 0.45) : 0);
    const siteGlow = f.site + Math.max(kick, read(0)) * 0.9;

    // Residues: cloud to fold as the chain grows past them, heat on top.
    const front = lerp(-LEAD, n + 2, f.build);
    for (let i = 0; i < n; i += 1) {
      const a = smooth((front + LEAD - i) / LEAD);
      const taken = smooth((front - i + 1.5) / 3);
      const shake = heat * (1 - model.hold[i]) * 3.4;
      for (let k = 0; k < 3; k += 1) {
        const j = i * 3 + k;
        const drift = Math.sin(clock * 0.9 + phase[j]) * 1.6;
        const wobble =
          Math.sin(clock * 5.1 + phase[j] + i * 0.31) * 0.6 + Math.sin(clock * 8.3 + phase[j] * 1.7 + i * 0.12) * 0.4;
        const cloud = lerp(far[j], near[j], f.gather) + drift * (1 - a);
        live[j] = lerp(cloud, model.fold[j], a) + wobble * shake;
      }
      dummy.position.set(live[i * 3], live[i * 3 + 1], live[i * 3 + 2]);
      dummy.quaternion.identity();
      dummy.scale.setScalar(f.cloud * (1 - taken) * lerp(0.95, 1.25, a));
      dummy.updateMatrix();
      beads.setMatrixAt(i, dummy.matrix);
    }
    beads.visible = f.cloud > 0.001 && f.build < 1;
    beads.instanceMatrix.needsUpdate = true;

    // The chain: drawn up to the growing end, which tapers to a point.
    const tip = front * SUB;
    const growing = f.build < 1;
    mesh.visible = f.present > 0.001 && tip > 0;
    if (mesh.visible) {
      tube.sweep(
        live,
        (residue, ring) =>
          radius[residue] *
          f.present *
          (growing ? smooth((tip - ring) / 7) : 1) *
          (1 + model.site[residue] * siteGlow * 0.7 + model.region[residue] * f.region * 0.12),
        (residue) => {
          tint.copy(chainPale).lerp(chain, residue / n);
          if (model.region[residue]) tint.lerp(cobalt, f.region);
          if (model.site[residue]) tint.lerp(teal, clamp(siteGlow));
        },
      );
      const drawn = growing ? clamp(Math.ceil(tip), 0, tube.rings - 1) : tube.rings - 1;
      tube.geometry.setDrawRange(0, drawn * tube.perRing);
    }

    // The family of designs, layering up behind the chosen one.
    for (let k = 0; k < ghosts.length; k += 1) {
      const ghost = ghosts[k];
      let shown = 0;
      let gone = 0;
      if (beat === 3) shown = smooth((seconds - (1.3 + k * 0.55)) / 1.0);
      else if (beat === 4) shown = 1;
      else if (beat === 5) {
        gone = smooth((seconds - k * 0.08) / 1.7);
        shown = 1 - gone;
      }
      ghost.mesh.visible = shown > 0.001;
      if (!ghost.mesh.visible) continue;
      ghost.material.opacity = shown * (0.46 + read(k + 1) * 0.5);
      ghost.mesh.position.copy(layer).multiplyScalar((k + 1) * (0.5 + 0.5 * shown + gone * 0.8));
    }

    drawStrand();

    // Camera: back for the family, in for the chosen one.
    camera.position.set(0, 0, base.z * (1 + f.wide * 0.36 - f.push * 0.17));
    rig.position.set(base.x + f.wide * 20 + f.push * 6, base.y - f.wide * 1 + f.push * 6, 0);
    scene.fog.near = camera.position.z - 20;
    scene.fog.far = camera.position.z + 62 + f.wide * 60;

    pointer.x = damp(pointer.x, pointer.tx, 3, reduced ? 1 : dt);
    pointer.y = damp(pointer.y, pointer.ty, 3, reduced ? 1 : dt);
    euler.set(Math.sin(clock * 0.23) * 0.07 + pointer.y * 0.18, Math.sin(clock * 0.31) * 0.22 + pointer.x * 0.3, 0);
    spin.quaternion.copy(turn.setFromEuler(euler)).multiply(rest);
    renderer.render(scene, camera);
  }

  // A two-stranded twist. Alone on stage it lies across the frame; then it
  // slides into the cutting site and parts there.
  function drawStrand() {
    strand.visible = f.strand > 0.001;
    rungs.visible = strand.visible;
    if (!strand.visible) return;
    const staged = smooth(f.stage);
    const d = smooth(f.dock);
    const cut = smooth((f.dock - 0.82) / 0.18);
    const long = lerp(1, 1.5, staged);
    origin.copy(model.siteCentre).addScaledVector(outward, lerp(46, 7.5, d)).lerp(stage, staged);
    for (let i = 0; i < STRAND; i += 1) {
      const u = i / (STRAND - 1) - 0.5;
      const along = u * 46 * long + Math.sign(u) * cut * 3.2;
      const lift = Math.abs(u) * cut * 9;
      // Grow from the middle outwards, and shrink back the same way.
      const size = smooth(f.strand * 2.2 - Math.abs(u) * 2.2);
      for (let s = 0; s < 2; s += 1) {
        const angle = u * 9.5 * long + s * Math.PI + clock * 0.25;
        const bead = s === 0 ? beadA : beadB;
        bead
          .copy(origin)
          .addScaledVector(axis, along)
          .addScaledVector(side, Math.cos(angle) * 3.4)
          .addScaledVector(outward, Math.sin(angle) * 3.4 + lift);
        dummy.position.copy(bead);
        dummy.quaternion.identity();
        dummy.scale.setScalar(0.78 * size);
        dummy.updateMatrix();
        strand.setMatrixAt(s * STRAND + i, dummy.matrix);
      }
      if (i % 2 === 0) {
        offset.subVectors(beadB, beadA);
        const length = offset.length();
        dummy.position.addVectors(beadA, beadB).multiplyScalar(0.5);
        dummy.quaternion.setFromUnitVectors(up, offset.divideScalar(length || 1));
        dummy.scale.set(0.24 * size, length, 0.24 * size);
        dummy.updateMatrix();
        rungs.setMatrixAt(i / 2, dummy.matrix);
      }
    }
    strand.instanceMatrix.needsUpdate = true;
    rungs.instanceMatrix.needsUpdate = true;
  }

  return {
    update,
    // Start a beat from its first frame and keep playing.
    jump(index) {
      beat = clamp(Math.round(index), 0, BEATS.length - 1);
      fresh = true;
      seconds = reduced ? BEATS[beat] : 0;
      playing = !reduced;
      onBeat(beat);
    },
    // Rest on the last frame of a beat.
    hold(index) {
      beat = clamp(Math.round(index), 0, BEATS.length - 1);
      fresh = true;
      seconds = BEATS[beat];
      playing = false;
      onBeat(beat);
    },
    play() {
      playing = !reduced;
    },
    pause() {
      playing = false;
    },
    // 0 to 1. Only the chosen design, in the last beat, is heated.
    heat(value) {
      heatTarget = clamp(value);
    },
    point(x, y) {
      if (reduced) return;
      pointer.tx = x;
      pointer.ty = y;
    },
  };
}

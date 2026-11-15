// Stylised sculptures accompany real, cited enzyme examples. The parametric
// shapes are visual concepts, not protein coordinates or model predictions.
import * as THREE from "../vendor/three.module.js";
import { colour, damp, fit } from "./tokens.mjs";

const TAU = Math.PI * 2;

class ConceptCurve extends THREE.Curve {
  constructor(index, strand = 0) { super(); this.index = index; this.strand = strand; }
  getPoint(t, point = new THREE.Vector3()) {
    const u = t * TAU;
    const i = this.index;
    const phase = i * 0.48 + this.strand * 0.65;
    const turns = i === 4 ? 3 : 2;
    const folds = [3, 5, 4, 3, 2][i];
    const radius = 1.18 + 0.42 * Math.cos(folds * u + phase);
    return point.set(
      Math.cos(turns * u + phase) * radius * (i === 2 ? 0.78 : 1),
      Math.sin(folds * u + phase) * (i === 2 ? 1.65 : 1.22) + 0.2 * Math.cos(u),
      Math.sin(turns * u + phase) * radius * 0.88,
    );
  }
}

export function mountConcepts(canvas, { reduced = false, concepts } = {}) {
  if (!Array.isArray(concepts) || concepts.length !== 5) throw new Error('Five enzyme examples are required');
  const CONCEPTS = concepts;
  const STEP = TAU / CONCEPTS.length;
  const wrap = (value) => ((value % CONCEPTS.length) + CONCEPTS.length) % CONCEPTS.length;
  const root = canvas.closest('.gallery');
  const tabs = [...root.querySelectorAll('[data-concept]')];
  let turn = 0;
  let target = 0;
  let angle = 0;
  let dragging = false;
  let down = null;
  let wheelDelta = 0;
  let lastWheel = 0;
  let wheelAt = 0;
  let renderer = null;
  let scene, camera, models, raycaster;

  function describe() {
    const selected = wrap(turn);
    const concept = CONCEPTS[selected];
    root.dataset.active = String(selected);
    root.querySelector('[data-concept-name]').textContent = concept.name;
    root.querySelector('[data-concept-family]').textContent = concept.family;
    root.querySelector('[data-concept-description]').textContent = concept.description;
    const source = root.querySelector('[data-concept-source]');
    source.href = concept.source.url;
    source.title = concept.source.title;
    source.setAttribute('aria-label', `Research paper on ${concept.name} (opens in a new tab)`);
    root.querySelector('[data-concept-count]').textContent = `${String(selected + 1).padStart(2, '0')} / 05`;
    tabs.forEach((tab, index) => tab.setAttribute('aria-pressed', String(index === selected)));
    canvas.setAttribute('aria-label', `${concept.name}, concept ${selected + 1} of 5. Use left and right arrows to explore.`);
    target = -turn * STEP;
  }
  function advance(direction) { turn += direction; describe(); }
  function select(index) {
    let difference = wrap(index - wrap(turn));
    if (difference > CONCEPTS.length / 2) difference -= CONCEPTS.length;
    turn += difference;
    describe();
  }
  tabs.forEach((tab) => tab.addEventListener('click', () => select(Number(tab.dataset.concept))));
  root.querySelectorAll('[data-concept-direction]').forEach((button) => {
    button.addEventListener('click', () => advance(Number(button.dataset.conceptDirection)));
  });
  canvas.addEventListener('keydown', (event) => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    if (event.key === 'Home') select(0);
    else if (event.key === 'End') select(CONCEPTS.length - 1);
    else advance(event.key === 'ArrowRight' ? 1 : -1);
  });
  canvas.addEventListener('wheel', (event) => {
    if (event.ctrlKey) return;
    const delta = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? event.deltaX : event.deltaY;
    const index = wrap(turn);
    // Let page scrolling resume at either end rather than trapping the visitor.
    if ((delta > 0 && index === CONCEPTS.length - 1) || (delta < 0 && index === 0)) return;
    event.preventDefault();
    const now = performance.now();
    if (now - wheelAt > 180) wheelDelta = 0;
    wheelAt = now;
    wheelDelta += delta * (event.deltaMode === 1 ? 16 : 1);
    if (Math.abs(wheelDelta) >= 35 && now - lastWheel > 380) {
      advance(Math.sign(wheelDelta));
      wheelDelta = 0;
      lastWheel = performance.now();
    }
  }, { passive: false });
  canvas.addEventListener('pointerdown', (event) => {
    if (event.button !== 0) return;
    down = { x: event.clientX, y: event.clientY, angle: target };
    dragging = false;
    canvas.setPointerCapture(event.pointerId);
    canvas.focus({ preventScroll: true });
  });
  canvas.addEventListener('pointermove', (event) => {
    if (!down) return;
    const dx = event.clientX - down.x;
    const dy = event.clientY - down.y;
    if (!dragging && Math.abs(dx) > 9 && Math.abs(dx) > Math.abs(dy)) {
      dragging = true;
      root.classList.add('is-dragging');
    }
    if (dragging) target = down.angle + dx / Math.max(320, canvas.clientWidth) * TAU;
  });
  function release(event, cancelled = false) {
    if (!down) return;
    if (dragging) { turn = Math.round(-target / STEP); describe(); }
    else if (!cancelled && renderer) {
      const rect = canvas.getBoundingClientRect();
      const pointer = new THREE.Vector2(
        (event.clientX - rect.left) / rect.width * 2 - 1,
        -(event.clientY - rect.top) / rect.height * 2 + 1,
      );
      raycaster.setFromCamera(pointer, camera);
      const hit = raycaster.intersectObjects(models, true)[0];
      if (hit) {
        let object = hit.object;
        while (object && object.userData.concept === undefined) object = object.parent;
        if (object) select(object.userData.concept);
      }
    }
    down = null;
    dragging = false;
    root.classList.remove('is-dragging');
  }
  canvas.addEventListener('pointerup', (event) => release(event));
  canvas.addEventListener('pointercancel', (event) => release(event, true));
  describe();

  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  } catch {
    root.classList.add('no-webgl');
    return { update() {} };
  }
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(34, 1, 0.1, 100);
  scene.add(new THREE.HemisphereLight(colour('--card-surface'), colour('--border-strong'), 2.1));
  const key = new THREE.DirectionalLight(colour('--card-surface'), 2.8);
  key.position.set(-4, 8, 10);
  scene.add(key);
  const rim = new THREE.DirectionalLight(colour('--cobalt-tint'), 2.3);
  rim.position.set(8, 3, -3);
  scene.add(rim);
  raycaster = new THREE.Raycaster();

  models = CONCEPTS.map((concept, index) => {
    const group = new THREE.Group();
    group.userData.concept = index;
    const body = new THREE.Group();
    const material = new THREE.MeshPhysicalMaterial({
      color: colour(concept.colour), roughness: 0.26, metalness: 0.08,
      clearcoat: 0.5, transparent: true,
    });
    body.add(new THREE.Mesh(new THREE.TubeGeometry(new ConceptCurve(index), 240, 0.145, 10, true), material));
    if (index === 1 || index === 3) {
      body.add(new THREE.Mesh(new THREE.TubeGeometry(new ConceptCurve(index, 1), 200, 0.105, 8, true), material));
    }
    group.add(body);
    group.userData.body = body;
    group.userData.material = material;
    scene.add(group);
    return group;
  });

  let laidOut = false;
  return {
    update(time, dt) {
      if (fit(renderer, camera, canvas) || !laidOut) {
        camera.position.set(0, 2.1, canvas.clientWidth / canvas.clientHeight > 1.25 ? 22 : 28);
        camera.lookAt(0, 0, 0);
        laidOut = true;
      }
      angle = reduced ? target : damp(angle, target, dragging ? 18 : 6, dt);
      models.forEach((model, index) => {
        const rotation = index * STEP + angle;
        const front = (Math.cos(rotation) + 1) / 2;
        model.position.set(Math.sin(rotation) * 6.2, -0.3 + front * 0.55, Math.cos(rotation) * 4.5);
        model.scale.setScalar(0.85 + front * 0.3);
        model.userData.body.rotation.set(
          0.15 + (reduced ? 0 : Math.sin(time * 0.35 + index) * 0.12),
          index * 0.75 + (reduced ? 0 : time * 0.12),
          index * 0.17,
        );
        model.userData.material.opacity = 0.25 + front * 0.75;
        model.userData.material.depthWrite = front > 0.8;
      });
      renderer.render(scene, camera);
    },
  };
}

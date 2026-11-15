// Sonazyme front page. Wires the scroll, the scenes and the small controls.
// Served under a strict CSP: nothing here writes an inline style. State goes
// to the page through classes and data attributes only.
import { notice } from "./lib/data.mjs";
import { mountOverhead } from "./lib/overhead.mjs";
import { mountPipe } from "./lib/pipe.mjs";
import { mountProtein } from "./lib/protein.mjs";
import { createScroll, pinProgress } from "./lib/scroll.mjs";
import { mountSonar } from "./lib/sonar.mjs";
import { mountLocalStructures } from "./lib/structures.mjs";

const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const $ = (selector, root = document) => root.querySelector(selector);
const scroll = createScroll({ reduced });
const scenes = [];

function register(canvas, mount) {
  if (!canvas) return null;
  try {
    const scene = mount(canvas);
    const entry = { canvas, scene, visible: false, entered: false };
    scenes.push(entry);
    return scene;
  } catch (error) {
    console.warn("Scene could not start", error);
    canvas.closest("section")?.classList.add("no-webgl");
    return null;
  }
}

// Footer notice comes from the same module the rest of the app uses.
const noticeNode = $("[data-notice]");
if (noticeNode) noticeNode.textContent = notice;

// Anchor links ease to their target and still move focus and the address.
for (const link of document.querySelectorAll('a[href^="#"]')) {
  link.addEventListener("click", (event) => {
    const target = document.getElementById(link.hash.slice(1));
    if (!target) return;
    event.preventDefault();
    scroll.to(target);
    history.pushState(null, "", link.hash);
    if (!target.hasAttribute("tabindex")) target.setAttribute("tabindex", "-1");
    target.focus({ preventScroll: true });
  });
}

// Sections ease in once.
const reveal = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-in");
        reveal.unobserve(entry.target);
      }
    }
  },
  { rootMargin: "0px 0px -12% 0px" },
);
document.querySelectorAll(".reveal").forEach((node) => reveal.observe(node));

// The pipe.
const pipeSection = $(".pipe");
const pipe = register($('[data-scene="pipe"]'), (canvas) => mountPipe(canvas, { reduced }));
const nav = $(".nav");
let beat = -1;
let tone = "";
function trackPipe() {
  const rect = pipeSection.getBoundingClientRect();
  const nextTone = rect.top < 48 && rect.bottom > 48 ? "dark" : "light";
  if (nextTone !== tone) {
    tone = nextTone;
    nav.dataset.tone = tone;
  }
  const progress = pinProgress(pipeSection);
  pipe?.progress(progress);
  const nextBeat = reduced ? 4 : Math.min(4, Math.floor(progress * 5));
  if (nextBeat !== beat) {
    beat = nextBeat;
    pipeSection.dataset.beat = String(beat);
  }
}

// The sonar bench.
const readout = $(".readout");
const readoutText = $(".readout__text");
const sonarCanvas = $('[data-scene="sonar"]');
register(sonarCanvas, (canvas) =>
  mountSonar(canvas, {
    reduced,
    onChange({ state, value }) {
      const text = state === "film" ? "Film under the probe" : "Clean wall";
      readout.dataset.state = state;
      readoutText.textContent = text;
      canvas.setAttribute("aria-valuenow", String(value));
      canvas.setAttribute("aria-valuetext", text);
    },
  }),
);

// The workflow.
const plan = $(".plan");
register($('[data-scene="overhead"]'), (canvas) =>
  mountOverhead(canvas, {
    reduced,
    onBeat(index) {
      plan.dataset.beat = String(index);
    },
  }),
);

// The enzyme, in the hero and in the card. One fetch, the only real data here.
// The three moves the designed enzyme makes, in the order the page tells them.
// `heat` is an illustration of warm water, never a temperature reading.
const STEPS = [
  { line: "Warm water shakes the chain. The designed region holds its shape.", heat: 0.7, state: { assemble: 1, site: 0, region: 1, dock: 0 } },
  { line: "The enzyme meets a strand of the glue and locks on.", heat: 0.7, state: { assemble: 1, site: 0, region: 1, dock: 1 } },
  { line: "The cutting site breaks the strand down.", heat: 0.7, state: { assemble: 1, site: 1, region: 1, dock: 1 } },
];
const LAST = STEPS.length - 1;
const card = $(".card");
const cardLine = $(".card__line");
const heat = $(".heat__range");
let cardScene = null;
let step = -1;
let auto = !reduced;
let since = 0;

function showStep(index) {
  step = index;
  since = 0;
  card.dataset.step = String(index);
  cardLine.textContent = STEPS[index].line;
  heat.value = String(Math.round(STEPS[index].heat * 100));
  cardScene?.set({ ...STEPS[index].state, heat: STEPS[index].heat });
}

async function startEnzyme() {
  const response = await fetch("data/enzyme.json");
  if (!response.ok) throw new Error("Enzyme trace could not be loaded");
  const data = await response.json();
  const hero = register($('[data-scene="hero"]'), (canvas) => mountProtein(canvas, data, { mode: "hero", reduced }));
  cardScene = register($('[data-scene="card"]'), (canvas) => mountProtein(canvas, data, { mode: "card", reduced }));
  observe();
  if (hero) {
    window.addEventListener("pointermove", (event) => {
      hero.point((event.clientX / window.innerWidth) * 2 - 1, (event.clientY / window.innerHeight) * 2 - 1);
    });
  }
  if (reduced) showStep(LAST);
  card.querySelectorAll(".step").forEach((button) => {
    button.addEventListener("click", () => {
      auto = false;
      showStep(Number(button.dataset.step));
    });
  });
  heat.addEventListener("input", () => {
    auto = false;
    cardScene?.set({ heat: Number(heat.value) / 100 });
  });
}

// Scenes draw only while on screen.
const watch = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) {
      const found = scenes.find((s) => s.canvas === entry.target);
      if (!found) continue;
      found.visible = entry.isIntersecting;
      if (entry.isIntersecting && !found.entered) {
        found.entered = true;
        found.scene.enter?.();
      }
    }
  },
  { rootMargin: "10% 0px" },
);
function observe() {
  scenes.forEach((entry) => watch.observe(entry.canvas));
}
observe();

let previous = performance.now();
function tick(now) {
  const dt = Math.min(0.05, (now - previous) / 1000);
  previous = now;
  scroll.update(dt);
  trackPipe();
  const time = now / 1000;
  for (const entry of scenes) {
    if (entry.visible) entry.scene.update(time, dt);
  }
  // The card plays through its steps once, while it is on screen.
  const cardEntry = scenes.find((entry) => entry.scene === cardScene);
  if (cardEntry?.visible && auto) {
    if (step < 0) showStep(0);
    since += dt;
    if (since > (step === 0 ? 4.2 : 3.8)) {
      if (step < LAST) showStep(step + 1);
      else auto = false;
    }
  }
  requestAnimationFrame(tick);
}
requestAnimationFrame(tick);

startEnzyme().catch((error) => {
  console.warn(error);
  $(".hero")?.classList.add("no-webgl");
});

mountLocalStructures(document).catch((error) => {
  const status = $("[data-local-structure-status]");
  const errorNode = $("[data-local-structure-error]");
  if (status) status.textContent = "Local structures could not be loaded.";
  if (errorNode) {
    errorNode.textContent = error instanceof Error ? error.message : String(error);
    errorNode.hidden = false;
  }
  console.warn("Local structure viewer could not start", error);
});

// The demo reads the saved run. It is loaded on its own, so that if its module
// or its run is unavailable the animations above still work, and the gallery
// says what is wrong instead of sitting empty.
function galleryMessage(text) {
  const gallery = $('[data-demo="gallery"]');
  if (!gallery) return;
  gallery.replaceChildren();
  const message = document.createElement("p");
  message.className = "variants__loading";
  message.textContent = text;
  gallery.append(message);
}

async function startDemo() {
  let demo;
  try {
    demo = await import("./lib/demo.mjs");
  } catch (error) {
    console.warn(error);
    galleryMessage("The demo code could not load. Restart the API server, then reload this page.");
    return;
  }
  try {
    await demo.mountDemo(document);
  } catch (error) {
    console.warn(error);
    galleryMessage("No saved run could be read. Start the API with --runs-dir pointing at a run.");
  }
}
startDemo();

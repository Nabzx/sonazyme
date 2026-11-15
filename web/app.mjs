// Sonazyme front page. Wires the scroll, the scenes and the small controls.
// Served under a strict CSP: nothing here writes an inline style. State goes
// to the page through classes and data attributes only.
import { mountConcepts } from "./lib/concepts.mjs";
import { mountFilm } from "./lib/film.mjs";
import { mountOverhead } from "./lib/overhead.mjs";
import { mountPipe } from "./lib/pipe.mjs";
import { mountProtein } from "./lib/protein.mjs";
import { createScroll, pinProgress } from "./lib/scroll.mjs";
import { mountSonar } from "./lib/sonar.mjs";

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
const pipeSection = $("#pipe");
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
  const nextBeat = Math.min(4, Math.floor(progress * 5));
  if (nextBeat !== beat) {
    beat = nextBeat;
    pipeSection.dataset.beat = String(beat);
  }
}

// The sonar bench.
const sonarCanvas = $('[data-scene="sonar"]');
register(sonarCanvas, (canvas) =>
  mountSonar(canvas, {
    reduced,
    onChange({ state, value }) {
      const text = state === "film" ? "Biofilm" : "Clean wall";
      canvas.setAttribute("aria-valuenow", String(value));
      canvas.setAttribute("aria-valuetext", text);
    },
  }),
);

// Literature-backed examples, displayed as stylised visual concepts.
async function startConcepts() {
  const response = await fetch("data/enzyme-examples.json");
  if (!response.ok) throw new Error("Enzyme examples could not be loaded");
  const catalogue = await response.json();
  register($('[data-scene="concepts"]'), (canvas) =>
    mountConcepts(canvas, { reduced, concepts: catalogue.examples }));
  observe();
}

// The workflow.
const plan = $(".plan");
const workflowSection = $("#workflow");
const overhead = register($('[data-scene="overhead"]'), (canvas) =>
  mountOverhead(canvas, {
    reduced,
    onBeat(index) {
      plan.dataset.beat = String(index);
    },
  }),
);

// The enzyme, in the hero and in the card. One fetch, the only real data here.
// The card is a six-beat film that loops; lib/film.mjs keeps the time and
// calls back as each beat begins. Every number in a line comes from the data.
const WORDS = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"];
const word = (count) => WORDS[count] ?? String(count);
function filmLines(data) {
  const designs = word(data.variants?.length ?? 0);
  const changed = data.engineered_region?.positions?.length ?? 0;
  const rejected = data.design?.rejected_count ?? 0;
  return [
    "Extracellular DNA holds the film onto the pipe. Cut that, and the film lets go.",
    `${data.name} is a bacterial enzyme that cuts exactly that bond.`,
    "Boltz-2 predicts its shape. The chain builds, and the cutting site parts the strand.",
    `HyperMPNN, on Tamarind Bio, rewrites the chain ${designs} ways.`,
    `MutRank scored every single change. ${rejected} touched the cutting site and were thrown out.`,
    `The design we keep: ${changed} positions changed, the cutting site untouched.`,
  ];
}
const card = $(".card");
const cardLine = $(".card__line");
const cardTags = card.querySelectorAll(".tag[data-beats]");
const stepButtons = card.querySelectorAll(".step[data-step]");
const filmToggle = $(".film-toggle");
let lines = [];
let cardScene = null;
let step = -1;
let heroScene = null;
let playing = !reduced;
let lineTimer = 0;
let cutTimer = 0;

function setPlaying(next) {
  playing = next && !reduced;
  if (playing) cardScene?.play();
  else cardScene?.pause();
  filmToggle.textContent = playing ? "Pause" : "Play";
  // A looping film should not keep interrupting a screen reader. The line is
  // announced only once the film is in the reader's hands.
  cardLine.setAttribute("aria-live", playing ? "off" : "polite");
}

// Called by the film as each beat begins, and after a jump.
function showStep(index) {
  if (index === step) return;
  step = index;
  card.dataset.step = String(index);
  stepButtons.forEach((button) => {
    if (Number(button.dataset.step) === index) button.setAttribute("aria-current", "step");
    else button.removeAttribute("aria-current");
  });
  cardTags.forEach((tag) => {
    tag.hidden = !tag.dataset.beats.split(" ").includes(String(index));
  });
  window.clearTimeout(lineTimer);
  if (reduced || !cardLine.textContent) {
    cardLine.textContent = lines[index];
    return;
  }
  cardLine.classList.add("is-changing");
  lineTimer = window.setTimeout(() => {
    cardLine.textContent = lines[index];
    cardLine.classList.remove("is-changing");
  }, 240);
}

// A jump dips the stage for a moment, so it reads as a dissolve, not a cut.
function jumpTo(index, { hold = false } = {}) {
  const land = () => {
    if (hold) cardScene?.hold(index);
    else cardScene?.jump(index);
    card.classList.remove("is-cutting");
  };
  window.clearTimeout(cutTimer);
  if (reduced) return land();
  card.classList.add("is-cutting");
  cutTimer = window.setTimeout(land, 240);
}

async function startEnzyme() {
  const response = await fetch("data/enzyme.json");
  if (!response.ok) throw new Error("Enzyme trace could not be loaded");
  const data = await response.json();
  lines = filmLines(data);
  const hero = register($('[data-scene="hero"]'), (canvas) => mountProtein(canvas, data, { mode: "hero", reduced }));
  heroScene = hero;
  cardScene = register($('[data-scene="card"]'), (canvas) => mountFilm(canvas, data, { reduced, onBeat: showStep }));
  observe();
  if (hero) {
    window.addEventListener("pointermove", (event) => {
      hero.point((event.clientX / window.innerWidth) * 2 - 1, (event.clientY / window.innerHeight) * 2 - 1);
    });
  }
  // With reduced motion there is no film: rest on the chosen design, and let
  // the steps show the last frame of each beat.
  filmToggle.hidden = reduced;
  setPlaying(!reduced);
  if (reduced) cardScene?.hold(lines.length - 1);
  else showStep(0);
  stepButtons.forEach((button) => {
    button.addEventListener("click", () => {
      jumpTo(Number(button.dataset.step));
      setPlaying(true);
    });
  });
  filmToggle.addEventListener("click", () => setPlaying(!playing));
}

// Scroll parallax: the hero drifts as it leaves, and the overhead leans as it
// crosses. Both are driven by scroll position, so neither moves on its own.
function trackParallax() {
  if (heroScene) {
    heroScene.scroll(window.scrollY / Math.max(1, window.innerHeight));
  }
  if (overhead && workflowSection) {
    const rect = workflowSection.getBoundingClientRect();
    const span = rect.height + window.innerHeight;
    overhead.scroll(span > 0 ? (window.innerHeight - rect.top) / span : 0.5);
  }
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
  trackParallax();
  const time = now / 1000;
  for (const entry of scenes) {
    if (entry.visible) entry.scene.update(time, dt);
  }
  requestAnimationFrame(tick);
}
requestAnimationFrame(tick);

startEnzyme().catch((error) => {
  console.warn(error);
  if (!heroScene) $(".hero")?.classList.add("no-webgl");
});
startConcepts().catch((error) => {
  console.warn(error);
  $(".gallery")?.classList.add("no-webgl");
});

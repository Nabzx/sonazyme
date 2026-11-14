// A small inertial scroll. The page still scrolls natively: this only eases
// wheel input towards a target with window.scrollTo, so the keyboard, the
// scrollbar, touch and anchor links all keep working.

const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

export function createScroll({ reduced = false } = {}) {
  let target = window.scrollY;
  let current = window.scrollY;
  let active = false;
  const limit = () => document.documentElement.scrollHeight - window.innerHeight;
  const stop = () => {
    active = false;
  };

  function onWheel(event) {
    if (event.ctrlKey || event.metaKey || event.defaultPrevented) return;
    if (Math.abs(event.deltaX) > Math.abs(event.deltaY)) return;
    event.preventDefault();
    let delta = event.deltaY;
    if (event.deltaMode === 1) delta *= 40;
    if (event.deltaMode === 2) delta *= window.innerHeight;
    if (!active) current = target = window.scrollY;
    target = clamp(target + delta, 0, limit());
    active = true;
  }

  if (!reduced) {
    window.addEventListener("wheel", onWheel, { passive: false });
    window.addEventListener("keydown", stop);
    window.addEventListener("pointerdown", stop);
    window.addEventListener("touchstart", stop, { passive: true });
  }

  return {
    update(dt) {
      if (!active) return;
      current += (target - current) * (1 - Math.exp(-dt * 7.5));
      if (Math.abs(target - current) < 0.5) {
        current = target;
        active = false;
      }
      window.scrollTo(0, current);
    },
    to(element) {
      const top = clamp(element.getBoundingClientRect().top + window.scrollY, 0, limit());
      if (reduced) {
        window.scrollTo(0, top);
        return;
      }
      current = window.scrollY;
      target = top;
      active = true;
    },
  };
}

// 0 when a pinned section first fills the screen, 1 when it is about to leave.
export function pinProgress(element) {
  const rect = element.getBoundingClientRect();
  const span = rect.height - window.innerHeight;
  return span <= 0 ? 0 : clamp(-rect.top / span, 0, 1);
}

// 0 as a section enters from below, 1 as it leaves at the top.
export function viewProgress(element) {
  const rect = element.getBoundingClientRect();
  return clamp((window.innerHeight - rect.top) / (window.innerHeight + rect.height), 0, 1);
}

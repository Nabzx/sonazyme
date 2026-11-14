// Coordinate inspection only. No geometry, confidence or stability is inferred.
export class TraceViewer {
  constructor(canvas) {
    this.canvas = canvas;
    this.points = [];
    this.angle = [0.22, -0.5];
    this.zoom = 1;
    this.active = new Set();
    this.changed = new Set();
    this.drag = null;
    canvas.addEventListener("pointerdown", event => { this.drag = [event.clientX, event.clientY]; canvas.setPointerCapture(event.pointerId); });
    canvas.addEventListener("pointerup", () => { this.drag = null; });
    canvas.addEventListener("pointercancel", () => { this.drag = null; });
    canvas.addEventListener("pointermove", event => {
      if (!this.drag) return;
      this.angle[1] += (event.clientX - this.drag[0]) * 0.008;
      this.angle[0] += (event.clientY - this.drag[1]) * 0.008;
      this.drag = [event.clientX, event.clientY]; this.draw();
    });
    canvas.addEventListener("wheel", event => { if (!this.points.length) return; event.preventDefault(); this.zoom = Math.max(0.5, Math.min(3, this.zoom * Math.exp(-event.deltaY * 0.001))); this.draw(); }, { passive: false });
    canvas.addEventListener("keydown", event => {
      const direction = { ArrowLeft:[0,-0.1], ArrowRight:[0,0.1], ArrowUp:[-0.1,0], ArrowDown:[0.1,0] }[event.key];
      if (direction) { event.preventDefault(); this.angle = this.angle.map((v,i) => v + direction[i]); this.draw(); }
      if (event.key === "+" || event.key === "=") this.scale(1.1);
      if (event.key === "-") this.scale(0.9);
    });
    new ResizeObserver(() => this.draw()).observe(canvas);
  }
  reset() { this.angle = [0.22, -0.5]; this.zoom = 1; this.draw(); }
  scale(factor) { this.zoom = Math.max(0.5, Math.min(3, this.zoom * factor)); this.draw(); }
  set(points, active = [], changed = []) { this.points = points; this.active = new Set(active); this.changed = new Set(changed); this.draw(); }
  draw() {
    const { canvas } = this;
    const bounds = canvas.getBoundingClientRect();
    const ratio = Math.min(devicePixelRatio || 1, 2);
    canvas.width = Math.round(bounds.width * ratio); canvas.height = Math.round(bounds.height * ratio);
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(ratio, ratio);
    const width = bounds.width, height = bounds.height;
    ctx.clearRect(0, 0, width, height);
    // Colours come from the design tokens, never from this file (#36).
    const style = getComputedStyle(this.canvas);
    const token = (name, fallback) => style.getPropertyValue(name).trim() || fallback;
    const grid = token("--border", "#e2e8f0");
    const activeColour = token("--teal-protein", "#0d9488");
    const changedColour = token("--cobalt-hydro", "#0284c7");
    const chainColour = token("--ink-faint", "#94a3b8");
    ctx.strokeStyle = grid; ctx.lineWidth = 1;
    for (let x = 24; x < width; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke(); }
    for (let y = 24; y < height; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke(); }
    if (!this.points.length) return;
    const center = [0,1,2].map(axis => this.points.reduce((sum,p) => sum + p.xyz[axis],0) / this.points.length);
    const radius = Math.max(...this.points.map(p => Math.hypot(...p.xyz.map((v,i) => v - center[i]))), 1);
    const scale = Math.min(width, height) * 0.34 / radius * this.zoom;
    const [pitch, yaw] = this.angle;
    const projected = this.points.map(point => {
      const [x,y,z] = point.xyz.map((v,i) => v - center[i]);
      const rx = x * Math.cos(yaw) + z * Math.sin(yaw), rz = -x * Math.sin(yaw) + z * Math.cos(yaw);
      return { position:point.position, x:width/2 + rx*scale, y:height/2 + (y*Math.cos(pitch)-rz*Math.sin(pitch))*scale, z:y*Math.sin(pitch)+rz*Math.cos(pitch) };
    });
    const segments = projected.slice(1).map((p,i) => ({ a:projected[i], b:p })).sort((a,b) => (a.a.z+a.b.z)-(b.a.z+b.b.z));
    for (const {a,b} of segments) {
      ctx.strokeStyle = this.active.has(b.position) ? activeColour : this.changed.has(b.position) ? changedColour : chainColour;
      ctx.globalAlpha = Math.max(0.3, Math.min(1, 0.65 + (a.z+b.z)/(4*radius)));
      ctx.lineWidth = this.active.has(b.position) || this.changed.has(b.position) ? 4 : 2.2;
      ctx.lineCap = "round"; ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y); ctx.stroke();
    }
    ctx.globalAlpha = 1;
    for (const point of projected.filter(p => this.active.has(p.position) || this.changed.has(p.position))) {
      ctx.fillStyle = this.active.has(point.position) ? activeColour : changedColour;
      ctx.beginPath(); ctx.arc(point.x,point.y,3.5,0,Math.PI*2); ctx.fill();
    }
  }
}

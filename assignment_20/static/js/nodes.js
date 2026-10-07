// Decorative node network for the home hero and the login background.
// Reads its colors from CSS variables and redraws on themechange and resize.
(function () {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const css = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  function nodeField(canvas, { count = 16 } = {}) {
    const ctx = canvas.getContext('2d');
    let w, h, nodes = [], mx = 0, my = 0, t = 0, raf = 0;
    function layout() {
      const r = canvas.getBoundingClientRect(), d = devicePixelRatio || 1;
      w = r.width; h = r.height;
      if (!w || !h) return;
      canvas.width = w * d; canvas.height = h * d;
      ctx.setTransform(d, 0, 0, d, 0, 0);
      nodes = Array.from({ length: count }, (_, i) => ({
        bx: ((i % 5) + 0.5 + (Math.random() - 0.5) * 0.6) / 5 * w,
        by: (Math.floor(i / 5) + 0.5 + (Math.random() - 0.5) * 0.6) / Math.ceil(count / 5) * h,
        r: 3 + Math.random() * 4, ph: Math.random() * 6.28, depth: 0.4 + Math.random() * 0.6,
      }));
    }
    function draw() {
      if (!w || !h) return;
      t += 0.01;
      ctx.clearRect(0, 0, w, h);
      const accent = css('--accent-ink'), fg = css('--fg');
      const pts = nodes.map(n => ({
        x: n.bx + Math.sin(t + n.ph) * 4 + mx * 10 * n.depth,
        y: n.by + Math.cos(t * 0.8 + n.ph) * 4 + my * 10 * n.depth,
        r: n.r * (1 + Math.sin(t * 1.5 + n.ph) * 0.08),
      }));
      ctx.lineWidth = 1; ctx.strokeStyle = fg; ctx.globalAlpha = 0.09;
      pts.forEach((a, i) => {
        let best = -1, bd = 1e9;
        pts.forEach((b, j) => {
          if (j !== i) {
            const d = (a.x - b.x) ** 2 + (a.y - b.y) ** 2;
            if (d < bd) { bd = d; best = j; }
          }
        });
        if (best > -1) { ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(pts[best].x, pts[best].y); ctx.stroke(); }
      });
      ctx.strokeStyle = accent; ctx.fillStyle = accent;
      pts.forEach(p => {
        ctx.globalAlpha = 0.3; ctx.beginPath(); ctx.arc(p.x, p.y, p.r * 2.4, 0, 6.28); ctx.stroke();
        ctx.globalAlpha = 0.5; ctx.beginPath(); ctx.arc(p.x, p.y, 1.6, 0, 6.28); ctx.fill();
      });
      ctx.globalAlpha = 1;
      if (!reduce) raf = requestAnimationFrame(draw);
    }
    canvas.parentElement.addEventListener('pointermove', e => {
      const r = canvas.getBoundingClientRect();
      mx = (e.clientX - r.left) / r.width - 0.5;
      my = (e.clientY - r.top) / r.height - 0.5;
    });
    new ResizeObserver(() => { layout(); draw(); }).observe(canvas);
    document.addEventListener('themechange', draw);
    document.addEventListener('visibilitychange', () => { cancelAnimationFrame(raf); if (!document.hidden && !reduce) draw(); });
    layout(); draw();
  }

  window.nodeField = nodeField;
})();

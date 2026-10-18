// Animation utilities, easing, and canvas helpers for StackCheck Launch Video

export function clamp(v, min = 0, max = 1) {
  return Math.min(max, Math.max(min, v));
}

export function easeOutCubic(x) {
  return 1 - Math.pow(1 - clamp(x), 3);
}

export function easeOutExpo(x) {
  return x === 1 ? 1 : 1 - Math.pow(2, -10 * clamp(x));
}

export function easeInOutCubic(x) {
  x = clamp(x);
  return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
}

export function easeOutBack(x, s = 1.70158) {
  x = clamp(x);
  return 1 + (s + 1) * Math.pow(x - 1, 3) + s * Math.pow(x - 1, 2);
}

export function roundRect(ctx, x, y, w, h, r = 12) {
  if (w < 2 * r) r = w / 2;
  if (h < 2 * r) r = h / 2;
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

export function drawGrid(ctx, W, H, spacing = 60, opacity = 0.08) {
  ctx.save();
  ctx.strokeStyle = `rgba(56, 189, 248, ${opacity})`;
  ctx.lineWidth = 1;
  for (let x = 0; x < W; x += spacing) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, H);
    ctx.stroke();
  }
  for (let y = 0; y < H; y += spacing) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(W, y);
    ctx.stroke();
  }
  ctx.restore();
}

export function drawVignette(ctx, W, H, color = '#0B0F19') {
  ctx.save();
  const grad = ctx.createRadialGradient(W / 2, H / 2, W * 0.25, W / 2, H / 2, W * 0.7);
  grad.addColorStop(0, 'rgba(11, 15, 25, 0)');
  grad.addColorStop(1, 'rgba(11, 15, 25, 0.85)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

export function drawCyanAura(ctx, cx, cy, radius = 300, alpha = 0.2) {
  ctx.save();
  const aura = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
  aura.addColorStop(0, `rgba(56, 189, 248, ${alpha})`);
  aura.addColorStop(0.5, `rgba(14, 165, 233, ${alpha * 0.4})`);
  aura.addColorStop(1, 'rgba(2, 132, 199, 0)');
  ctx.fillStyle = aura;
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

export function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => resolve(img);
    img.onerror = (e) => reject(new Error('Failed to load image: ' + src));
    img.src = src;
  });
}

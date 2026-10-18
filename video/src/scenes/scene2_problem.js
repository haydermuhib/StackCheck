import { clamp, easeOutCubic, easeInOutCubic, roundRect, drawGrid, drawVignette } from '../utils.js';

export function draw(ctx, t, { W, H, dur }) {
  // Base dark canvas
  ctx.fillStyle = '#0B0F19';
  ctx.fillRect(0, 0, W, H);
  drawGrid(ctx, W, H, 60, 0.05);

  // Collapse and shatter timing
  const collapseStart = 2.4;
  const shatterStart = 3.2;
  const isCollapsing = t > collapseStart;
  const collapseP = clamp((t - collapseStart) / (shatterStart - collapseStart));
  const shatterP = clamp((t - shatterStart) / (dur - shatterStart));

  ctx.save();
  if (shatterP > 0) {
    ctx.globalAlpha = 1 - easeOutCubic(shatterP);
  }

  // Header Typography
  const hP = easeOutCubic(clamp(t / 0.5));
  ctx.save();
  ctx.globalAlpha = hP;
  ctx.translate(0, (1 - hP) * 20);
  ctx.textAlign = 'center';
  ctx.font = '800 64px system-ui, -apple-system, sans-serif';
  ctx.fillStyle = '#F43F5E';
  ctx.shadowColor = 'rgba(244, 63, 94, 0.4)';
  ctx.shadowBlur = 20;
  ctx.fillText('STOP GUESSING', W / 2, H * 0.22);

  ctx.shadowBlur = 0;
  ctx.font = '600 36px system-ui, -apple-system, sans-serif';
  ctx.fillStyle = '#94A3B8';
  ctx.fillText('FROM HYPE CYCLES & OUTDATED SURVEYS', W / 2, H * 0.22 + 54);
  ctx.restore();

  // Floating noisy cards
  const cards = [
    { label: '⚠ HYPE CYCLES', x: W * 0.28, y: H * 0.45, w: 220, rot: -0.08, col: '#EF4444' },
    { label: '⚠ BIASED SURVEYS', x: W * 0.72, y: H * 0.46, w: 230, rot: 0.06, col: '#F59E0B' },
    { label: '⚠ UNVERIFIED SALARIES', x: W * 0.36, y: H * 0.65, w: 260, rot: 0.05, col: '#EF4444' },
    { label: '⚠ SOCIAL MEDIA NOISE', x: W * 0.65, y: H * 0.68, w: 270, rot: -0.06, col: '#F59E0B' },
    { label: '⚠ REDDIT ANECDOTES', x: W * 0.50, y: H * 0.54, w: 240, rot: 0.02, col: '#EF4444' }
  ];

  for (let i = 0; i < cards.length; i++) {
    const c = cards[i];
    const enter = easeOutCubic(clamp((t - (0.2 + i * 0.12)) / 0.4));
    if (enter <= 0) continue;

    ctx.save();
    let cx = c.x;
    let cy = c.y;
    let scale = enter;
    let rot = c.rot + Math.sin(t * 2 + i) * 0.02;

    if (isCollapsing) {
      // Inward gravitational pull towards center (W/2, H*0.55)
      const pull = easeInOutCubic(collapseP);
      cx = c.x + (W / 2 - c.x) * pull;
      cy = c.y + (H * 0.55 - c.y) * pull;
      rot += pull * (i % 2 === 0 ? 1 : -1) * 0.4;
      scale *= (1 - pull * 0.7);
    }

    ctx.translate(cx, cy);
    ctx.rotate(rot);
    ctx.scale(scale, scale);

    // Card background
    ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
    roundRect(ctx, -c.w / 2, -26, c.w, 52, 10);
    ctx.fill();

    // Red/Amber warning border
    ctx.strokeStyle = c.col;
    ctx.lineWidth = 1.5;
    ctx.shadowColor = c.col;
    ctx.shadowBlur = 12;
    ctx.stroke();

    ctx.shadowBlur = 0;
    ctx.fillStyle = '#F8FAFC';
    ctx.font = '700 18px monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(c.label, 0, 0);

    ctx.restore();
  }

  // Flash burst on shatter
  if (t > shatterStart && t < shatterStart + 0.3) {
    const flashP = 1 - (t - shatterStart) / 0.3;
    ctx.fillStyle = `rgba(56, 189, 248, ${flashP * 0.25})`;
    ctx.fillRect(0, 0, W, H);
  }

  ctx.restore();
  drawVignette(ctx, W, H);
}

import { clamp, easeOutCubic, easeOutExpo, roundRect, drawGrid, drawVignette, drawCyanAura } from '../utils.js';

export function draw(ctx, t, { W, H, dur }) {
  // Base dark canvas
  ctx.fillStyle = '#0B0F19';
  ctx.fillRect(0, 0, W, H);

  // Subtle animated grid drift
  ctx.save();
  ctx.translate(0, (t * 12) % 60);
  drawGrid(ctx, W, H, 60, 0.07);
  ctx.restore();

  // Central ambient cyan glow
  drawCyanAura(ctx, W / 2, H / 2, 450, 0.22);
  drawVignette(ctx, W, H);

  // Floating telemetry tags
  const tags = [
    { text: '• 4,820 Live Job Posts', x: W * 0.12, y: H * 0.22, delay: 0.4 },
    { text: '• Q4 Salary Benchmarks', x: W * 0.72, y: H * 0.28, delay: 0.9 },
    { text: '• HiringCafe Feed Active', x: W * 0.68, y: H * 0.78, delay: 1.4 }
  ];
  for (const tag of tags) {
    if (t > tag.delay) {
      const p = easeOutCubic((t - tag.delay) / 0.5);
      ctx.save();
      ctx.globalAlpha = p * 0.75;
      ctx.fillStyle = '#1E293B';
      roundRect(ctx, tag.x, tag.y - 18, 200, 32, 16);
      ctx.fill();
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.3)';
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.fillStyle = '#38BDF8';
      ctx.font = '600 13px monospace';
      ctx.fillText(tag.text, tag.x + 12, tag.y + 3);
      ctx.restore();
    }
  }

  // Camera exit push
  const exitP = t > dur - 0.3 ? (t - (dur - 0.3)) / 0.3 : 0;
  const zoom = 1 + exitP * 0.15;
  ctx.save();
  ctx.translate(W / 2, H / 2);
  ctx.scale(zoom, zoom);
  ctx.translate(-W / 2, -H / 2);
  if (exitP > 0) ctx.globalAlpha = 1 - exitP;

  // Staggered text build
  // Line 1: WHAT TECH SKILLS
  const t1 = clamp((t - 0.2) / 0.45);
  if (t1 > 0) {
    const p1 = easeOutCubic(t1);
    ctx.save();
    ctx.globalAlpha = p1;
    ctx.translate(0, (1 - p1) * 30);
    ctx.font = '800 68px system-ui, -apple-system, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillStyle = '#F8FAFC';
    ctx.fillText('WHAT TECH SKILLS', W / 2, H / 2 - 100);
    ctx.restore();
  }

  // Line 2: ARE ENGINEERING TEAMS
  const t2 = clamp((t - 0.75) / 0.45);
  if (t2 > 0) {
    const p2 = easeOutCubic(t2);
    ctx.save();
    ctx.globalAlpha = p2;
    ctx.translate(0, (1 - p2) * 30);
    ctx.font = '700 56px system-ui, -apple-system, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillStyle = '#94A3B8';
    ctx.fillText('ARE ENGINEERING TEAMS', W / 2, H / 2 - 20);
    ctx.restore();
  }

  // Line 3: ACTUALLY HIRING FOR?
  const t3 = clamp((t - 1.5) / 0.5);
  if (t3 > 0) {
    const p3 = easeOutExpo(t3);
    ctx.save();
    ctx.globalAlpha = p3;
    const boxScale = 0.9 + 0.1 * p3;
    ctx.translate(W / 2, H / 2 + 80);
    ctx.scale(boxScale, boxScale);

    // Pill background with cyan neon glow
    const bw = 780, bh = 88;
    ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
    roundRect(ctx, -bw / 2, -bh / 2, bw, bh, 20);
    ctx.fill();

    ctx.strokeStyle = '#38BDF8';
    ctx.lineWidth = 2.5;
    ctx.shadowColor = 'rgba(56, 189, 248, 0.6)';
    ctx.shadowBlur = 25;
    ctx.stroke();

    ctx.shadowBlur = 0;
    ctx.font = '800 66px system-ui, -apple-system, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    const grad = ctx.createLinearGradient(-bw / 2, 0, bw / 2, 0);
    grad.addColorStop(0, '#FFFFFF');
    grad.addColorStop(0.35, '#38BDF8');
    grad.addColorStop(1, '#0EA5E9');
    ctx.fillStyle = grad;
    ctx.fillText('ACTUALLY HIRING FOR?', 0, 0);
    ctx.restore();
  }

  ctx.restore();
}

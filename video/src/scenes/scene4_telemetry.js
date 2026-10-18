import { clamp, easeOutCubic, roundRect, drawGrid, drawVignette, drawCyanAura, loadImage } from '../utils.js';

let compImg = null;
let explorerImg = null;

export async function init() {
  try {
    compImg = await loadImage('/assets/screenshots/dashboard-compensation.png');
    explorerImg = await loadImage('/assets/screenshots/dashboard-explorer.png');
  } catch (e) {
    console.warn('Could not load telemetry images', e);
  }
}

export function draw(ctx, t, { W, H, dur }) {
  // Base dark canvas
  ctx.fillStyle = '#0B0F19';
  ctx.fillRect(0, 0, W, H);
  drawGrid(ctx, W, H, 60, 0.08);

  // Background dual cyan aura
  drawCyanAura(ctx, W * 0.25, H * 0.5, 420, 0.2);
  drawCyanAura(ctx, W * 0.75, H * 0.5, 420, 0.2);

  // Section Header
  const headP = easeOutCubic(clamp(t / 0.5));
  ctx.save();
  ctx.globalAlpha = headP;
  ctx.translate(0, (1 - headP) * 20);
  ctx.textAlign = 'center';
  ctx.font = '800 50px system-ui, -apple-system, sans-serif';
  ctx.fillStyle = '#F8FAFC';
  ctx.fillText('DEEP MARKET TELEMETRY & SALARY CURVES', W / 2, 90);
  ctx.font = '600 20px monospace';
  ctx.fillStyle = '#38BDF8';
  ctx.fillText('CROSS-CORRELATING FRAMEWORKS · SKILL PAIRINGS · REAL COMPENSATION', W / 2, 130);
  ctx.restore();

  const cardW = 780;
  const cardH = 460;

  // Left Card: Compensation Benchmarks
  const leftP = easeOutCubic(clamp((t - 0.2) / 0.7));
  if (leftP > 0 && compImg) {
    ctx.save();
    const floatL = Math.sin(t * 2) * 6;
    const targetX = W * 0.28;
    const targetY = H * 0.60 + floatL;
    const startX = -cardW;

    ctx.translate(startX + (targetX - startX) * leftP, targetY);
    ctx.scale(0.88 + 0.12 * leftP, 0.88 + 0.12 * leftP);
    ctx.transform(1, 0.03, -0.01, 1, 0, 0);

    // Drop shadow
    ctx.shadowColor = 'rgba(0, 0, 0, 0.8)';
    ctx.shadowBlur = 40;
    ctx.shadowOffsetY = 25;

    // Card background
    ctx.fillStyle = '#0F172A';
    roundRect(ctx, -cardW / 2, -cardH / 2, cardW, cardH, 16);
    ctx.fill();

    // Border
    ctx.strokeStyle = '#38BDF8';
    ctx.lineWidth = 2;
    ctx.shadowColor = 'rgba(56, 189, 248, 0.4)';
    ctx.shadowBlur = 20;
    ctx.stroke();

    // Image
    ctx.save();
    ctx.shadowBlur = 0;
    roundRect(ctx, -cardW / 2 + 5, -cardH / 2 + 5, cardW - 10, cardH - 10, 12);
    ctx.clip();
    ctx.drawImage(compImg, -cardW / 2 + 5, -cardH / 2 + 5, cardW - 10, cardH - 10);
    ctx.restore();

    // Badge: Salary Percentiles
    ctx.save();
    ctx.fillStyle = '#0369A1';
    roundRect(ctx, -cardW / 2 + 20, -cardH / 2 - 18, 260, 36, 18);
    ctx.fill();
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '700 14px monospace';
    ctx.fillText('📈 SALARY BENCHMARKING', -cardW / 2 + 36, -cardH / 2 + 5);
    ctx.restore();

    ctx.restore();
  }

  // Right Card: Skill Explorer & Co-occurrence
  const rightP = easeOutCubic(clamp((t - 1.6) / 0.7));
  if (rightP > 0 && explorerImg) {
    ctx.save();
    const floatR = Math.cos(t * 2) * 6;
    const targetX = W * 0.72;
    const targetY = H * 0.60 + floatR;
    const startX = W + cardW;

    ctx.translate(startX + (targetX - startX) * rightP, targetY);
    ctx.scale(0.88 + 0.12 * rightP, 0.88 + 0.12 * rightP);
    ctx.transform(1, -0.03, 0.01, 1, 0, 0);

    // Drop shadow
    ctx.shadowColor = 'rgba(0, 0, 0, 0.8)';
    ctx.shadowBlur = 40;
    ctx.shadowOffsetY = 25;

    // Card background
    ctx.fillStyle = '#0F172A';
    roundRect(ctx, -cardW / 2, -cardH / 2, cardW, cardH, 16);
    ctx.fill();

    // Border
    ctx.strokeStyle = '#0EA5E9';
    ctx.lineWidth = 2;
    ctx.shadowColor = 'rgba(14, 165, 233, 0.4)';
    ctx.shadowBlur = 20;
    ctx.stroke();

    // Image
    ctx.save();
    ctx.shadowBlur = 0;
    roundRect(ctx, -cardW / 2 + 5, -cardH / 2 + 5, cardW - 10, cardH - 10, 12);
    ctx.clip();
    ctx.drawImage(explorerImg, -cardW / 2 + 5, -cardH / 2 + 5, cardW - 10, cardH - 10);
    ctx.restore();

    // Badge: Skill Pairings
    ctx.save();
    ctx.fillStyle = '#0284C7';
    roundRect(ctx, -cardW / 2 + 20, -cardH / 2 - 18, 240, 36, 18);
    ctx.fill();
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '700 14px monospace';
    ctx.fillText('⚡ SKILL PAIRING GRAPH', -cardW / 2 + 36, -cardH / 2 + 5);
    ctx.restore();

    ctx.restore();
  }

  drawVignette(ctx, W, H);
}

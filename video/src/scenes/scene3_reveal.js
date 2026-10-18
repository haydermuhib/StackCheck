import { clamp, easeOutCubic, easeOutExpo, roundRect, drawGrid, drawVignette, drawCyanAura, loadImage } from '../utils.js';

let executiveImg = null;

export async function init() {
  try {
    executiveImg = await loadImage('/assets/screenshots/dashboard-executive.png');
  } catch (e) {
    console.warn('Could not load dashboard-executive.png', e);
  }
}

export function draw(ctx, t, { W, H, dur }) {
  // Base dark canvas
  ctx.fillStyle = '#0B0F19';
  ctx.fillRect(0, 0, W, H);
  drawGrid(ctx, W, H, 60, 0.08);

  // Background cyan light pools
  drawCyanAura(ctx, W * 0.28, H * 0.35, 400, 0.25);
  drawCyanAura(ctx, W * 0.75, H * 0.6, 500, 0.15);

  // Phase 1: Logo & Title build (t = 0 to 1.6)
  const logoP = easeOutExpo(clamp(t / 0.8));
  const subP = easeOutCubic(clamp((t - 0.7) / 0.6));

  ctx.save();
  ctx.translate(W * 0.08, H * 0.14);

  // Draw 3-strata monogram
  const strataW = 96;
  const strataH = 18;
  const strataGap = 8;

  // Stratum 1: Sky Cyan #38BDF8
  const s1P = easeOutCubic(clamp(t / 0.4));
  ctx.save();
  ctx.globalAlpha = s1P;
  ctx.translate((1 - s1P) * -40, 0);
  ctx.fillStyle = '#38BDF8';
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(strataW, 0);
  ctx.lineTo(strataW - strataH, strataH);
  ctx.lineTo(0, strataH);
  ctx.closePath();
  ctx.fill();
  ctx.restore();

  // Stratum 2: Cobalt Sky #0EA5E9
  const s2P = easeOutCubic(clamp((t - 0.15) / 0.4));
  ctx.save();
  ctx.globalAlpha = s2P;
  ctx.translate((1 - s2P) * -50, strataH + strataGap);
  ctx.fillStyle = '#0EA5E9';
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(strataW - strataH, 0);
  ctx.lineTo(strataW, strataH);
  ctx.lineTo(0, strataH);
  ctx.closePath();
  ctx.fill();
  ctx.restore();

  // Stratum 3: Deep Azure #0284C7
  const s3P = easeOutCubic(clamp((t - 0.3) / 0.4));
  ctx.save();
  ctx.globalAlpha = s3P;
  ctx.translate((1 - s3P) * -60, (strataH + strataGap) * 2);
  ctx.fillStyle = '#0284C7';
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(strataW, 0);
  ctx.lineTo(strataW - strataH, strataH);
  ctx.lineTo(0, strataH);
  ctx.closePath();
  ctx.fill();
  ctx.restore();

  // Wordmark: StackCheck
  ctx.save();
  ctx.globalAlpha = logoP;
  ctx.translate(strataW + 28, 52);
  ctx.font = '800 58px system-ui, -apple-system, sans-serif';
  ctx.fillStyle = '#F8FAFC';
  ctx.fillText('Stack', 0, 0);
  const stackWidth = ctx.measureText('Stack').width;
  ctx.fillStyle = '#38BDF8';
  ctx.shadowColor = 'rgba(56, 189, 248, 0.5)';
  ctx.shadowBlur = 20;
  ctx.fillText('Check', stackWidth + 2, 0);
  ctx.restore();

  // Subtitle
  if (subP > 0) {
    ctx.save();
    ctx.globalAlpha = subP;
    ctx.font = '600 20px monospace';
    ctx.fillStyle = '#94A3B8';
    ctx.fillText('OPEN-SOURCE MARKET INTELLIGENCE ENGINE', strataW + 28, 92);
    ctx.restore();
  }

  ctx.restore();

  // Phase 2: Executive Dashboard 3D Floating Card
  const cardStart = 1.0;
  const cardP = easeOutCubic(clamp((t - cardStart) / 0.9));

  if (cardP > 0 && executiveImg) {
    ctx.save();
    const floatY = Math.sin((t - cardStart) * 2) * 8;
    const targetX = W * 0.52;
    const targetY = H * 0.58 + floatY;
    const startY = H + 200;

    const currentY = startY + (targetY - startY) * cardP;
    const currentScale = 0.85 + 0.15 * cardP;

    ctx.translate(targetX, currentY);
    ctx.scale(currentScale, currentScale);

    // Subtle isometric skew/tilt
    ctx.transform(1, -0.04, 0.02, 1, 0, 0);

    const cardW = 1040;
    const cardH = 585;

    // Card drop shadow
    ctx.shadowColor = 'rgba(0, 0, 0, 0.8)';
    ctx.shadowBlur = 50;
    ctx.shadowOffsetY = 30;

    // Outer card glass container
    ctx.fillStyle = '#0F172A';
    roundRect(ctx, -cardW / 2, -cardH / 2, cardW, cardH, 16);
    ctx.fill();

    // Cyan glowing rim
    ctx.shadowColor = 'rgba(56, 189, 248, 0.4)';
    ctx.shadowBlur = 25;
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.6)';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Clip image to card rounded bounds
    ctx.save();
    ctx.shadowBlur = 0;
    roundRect(ctx, -cardW / 2 + 6, -cardH / 2 + 6, cardW - 12, cardH - 12, 12);
    ctx.clip();
    ctx.drawImage(executiveImg, -cardW / 2 + 6, -cardH / 2 + 6, cardW - 12, cardH - 12);
    ctx.restore();

    // Live Badge Pill on top of card
    const badgeP = easeOutCubic(clamp((t - 2.2) / 0.5));
    if (badgeP > 0) {
      ctx.save();
      ctx.globalAlpha = badgeP;
      ctx.translate(-cardW / 2 + 40, -cardH / 2 - 20);
      ctx.fillStyle = '#0284C7';
      roundRect(ctx, 0, 0, 240, 36, 18);
      ctx.fill();
      ctx.fillStyle = '#FFFFFF';
      ctx.font = '700 14px monospace';
      ctx.fillText('● 1,420 LIVE JOB POSTS', 16, 23);
      ctx.restore();
    }

    ctx.restore();
  }

  drawVignette(ctx, W, H);
}

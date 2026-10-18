import { clamp, easeOutCubic, easeOutExpo, roundRect, drawGrid, drawVignette, drawCyanAura } from '../utils.js';

export function draw(ctx, t, { W, H, dur }) {
  // Base dark canvas
  ctx.fillStyle = '#0B0F19';
  ctx.fillRect(0, 0, W, H);
  drawGrid(ctx, W, H, 60, 0.08);

  // Soft cyan central aura
  drawCyanAura(ctx, W / 2, H * 0.42, 500, 0.3);

  // Fade to black at the very end
  const fadeP = t > dur - 0.4 ? (t - (dur - 0.4)) / 0.4 : 0;
  ctx.save();
  if (fadeP > 0) ctx.globalAlpha = 1 - fadeP;

  // Scale entrance
  const enterP = easeOutExpo(clamp(t / 0.6));
  const scale = 0.92 + 0.08 * enterP;

  ctx.save();
  ctx.translate(W / 2, H * 0.42);
  ctx.scale(scale, scale);

  // 3-Strata Monogram (Large)
  const mw = 120;
  const mh = 22;
  const mgap = 10;
  const logoTotalH = mh * 3 + mgap * 2;

  ctx.save();
  ctx.translate(-260, -logoTotalH / 2);

  // Stratum 1: Sky Cyan #38BDF8
  ctx.fillStyle = '#38BDF8';
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(mw, 0);
  ctx.lineTo(mw - mh, mh);
  ctx.lineTo(0, mh);
  ctx.closePath();
  ctx.fill();

  // Stratum 2: Cobalt Sky #0EA5E9
  ctx.translate(0, mh + mgap);
  ctx.fillStyle = '#0EA5E9';
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(mw - mh, 0);
  ctx.lineTo(mw, mh);
  ctx.lineTo(0, mh);
  ctx.closePath();
  ctx.fill();

  // Stratum 3: Deep Azure #0284C7
  ctx.translate(0, mh + mgap);
  ctx.fillStyle = '#0284C7';
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(mw, 0);
  ctx.lineTo(mw - mh, mh);
  ctx.lineTo(0, mh);
  ctx.closePath();
  ctx.fill();
  ctx.restore();

  // Large Wordmark: StackCheck
  ctx.save();
  ctx.translate(-100, 16);
  ctx.font = '800 84px system-ui, -apple-system, sans-serif';
  ctx.fillStyle = '#F8FAFC';
  ctx.fillText('Stack', 0, 0);
  const sw = ctx.measureText('Stack').width;
  ctx.fillStyle = '#38BDF8';
  ctx.shadowColor = 'rgba(56, 189, 248, 0.6)';
  ctx.shadowBlur = 30;
  ctx.fillText('Check', sw + 6, 0);
  ctx.restore();

  ctx.restore();

  // Tagline
  const tagP = easeOutCubic(clamp((t - 0.4) / 0.5));
  if (tagP > 0) {
    ctx.save();
    ctx.globalAlpha = tagP;
    ctx.textAlign = 'center';
    ctx.font = '600 24px monospace';
    ctx.fillStyle = '#94A3B8';
    ctx.fillText('TECH STACK MARKET INTELLIGENCE & DATA ANALYTICS', W / 2, H * 0.58);
    ctx.restore();
  }

  // Feature Badges
  const badgeP = easeOutCubic(clamp((t - 0.8) / 0.5));
  if (badgeP > 0) {
    ctx.save();
    ctx.globalAlpha = badgeP;
    const badges = ['Python 3.10+', 'Open Source MIT', 'Portable Binary'];
    const totalW = 680;
    const startX = (W - totalW) / 2;
    for (let i = 0; i < badges.length; i++) {
      const bx = startX + i * 230;
      ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
      roundRect(ctx, bx, H * 0.65, 210, 40, 20);
      ctx.fill();
      ctx.strokeStyle = '#1E293B';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      ctx.font = '600 15px monospace';
      ctx.fillStyle = '#38BDF8';
      ctx.textAlign = 'center';
      ctx.fillText(badges[i], bx + 105, H * 0.65 + 25);
    }
    ctx.restore();
  }

  // CTA Pill Button
  const ctaP = easeOutExpo(clamp((t - 1.2) / 0.5));
  if (ctaP > 0) {
    ctx.save();
    ctx.globalAlpha = ctaP;
    const btnW = 540;
    const btnH = 64;
    const btnX = (W - btnW) / 2;
    const btnY = H * 0.77;

    ctx.fillStyle = 'rgba(15, 23, 42, 0.95)';
    roundRect(ctx, btnX, btnY, btnW, btnH, 32);
    ctx.fill();

    ctx.strokeStyle = '#38BDF8';
    ctx.lineWidth = 2;
    ctx.shadowColor = 'rgba(56, 189, 248, 0.6)';
    ctx.shadowBlur = 25;
    ctx.stroke();

    ctx.shadowBlur = 0;
    ctx.font = '700 22px monospace';
    ctx.fillStyle = '#F8FAFC';
    ctx.textAlign = 'center';
    ctx.fillText('⚡ github.com/haydermuhib/StackCheck', W / 2, btnY + 40);
    ctx.restore();
  }

  ctx.restore();
  drawVignette(ctx, W, H);
}

import { clamp, easeOutCubic, easeOutExpo, roundRect, drawGrid, drawVignette, drawCyanAura } from '../utils.js';

export function draw(ctx, t, { W, H, dur }) {
  // Base dark canvas
  ctx.fillStyle = '#0B0F19';
  ctx.fillRect(0, 0, W, H);
  drawGrid(ctx, W, H, 60, 0.08);

  // Background cyan glow
  drawCyanAura(ctx, W / 2, H * 0.58, 480, 0.22);

  // Section Header
  const headP = easeOutCubic(clamp(t / 0.5));
  ctx.save();
  ctx.globalAlpha = headP;
  ctx.translate(0, (1 - headP) * 20);
  ctx.textAlign = 'center';
  ctx.font = '800 52px system-ui, -apple-system, sans-serif';
  ctx.fillStyle = '#F8FAFC';
  ctx.fillText('ZERO CLOUD DEPENDENCIES', W / 2, 100);

  ctx.font = '600 22px monospace';
  ctx.fillStyle = '#38BDF8';
  ctx.fillText('100% LOCAL & PRIVATE · RUNS DIRECTLY ON YOUR MACHINE', W / 2, 142);
  ctx.restore();

  // Glass Terminal HUD Window
  const termP = easeOutExpo(clamp((t - 0.25) / 0.6));
  if (termP > 0) {
    ctx.save();
    const termW = 960;
    const termH = 480;
    const termX = (W - termW) / 2;
    const targetY = H * 0.26;
    const startY = H * 0.45;
    const termY = startY + (targetY - startY) * termP;

    ctx.translate(0, termY - targetY);
    ctx.globalAlpha = termP;

    // Terminal Container with Drop Shadow
    ctx.save();
    ctx.shadowColor = 'rgba(0, 0, 0, 0.85)';
    ctx.shadowBlur = 50;
    ctx.shadowOffsetY = 30;
    ctx.fillStyle = 'rgba(15, 23, 42, 0.95)';
    roundRect(ctx, termX, targetY, termW, termH, 16);
    ctx.fill();

    // Border glow
    ctx.strokeStyle = '#38BDF8';
    ctx.lineWidth = 1.5;
    ctx.shadowColor = 'rgba(56, 189, 248, 0.4)';
    ctx.shadowBlur = 20;
    ctx.shadowOffsetY = 0;
    ctx.stroke();
    ctx.restore(); // Restores shadow blur/offset to 0

    // Terminal Header Bar
    ctx.save();
    ctx.fillStyle = 'rgba(30, 41, 59, 0.8)';
    roundRect(ctx, termX, targetY, termW, 46, 16);
    ctx.fill();
    ctx.fillRect(termX, targetY + 30, termW, 16);

    // Window Dots
    const dots = [
      { col: '#EF4444', x: termX + 24 },
      { col: '#F59E0B', x: termX + 44 },
      { col: '#10B981', x: termX + 64 }
    ];
    for (const d of dots) {
      ctx.beginPath();
      ctx.arc(d.x, targetY + 23, 6, 0, Math.PI * 2);
      ctx.fillStyle = d.col;
      ctx.fill();
    }

    // Terminal Title
    ctx.font = '600 13px monospace';
    ctx.fillStyle = '#94A3B8';
    ctx.textAlign = 'center';
    ctx.fillText('bash — stackcheck', termX + termW / 2, targetY + 28);
    ctx.restore();

    // Terminal Body Text (ensure 0 shadow)
    ctx.save();
    ctx.shadowBlur = 0;
    ctx.shadowColor = 'transparent';
    ctx.shadowOffsetY = 0;
    ctx.textAlign = 'left';
    ctx.font = '600 20px monospace';

    // Command Typing: $ stackcheck
    const cmdStr = '$ stackcheck';
    const typeP = clamp((t - 0.7) / 0.8);
    const charCount = Math.floor(typeP * cmdStr.length);
    const typedText = cmdStr.slice(0, charCount);

    ctx.fillStyle = '#38BDF8';
    ctx.fillText(typedText, termX + 36, targetY + 95);

    // Blinking cursor
    if (t < 2.0 && Math.floor(t * 4) % 2 === 0) {
      const cursorX = termX + 36 + ctx.measureText(typedText).width + 4;
      ctx.fillRect(cursorX, targetY + 77, 10, 22);
    }

    // Checkmark 1: SQLite
    if (t > 1.7) {
      const p = easeOutCubic(clamp((t - 1.7) / 0.3));
      ctx.save();
      ctx.globalAlpha = p;
      ctx.fillStyle = '#34D399';
      ctx.fillText('[✓] Local SQLite Engine Loaded', termX + 36, targetY + 155);
      ctx.fillStyle = '#64748B';
      ctx.font = '500 16px monospace';
      ctx.fillText('    Zero cloud telemetry · 100% private in-memory cache', termX + 36, targetY + 185);
      ctx.restore();
    }

    // Checkmark 2: Live Ingestion
    if (t > 2.5) {
      const p = easeOutCubic(clamp((t - 2.5) / 0.3));
      ctx.save();
      ctx.globalAlpha = p;
      ctx.fillStyle = '#34D399';
      ctx.font = '600 20px monospace';
      ctx.fillText('[✓] Ingested 1,420 Live Job Postings from HiringCafe', termX + 36, targetY + 235);
      ctx.fillStyle = '#64748B';
      ctx.font = '500 16px monospace';
      ctx.fillText('    Extracted technical requirements & compensation percentiles', termX + 36, targetY + 265);
      ctx.restore();
    }

    // Checkmark 3: UI Ready
    if (t > 3.3) {
      const p = easeOutCubic(clamp((t - 3.3) / 0.3));
      ctx.save();
      ctx.globalAlpha = p;
      ctx.fillStyle = '#38BDF8';
      ctx.font = '700 21px monospace';
      ctx.fillText('🚀 Local Dashboard Running: http://localhost:8501', termX + 36, targetY + 330);
      ctx.restore();
    }

    ctx.restore();
    ctx.restore();
  }

  drawVignette(ctx, W, H);
}

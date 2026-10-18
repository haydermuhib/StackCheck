// Design dimensions and absolute scene timing locked to VO audio (plan/beats.json)
export const W = 1920, H = 1080, FPS = 30;

export const scenes = [
  { id: 'scene1_hook', start: 0.0, end: 4.10 },
  { id: 'scene2_problem', start: 4.10, end: 8.10 },
  { id: 'scene3_reveal', start: 8.10, end: 15.20 },
  { id: 'scene4_telemetry', start: 15.20, end: 22.50 },
  { id: 'scene5_privacy', start: 22.50, end: 27.80 },
  { id: 'scene6_outro', start: 27.80, end: 31.00 }
];

export const DURATION = scenes.at(-1).end;

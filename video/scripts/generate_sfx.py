#!/usr/bin/env python3
"""
Generate precision UI sound effects and tech bed for StackCheck launch video.
Zero third-party dependencies — uses standard library `wave`, `math`, `struct`.
"""
import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 48000

def write_wav(path: Path, samples: list[float], sample_rate: int = SAMPLE_RATE):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        packed = bytearray()
        for s in samples:
            val = max(-1.0, min(1.0, s))
            int_val = int(val * 32767.0)
            packed.extend(struct.pack('<h', int_val))
        wav_file.writeframes(packed)
    print(f"Generated: {path} ({len(samples)} samples, {len(samples)/sample_rate:.3f}s)")

def make_tick(duration=0.06, freq=1800.0, peak_db=-10.0):
    n_samples = int(duration * SAMPLE_RATE)
    amp = 10.0 ** (peak_db / 20.0)
    samples = []
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 85.0)
        s = math.sin(2.0 * math.pi * freq * t) * env * amp
        samples.append(s)
    return samples

def make_pop(duration=0.10, start_freq=650.0, end_freq=220.0, peak_db=-8.0):
    n_samples = int(duration * SAMPLE_RATE)
    amp = 10.0 ** (peak_db / 20.0)
    samples = []
    phase = 0.0
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        cur_freq = start_freq + (end_freq - start_freq) * (t / duration)
        phase += 2.0 * math.pi * cur_freq / SAMPLE_RATE
        env = math.sin(math.pi * min(1.0, t / (duration * 0.2))) * math.exp(-t * 28.0)
        s = math.sin(phase) * env * amp
        samples.append(s)
    return samples

def make_swish(duration=0.25, peak_db=-14.0):
    n_samples = int(duration * SAMPLE_RATE)
    amp = 10.0 ** (peak_db / 20.0)
    samples = []
    import random
    rng = random.Random(42)
    last = 0.0
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        env = math.sin(math.pi * (t / duration)) ** 2
        noise = (rng.random() * 2.0 - 1.0)
        last = last * 0.85 + noise * 0.15 # Low-pass smooth
        samples.append(last * env * amp)
    return samples

def make_sub_impact(duration=0.6, base_freq=58.0, peak_db=-9.0):
    n_samples = int(duration * SAMPLE_RATE)
    amp = 10.0 ** (peak_db / 20.0)
    samples = []
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        f = base_freq * (1.0 - 0.25 * (t / duration))
        env = math.exp(-t * 6.5)
        s1 = math.sin(2.0 * math.pi * f * t)
        s2 = 0.3 * math.sin(2.0 * math.pi * f * 2.0 * t)
        samples.append((s1 + s2) * env * amp)
    return samples

def make_chime(duration=0.7, freqs=[523.25, 659.25, 783.99, 1046.50], peak_db=-12.0):
    n_samples = int(duration * SAMPLE_RATE)
    amp = 10.0 ** (peak_db / 20.0) / len(freqs)
    samples = []
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 4.2)
        s = sum(math.sin(2.0 * math.pi * f * t) for f in freqs) * env * amp
        samples.append(s)
    return samples

def make_success_beep(duration=0.12, freq=880.0, peak_db=-12.0):
    n_samples = int(duration * SAMPLE_RATE)
    amp = 10.0 ** (peak_db / 20.0)
    samples = []
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        env = math.sin(math.pi * min(1.0, t / 0.015)) * math.exp(-t * 22.0)
        s = math.sin(2.0 * math.pi * freq * t) * env * amp
        samples.append(s)
    return samples

def main():
    out_dir = Path("video/assets/sfx")
    write_wav(out_dir / "tick.wav", make_tick())
    write_wav(out_dir / "pop.wav", make_pop())
    write_wav(out_dir / "swish.wav", make_swish())
    write_wav(out_dir / "sub_impact.wav", make_sub_impact())
    write_wav(out_dir / "chime.wav", make_chime())
    write_wav(out_dir / "beep.wav", make_success_beep())

if __name__ == '__main__':
    main()

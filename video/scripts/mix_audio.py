#!/usr/bin/env python3
"""
Audio mixing script for StackCheck launch video.
Positions VO and SFX cues at the exact timestamps defined in plan/beats.json,
applies proper gain staging, and outputs video/assets/audio_mix.wav.
"""
import json
import math
import subprocess
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    beats_file = root / "plan" / "beats.json"
    with open(beats_file, "r") as f:
        beats = json.load(f)

    vo_mp3 = root / "assets" / "vo" / "vo_v1.mp3"
    vo_wav = root / "cache" / "vo.wav"
    vo_wav.parent.mkdir(parents=True, exist_ok=True)

    # 1. Convert VO MP3 to 48kHz PCM16 WAV
    subprocess.run([
        "ffmpeg", "-y", "-i", str(vo_mp3),
        "-ar", "48000", "-ac", "1",
        str(vo_wav)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    sfx_dir = root / "assets" / "sfx"
    sfx_map = {
        "mechanical_tick": sfx_dir / "tick.wav",
        "accent_blip": sfx_dir / "pop.wav",
        "friction_whoosh": sfx_dir / "swish.wav",
        "shatter_glitch": sfx_dir / "pop.wav",
        "sub_impact": sfx_dir / "sub_impact.wav",
        "glass_glide": sfx_dir / "swish.wav",
        "data_chirp": sfx_dir / "beep.wav",
        "network_arpeggio": sfx_dir / "pop.wav",
        "terminal_slam": sfx_dir / "sub_impact.wav",
        "success_beep_1": sfx_dir / "beep.wav",
        "success_beep_2": sfx_dir / "beep.wav",
        "success_beep_3": sfx_dir / "beep.wav",
        "harmonic_chime": sfx_dir / "chime.wav",
    }

    # Build FFmpeg complex filter to delay and mix all cues
    inputs = ["-i", str(vo_wav)]
    filter_parts = []
    
    # VO input is 0:a
    filter_parts.append("[0:a]volume=1.0[vo]")
    mix_labels = ["[vo]"]

    cues = beats.get("sfx_cues", [])
    for idx, cue in enumerate(cues, start=1):
        sfx_path = sfx_map.get(cue["type"])
        if not sfx_path or not sfx_path.exists():
            continue
        delay_ms = int(cue["t"] * 1000)
        inputs.extend(["-i", str(sfx_path)])
        # Each SFX input gets delayed by its timestamp
        gain = 0.7 if "sub" in cue["type"] else 0.45
        filter_parts.append(f"[{idx}:a]adelay={delay_ms}|{delay_ms},volume={gain}[sfx_{idx}]")
        mix_labels.append(f"[sfx_{idx}]")

    num_inputs = len(mix_labels)
    filter_complex = ";".join(filter_parts) + f";{''.join(mix_labels)}amix=inputs={num_inputs}:dropout_transition=0:normalize=0[mixed];[mixed]alimiter=limit=-1.5dB:level=false[out]"

    out_mix = root / "assets" / "audio_mix.wav"
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-ar", "48000",
        "-t", "31.007",
        str(out_mix)
    ]
    subprocess.run(cmd, check=True)
    print(f"Master audio mix generated: {out_mix}")

if __name__ == "__main__":
    main()

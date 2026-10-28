"""
Render the complete, exact 180.00-second (03:00, 5,400 frames @ 30fps, 1920x1080)
SafeUndo Anime Cinematic Product Demo MP4 (H.264 + AAC).
"""
from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_MP4 = ROOT / "ussd-sim" / "SafeUndo_Anime_Demo_3min.mp4"
DOWNLOADS_MP4 = Path("C:/Users/SMuthii/Downloads/SafeUndo_Anime_Demo_3min.mp4")

W, H = 1920, 1080
FPS = 30
TOTAL_S = 180
TOTAL_FRAMES = TOTAL_S * FPS  # 5,400 frames = 180.000s
SR = 44100
TOTAL_SAMPLES = TOTAL_S * SR  # 7,938,000 samples = 180.000s

SCENES = [
    (1, 0.0,   15.0,  "00:00-00:15", "SCENE 1 · THE CINEMATIC HOOK",              "EXTREME CLOSE-UP · NAIROBI DUSK"),
    (2, 15.0,  40.0,  "00:15-00:40", "SCENE 2 · THE MISTAKE",                     "MATCH CUT · SHOCK REACTION"),
    (3, 40.0,  65.0,  "00:40-01:05", "SCENE 3 · PANIC & THE REVERSAL PROBLEM",    "FAST CUTS · RISING TENSION"),
    (4, 65.0,  80.0,  "01:05-01:20", "SCENE 4 · THE SAFEUNDO REVEAL",             "CAMERA PUSH · THINK BEFORE IT SENDS"),
    (5, 80.0,  115.0, "01:20-01:55", "SCENE 5 · LIVE DEMO: PROACTIVE PROTECTION", "OVER-THE-SHOULDER · ANOMALY WARNING"),
    (6, 115.0, 145.0, "01:55-02:25", "SCENE 6 · WHEN A MISTAKE STILL HAPPENS",    "CLOSE-UP · REVERSAL TRACKER"),
    (7, 145.0, 165.0, "02:25-02:45", "SCENE 7 · THE PAYOFF",                      "THUMB CALLBACK · COMPOSED"),
    (8, 165.0, 180.0, "02:45-03:00", "SCENE 8 · FINAL IMPACT",                    "HERO SHOT · 03:00 LOCK"),
]

# (start_s, end_s, speaker, display_subtitle, tts_phonetic_text, rate, pitch_shift)
SCRIPT_CUES = [
    # Scene 1: 00:00 - 00:15
    (1.2,  7.8,  "NARRATOR",
     "What happens when one wrong tap sends your money to the wrong person?",
     "What happens, when one wrong tap, sends your money to the wrong person?", -1, 0),
    (8.5,  14.2, "SAFEUNDO",
     "SAFEUNDO — One mistake. A smarter way forward.",
     "Safe Undo. One mistake. A smarter way forward.", -1, 0),

    # Scene 2: 00:15 - 00:40
    (15.5, 23.2, "NARRATOR",
     "Naruto intends to send KSh 2,000 to Mama Wanjiru, but selects an unfamiliar number in haste.",
     "Naruto intends to send two thousand Kenyan shillings to Mama Wanjiru, but selects an unfamiliar number in haste.", 0, 0),
    (24.2, 29.5, "NARUTO",
     "\"Wait... I sent it to the wrong person!\"",
     "Wait! I sent it to the wrong person!", 1, 1),
    (30.0, 39.5, "SILENCE · MATCH CUT",
     "RK94X2M10P Confirmed. KSh 2,000 sent to NANCY KAMAU. His eyes widen as the mistake sinks in.",
     "", 0, 0),

    # Scene 3: 00:40 - 01:05
    (40.5, 51.0, "NARRATOR",
     "The money is gone. The mistake is real. And now, figuring out what to do next becomes another problem.",
     "The money is gone. The mistake is real. And now, figuring out what to do next, becomes another problem.", 0, 0),
    (51.8, 61.5, "NARUTO",
     "\"Do I forward the SMS to 456? What about a Till or PayBill? How long will it stay under review?\"",
     "Do I forward the S M S to four five six? What about a Till or Pay Bill? How long will it stay under review?", 1, 1),
    (62.0, 65.0, "DRAMATIC SILENCE",
     "[Sound cuts to silence as Naruto stares at the phone screen]",
     "", 0, 0),

    # Scene 4: 01:05 - 01:20
    (65.6, 74.2, "NARRATOR",
     "What if your transaction could be checked before the mistake happens — and guided if something still goes wrong?",
     "What if your transaction could be checked before the mistake happens, and guided if something still goes wrong?", 0, 0),
    (74.8, 79.5, "SAFEUNDO",
     "SAFEUNDO — THINK BEFORE IT SENDS.",
     "Safe Undo. Think before it sends.", -1, 0),

    # Scene 5: 01:20 - 01:55
    (80.6,  93.2, "NARRATOR",
     "SafeUndo learns a customer's normal transaction patterns and helps flag activity that may be unusual — before the payment is completed.",
     "Safe Undo learns a customer's normal transaction patterns, and helps flag activity that may be unusual, before the payment is completed.", 0, 0),
    (94.0,  103.0, "NARUTO",
     "\"That number... I don't usually send money there.\"",
     "That number... I don't usually send money there!", 0, 1),
    (103.8, 114.2, "NARRATOR",
     "Seeing Nancy Kamau via Hakikisha and the high-amount prompt, he cancels safely before a single shilling leaves.",
     "Seeing Nancy Kamau via Ha-kee-kee-sha and the high amount prompt, he cancels safely before a single shilling leaves.", 0, 0),

    # Scene 6: 01:55 - 02:25
    (115.6, 130.5, "NARRATOR",
     "And if a transaction still goes through by mistake, SafeUndo helps the customer navigate the reversal process and follow the request.",
     "And if a transaction still goes through by mistake, Safe Undo helps the customer navigate the reversal process, and follow the request.", 0, 0),
    (131.2, 144.2, "NARUTO",
     "\"Case SU-1042 is tracked on both *334# and My OneApp, with clear 456 steps and an estimated 5 to 9 hours remaining.\"",
     "Case S U ten forty two is tracked on both U S S D and My One App, with clear four five six steps, and an estimated five to nine hours remaining.", 0, 1),

    # Scene 7: 02:25 - 02:45
    (145.6, 155.8, "NARRATOR",
     "Because protecting your money is not only about detecting a mistake. It's about helping you make a better decision — and know what to do next.",
     "Because protecting your money is not only about detecting a mistake. It is about helping you make a better decision, and know what to do next.", 0, 0),
    (156.5, 164.4, "NARRATOR",
     "Same thumb, same phone — this time Naruto pauses, verifies the recipient and amount, and stays in control.",
     "Same thumb, same phone. This time, Naruto pauses, verifies the recipient and amount, and stays in control.", 0, 0),

    # Scene 8: 02:45 - 03:00
    (165.6, 173.5, "NARRATOR",
     "SafeUndo. Catch the unusual. Guide the reversal. Protect the decision.",
     "Safe Undo. Catch the unusual. Guide the reversal. Protect the decision.", -1, 0),
    (174.0, 180.0, "SAFEUNDO · 03:00",
     "SAFEUNDO — Catch the unusual. Guide the reversal. Protect the decision.",
     "", 0, 0),
]


def _load_wav_mono(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as wf:
        ch = wf.getnchannels()
        sr = wf.getframerate()
        raw = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        raw = raw.reshape(-1, ch).mean(axis=1)
    if sr != SR and len(raw) > 10:
        new_len = int(len(raw) * SR / sr)
        raw = np.interp(np.linspace(0, len(raw) - 1, new_len), np.arange(len(raw)), raw).astype(np.float32)
    return raw


def build_master_audio(tmp_dir: Path) -> tuple[Path, np.ndarray]:
    """Synthesize all voice cues via Windows SAPI + procedural anime score & SFX into an exact 180.000s WAV."""
    ps_lines = ["Add-Type -AssemblyName System.Speech"]
    ps_lines.append("$s = New-Object System.Speech.Synthesis.SpeechSynthesizer")
    ps_lines.append("try { $s.SelectVoice('Microsoft Hazel Desktop') } catch {}")

    wav_map: dict[int, Path] = {}
    for idx, (st, en, spk, sub, tts, rate, _) in enumerate(SCRIPT_CUES):
        if not tts:
            continue
        wpath = tmp_dir / f"cue_{idx:02d}.wav"
        wav_map[idx] = wpath
        safe_txt = tts.replace("'", "''")
        ps_lines.append(f"$s.Rate = {rate}")
        ps_lines.append(f"$s.SetOutputToWaveFile('{wpath.as_posix()}')")
        ps_lines.append(f"$s.Speak('{safe_txt}')")
    ps_lines.append("$s.Dispose()")

    ps_script = tmp_dir / "tts.ps1"
    ps_script.write_text("\n".join(ps_lines), encoding="utf-8")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_script)], check=True)

    voice_track = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    voice_env = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

    for idx, wpath in wav_map.items():
        if not wpath.exists():
            continue
        st, en, spk, sub, tts, rate, pitch_shift = SCRIPT_CUES[idx]
        samples = _load_wav_mono(wpath)
        if pitch_shift > 0 and len(samples) > 100:
            # Slight energetic pitch-up for Naruto's lines
            res_len = int(len(samples) / 1.07)
            samples = np.interp(np.linspace(0, len(samples) - 1, res_len), np.arange(len(samples)), samples).astype(np.float32)
        max_slot = int((en - st - 0.15) * SR)
        if len(samples) > max_slot > 0:
            samples = np.interp(np.linspace(0, len(samples) - 1, max_slot), np.arange(len(samples)), samples).astype(np.float32)
        s0 = int(st * SR)
        s1 = min(TOTAL_SAMPLES, s0 + len(samples))
        seg = samples[: s1 - s0]
        peak = float(np.max(np.abs(seg))) if len(seg) else 0.0
        if peak > 1e-4:
            seg = seg / peak * 0.78
        voice_track[s0:s1] += seg
        voice_env[max(0, s0 - int(0.15 * SR)) : min(TOTAL_SAMPLES, s1 + int(0.25 * SR))] = 1.0

    # Procedural Cinematic Soundtrack & Foley Score
    t = np.arange(TOTAL_SAMPLES, dtype=np.float32) / SR
    music = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    sfx = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

    def add_tone(buf: np.ndarray, t0: float, dur: float, freq: float, amp: float, kind: str = "sine", f_end: float | None = None):
        i0 = max(0, int(t0 * SR))
        i1 = min(TOTAL_SAMPLES, int((t0 + dur) * SR))
        if i1 <= i0:
            return
        lt = np.arange(i1 - i0, dtype=np.float32) / SR
        if f_end is not None:
            phase = 2 * np.pi * (freq * lt + 0.5 * (f_end - freq) * (lt ** 2) / max(dur, 0.01))
        else:
            phase = 2 * np.pi * freq * lt
        wave_sig = np.sin(phase) if kind == "sine" else np.sign(np.sin(phase)) * 0.6 + 0.4 * np.sin(phase)
        env = np.minimum(lt / 0.03, 1.0) * np.exp(-lt / max(dur * 0.55, 0.05))
        buf[i0:i1] += (wave_sig * env * amp).astype(np.float32)

    # Scene 1 (0-15s): Sub-bass rumble + dusk motif + title impact at 8.2s
    add_tone(music, 0.0, 6.8, 55.0, 0.16, "sine", 48.0)
    for note_t, f in [(1.5, 293.66), (2.2, 329.63), (3.0, 392.00), (4.0, 440.00), (5.2, 392.00)]:
        add_tone(music, note_t, 0.85, f, 0.08)
    # 8.2s Title Impact Hit
    add_tone(sfx, 8.2, 1.1, 110.0, 0.28, "saw", 42.0)
    add_tone(sfx, 8.2, 1.2, 220.0, 0.18, "sine", 110.0)

    # Scene 2 (15-40s): Phone taps (16-21s), M-PESA confirmation tone (22.2s), shock sting (23.8s), silence (30-35s)
    for tap_t in [16.2, 16.7, 17.3, 18.0, 18.6, 19.4, 20.3]:
        add_tone(sfx, tap_t, 0.06, 980.0, 0.12)
    add_tone(sfx, 22.1, 0.18, 587.33, 0.18)
    add_tone(sfx, 22.28, 0.35, 880.0, 0.20)
    # Shock sting at 23.8s
    add_tone(sfx, 23.8, 0.9, 466.16, 0.24, "saw", 146.83)
    add_tone(sfx, 23.85, 0.9, 311.13, 0.18, "saw", 110.0)

    # Scene 3 (40-65s): Rising heartbeat & ticking pulse, cutting to complete silence at 62.0s!
    hb_t = 40.2
    while hb_t < 61.6:
        add_tone(sfx, hb_t, 0.14, 68.0, 0.22)
        add_tone(sfx, hb_t + 0.18, 0.18, 58.0, 0.18)
        add_tone(sfx, hb_t + 0.45, 0.04, 1250.0, 0.07)
        hb_t += 0.85

    # Scene 4 (65-80s): Shimmering SafeUndo Reveal & Confident Progression
    for i, f in enumerate([261.63, 329.63, 392.00, 523.25, 659.25]):
        add_tone(sfx, 65.1 + i * 0.08, 0.9, f, 0.14)
    for chord_t, root in [(66.0, 261.63), (70.0, 293.66), (74.5, 329.63)]:
        add_tone(music, chord_t, 3.8, root, 0.09)
        add_tone(music, chord_t, 3.8, root * 1.25, 0.07)
        add_tone(music, chord_t, 3.8, root * 1.5, 0.07)

    # Scene 5 (80-115s): Proactive Protection Demo — Warning Alert & Cancellation Resolution
    add_tone(sfx, 85.0, 0.16, 740.0, 0.18, "saw")
    add_tone(sfx, 85.22, 0.22, 740.0, 0.18, "saw")
    for chord_t, root in [(81.0, 220.0), (88.0, 246.94), (96.0, 261.63), (104.5, 293.66), (110.0, 329.63)]:
        add_tone(music, chord_t, 5.5, root, 0.08)
        add_tone(music, chord_t, 5.5, root * 1.5, 0.06)
    # Positive cancellation chime at 104.2s
    add_tone(sfx, 104.2, 0.2, 523.25, 0.16)
    add_tone(sfx, 104.4, 0.35, 783.99, 0.18)

    # Scene 6 (115-145s): Guided Reversal & Status Tracker Chimes
    for chord_t, root in [(116.0, 261.63), (124.0, 293.66), (132.0, 329.63), (139.0, 349.23)]:
        add_tone(music, chord_t, 6.5, root, 0.08)
        add_tone(music, chord_t, 6.5, root * 1.25, 0.06)
    add_tone(sfx, 131.0, 0.2, 587.33, 0.15)
    add_tone(sfx, 131.2, 0.3, 880.0, 0.16)

    # Scene 7 (145-165s): Warm Orchestral Payoff
    for chord_t, root in [(145.5, 261.63), (151.0, 349.23), (156.5, 392.00), (161.0, 261.63)]:
        add_tone(music, chord_t, 5.0, root, 0.10)
        add_tone(music, chord_t, 5.0, root * 1.25, 0.08)
        add_tone(music, chord_t, 5.0, root * 1.5, 0.08)

    # Scene 8 (165-180s): Hero Crescendo + Sonic Signature (finishing cleanly before 180.0s)
    for chord_t, root in [(165.2, 261.63), (170.0, 329.63), (174.0, 392.00)]:
        add_tone(music, chord_t, 4.5, root, 0.11)
        add_tone(music, chord_t, 4.5, root * 1.25, 0.09)
        add_tone(music, chord_t, 4.5, root * 1.5, 0.09)
    # Final Sonic Signature at 175.5s
    for i, f in enumerate([523.25, 659.25, 783.99, 1046.50]):
        add_tone(sfx, 175.2 + i * 0.14, 1.8, f, 0.16)

    # Apply audio ducking to music/sfx when voice is active
    duck = 1.0 - 0.62 * voice_env
    mix = voice_track + (music * duck) + (sfx * (1.0 - 0.35 * voice_env))
    # Clean fade-out on final 0.25s so 03:00 has zero pop/tail
    fade_len = int(0.25 * SR)
    mix[-fade_len:] *= np.linspace(1.0, 0.0, fade_len, dtype=np.float32)
    mix = np.clip(mix, -0.98, 0.98)

    # Compute per-frame (30fps) voice amplitude for lip-sync mouth animation
    frame_samples = SR // FPS
    lip_amp = np.array([
        float(np.sqrt(np.mean(voice_track[i * frame_samples : (i + 1) * frame_samples] ** 2)))
        for i in range(TOTAL_FRAMES)
    ])

    wav_out = tmp_dir / "master_180s.wav"
    pcm16 = (mix * 32767.0).astype(np.int16)
    stereo = np.column_stack([pcm16, pcm16]).ravel()
    with wave.open(str(wav_out), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(stereo.tobytes())

    return wav_out, lip_amp


def get_fonts():
    try:
        return {
            "h1": ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 44),
            "h2": ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 32),
            "h3": ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 24),
            "body": ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 23),
            "small": ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 19),
            "mono": ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 22),
            "timer": ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 28),
            "hero": ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 74),
        }
    except Exception:
        d = ImageFont.load_default()
        return {k: d for k in ("h1", "h2", "h3", "body", "small", "mono", "timer", "hero")}


def draw_naruto_avatar(draw: ImageDraw.ImageDraw, cx: int, cy: int, shocked: bool, mouth_open: bool, thumb_offset: int, phone_label: str):
    """Draw expressive Naruto Uzumaki anime character rig (spiky blond hair, leaf headband, whisker marks, orange/black jacket)."""
    # Chakra / mood aura
    aura_col = (255, 71, 87) if shocked else (255, 125, 30)
    draw.ellipse([cx - 210, cy - 220, cx + 210, cy + 220], fill=(aura_col[0] // 5, aura_col[1] // 5, aura_col[2] // 5))
    draw.ellipse([cx - 170, cy - 180, cx + 170, cy + 180], fill=(aura_col[0] // 4, aura_col[1] // 4, aura_col[2] // 4))

    # Spiky golden-blond hair (crown spikes)
    spikes = [
        (cx, cy - 245), (cx - 42, cy - 185), (cx - 98, cy - 228), (cx - 82, cy - 162),
        (cx - 144, cy - 184), (cx - 104, cy - 115), (cx - 148, cy - 94), (cx - 94, cy - 60),
        (cx + 94, cy - 60), (cx + 148, cy - 94), (cx + 104, cy - 115), (cx + 144, cy - 184),
        (cx + 82, cy - 162), (cx + 98, cy - 228), (cx + 42, cy - 185),
    ]
    draw.polygon(spikes, fill=(255, 206, 42), outline=(204, 148, 0))

    # Iconic Orange & Black Jacket Shoulders
    draw.polygon([
        (cx - 165, cy + 250), (cx - 135, cy + 95), (cx - 65, cy + 68),
        (cx + 65, cy + 68), (cx + 135, cy + 95), (cx + 165, cy + 250)
    ], fill=(255, 122, 28), outline=(28, 34, 48))
    draw.polygon([
        (cx - 68, cy + 72), (cx - 45, cy + 250), (cx + 45, cy + 250), (cx + 68, cy + 72)
    ], fill=(24, 30, 44))
    # High Black/White Collar
    draw.polygon([
        (cx - 78, cy + 28), (cx - 55, cy + 86), (cx + 55, cy + 86), (cx + 78, cy + 28),
        (cx + 55, cy + 18), (cx - 55, cy + 18)
    ], fill=(30, 38, 54), outline=(235, 240, 248))

    # Neck & Face
    draw.rectangle([cx - 26, cy + 4, cx + 26, cy + 56], fill=(242, 192, 154))
    draw.ellipse([cx - 84, cy - 132, cx + 84, cy + 36], fill=(248, 204, 166), outline=(140, 92, 56))

    # Forehead Protector (Headband)
    draw.rectangle([cx - 86, cy - 132, cx + 86, cy - 92], fill=(30, 42, 64), outline=(15, 23, 42))
    draw.rounded_rectangle([cx - 44, cy - 125, cx + 44, cy - 98], radius=6, fill=(204, 214, 226), outline=(71, 85, 105))
    # Leaf swirl emblem in plate
    draw.arc([cx - 12, cy - 119, cx + 8, cy - 103], start=0, end=300, fill=(30, 42, 64), width=3)

    # Blond front bangs over headband
    bangs = [
        (cx - 82, cy - 132), (cx - 64, cy - 82), (cx - 46, cy - 126), (cx - 22, cy - 86),
        (cx, cy - 132), (cx + 22, cy - 86), (cx + 46, cy - 126), (cx + 64, cy - 82), (cx + 82, cy - 132)
    ]
    draw.polygon(bangs, fill=(255, 214, 51))

    # 3 Whisker Marks on Each Cheek
    for dy in (-22, -10, 2):
        draw.line([(cx - 74, cy + dy), (cx - 42, cy + dy + 3)], fill=(138, 88, 52), width=3)
        draw.line([(cx + 74, cy + dy), (cx + 42, cy + dy + 3)], fill=(138, 88, 52), width=3)

    # Eyes (Cerulean Blue Anime Eyes vs Wide Shock Eyes)
    for ex in (cx - 38, cx + 38):
        if shocked:
            draw.ellipse([ex - 21, cy - 68, ex + 21, cy - 22], fill=(255, 255, 255), outline=(15, 15, 15), width=3)
            draw.ellipse([ex - 7, cy - 51, ex + 7, cy - 37], fill=(30, 144, 255))
            draw.ellipse([ex - 3, cy - 47, ex + 3, cy - 41], fill=(0, 0, 0))
        else:
            draw.ellipse([ex - 19, cy - 64, ex + 19, cy - 26], fill=(255, 255, 255), outline=(15, 15, 15), width=3)
            draw.ellipse([ex - 12, cy - 57, ex + 12, cy - 33], fill=(30, 144, 255))
            draw.ellipse([ex - 6, cy - 51, ex + 6, cy - 39], fill=(10, 24, 42))
            draw.ellipse([ex - 9, cy - 55, ex - 3, cy - 49], fill=(255, 255, 255))

    # Eyebrows
    if shocked:
        draw.line([(cx - 60, cy - 82), (cx - 20, cy - 68)], fill=(180, 122, 0), width=5)
        draw.line([(cx + 20, cy - 68), (cx + 60, cy - 82)], fill=(180, 122, 0), width=5)
    else:
        draw.line([(cx - 60, cy - 72), (cx - 20, cy - 76)], fill=(180, 122, 0), width=5)
        draw.line([(cx + 20, cy - 76), (cx + 60, cy - 72)], fill=(180, 122, 0), width=5)

    # Mouth (Lip-Synced to Voice Waveform or Shocked)
    if shocked and not mouth_open:
        draw.ellipse([cx - 16, cy - 4, cx + 16, cy + 22], fill=(64, 24, 18), outline=(40, 15, 10), width=2)
    elif mouth_open:
        draw.ellipse([cx - 15, cy - 2, cx + 15, cy + 16], fill=(214, 68, 80), outline=(80, 32, 20), width=2)
    else:
        draw.arc([cx - 22, cy - 6, cx + 22, cy + 16], start=15, end=165, fill=(92, 45, 22), width=4)

    # Smartphone held in hand + animated thumb
    px, py = cx + 62, cy + 56
    draw.rounded_rectangle([px, py, px + 88, py + 152], radius=14, fill=(11, 15, 24), outline=(105, 240, 174), width=3)
    draw.rounded_rectangle([px + 8, py + 14, px + 80, py + 126], radius=8, fill=(18, 42, 30))
    # Thumb hovering over screen
    ty = py + 95 + thumb_offset
    draw.ellipse([px + 54, ty - 11, px + 92, ty + 11], fill=(248, 204, 166), outline=(138, 88, 52), width=2)


def render_right_panel(scene_id: int, sub_phase: int, fonts: dict) -> Image.Image:
    """Pre-render crisp right-hand story & actual SafeUndo UI cards for each scene/sub-phase."""
    panel = Image.new("RGBA", (1020, 740), (0, 0, 0, 0))
    d = ImageDraw.Draw(panel)

    def card(box, border_col, bg_col=(18, 25, 38, 242)):
        d.rounded_rectangle(box, radius=26, fill=bg_col, outline=border_col, width=3)

    if scene_id == 1:
        card([20, 110, 990, 620], (255, 120, 31))
        d.text((64, 155), "SCENE 1 · 00:00–00:15 · THE CINEMATIC HOOK", font=fonts["small"], fill=(255, 163, 102))
        d.text((64, 205), "SAFEUNDO", font=fonts["hero"], fill=(255, 255, 255))
        d.text((64, 300), "One mistake. A smarter way forward.", font=fonts["h2"], fill=(105, 240, 174))
        d.text((64, 375), "Nairobi at dusk. Naruto prepares a routine M-PESA transfer,", font=fonts["body"], fill=(210, 220, 238))
        d.text((64, 412), "his thumb hovering a millimetre above the confirmation key.", font=fonts["body"], fill=(210, 220, 238))
        d.rounded_rectangle([64, 470, 930, 575], radius=16, fill=(12, 17, 26), outline=(67, 176, 42), width=2)
        d.text((92, 495), "Central Question:", font=fonts["small"], fill=(105, 240, 174))
        d.text((92, 525), "\"What happens when one wrong tap sends your money to the wrong person?\"", font=fonts["body"], fill=(255, 255, 255))

    elif scene_id == 2:
        card([20, 80, 990, 650], (255, 71, 87))
        d.text((64, 120), "SCENE 2 · 00:15–00:40 · THE MISTAKE", font=fonts["small"], fill=(255, 120, 130))
        d.text((64, 162), "\"Wait... I sent it to the wrong person!\"", font=fonts["h1"], fill=(255, 255, 255))
        # USSD Confirmation Modal Replica
        d.rounded_rectangle([64, 240, 930, 475], radius=20, fill=(37, 39, 44), outline=(255, 71, 87), width=3)
        d.text((96, 268), "RK94X2M10P Confirmed.", font=fonts["mono"], fill=(255, 190, 195))
        d.text((96, 308), "KSh 2,000.00 sent to NANCY KAMAU", font=fonts["mono"], fill=(255, 255, 255))
        d.text((96, 348), "on 28/10/26 at 7:15 PM.", font=fonts["mono"], fill=(210, 215, 225))
        d.text((96, 388), "New M-PESA balance: KSh 22,310.50.", font=fonts["mono"], fill=(105, 240, 174))
        d.text((96, 428), "(Intended recipient: Mama Wanjiru · 07XX XXX 401)", font=fonts["small"], fill=(255, 179, 0))
        d.text((64, 510), "Match cut from the confirmation screen to Naruto's widened eyes", font=fonts["body"], fill=(220, 228, 242))
        d.text((64, 548), "as the unfamiliar recipient name registers a second too late.", font=fonts["body"], fill=(220, 228, 242))

    elif scene_id == 3:
        card([20, 80, 990, 650], (255, 179, 0))
        d.text((64, 120), "SCENE 3 · 00:40–01:05 · PANIC & THE REVERSAL PROBLEM", font=fonts["small"], fill=(255, 195, 64))
        d.text((64, 162), "The Uncertainty After the Mistake", font=fonts["h1"], fill=(255, 255, 255))
        d.rounded_rectangle([64, 245, 495, 560], radius=18, fill=(14, 19, 30), outline=(255, 179, 0), width=2)
        d.text((90, 275), "1. Which Reversal Route?", font=fonts["h3"], fill=(255, 195, 64))
        d.text((90, 325), "Send Money uses 456 SMS.", font=fonts["body"], fill=(225, 232, 245))
        d.text((90, 362), "Buy Goods Tills (523417),", font=fonts["body"], fill=(225, 232, 245))
        d.text((90, 399), "PayBills (247247), and Pochi", font=fonts["body"], fill=(225, 232, 245))
        d.text((90, 436), "each need different steps.", font=fonts["body"], fill=(225, 232, 245))

        d.rounded_rectangle([520, 245, 945, 560], radius=18, fill=(14, 19, 30), outline=(255, 179, 0), width=2)
        d.text((546, 275), "2. Zero Status Visibility", font=fonts["h3"], fill=(255, 195, 64))
        d.text((546, 325), "Hours pass Under Review.", font=fonts["body"], fill=(225, 232, 245))
        d.text((546, 362), "Will it take 5 hours or 2 days?", font=fonts["body"], fill=(225, 232, 245))
        d.text((546, 399), "Is delay risk low or elevated?", font=fonts["body"], fill=(225, 232, 245))
        d.text((546, 436), "What should the customer do?", font=fonts["body"], fill=(225, 232, 245))

    elif scene_id == 4:
        card([20, 110, 990, 620], (0, 229, 255))
        d.text((64, 155), "SCENE 4 · 01:05–01:20 · THE SAFEUNDO REVEAL", font=fonts["small"], fill=(0, 229, 255))
        d.text((64, 210), "SAFEUNDO — THINK BEFORE IT SENDS.", font=fonts["h1"], fill=(255, 255, 255))
        d.text((64, 295), "1. Pre-Transaction Behavioural Warning (Isolation Forest + Hakikisha)", font=fonts["h3"], fill=(105, 240, 174))
        d.text((64, 345), "2. Transaction-Type Guided Reversal (Send Money 456 / Till / PayBill)", font=fonts["h3"], fill=(105, 240, 174))
        d.text((64, 395), "3. Predictive Resolution Time & 24h Delay-Risk Tracker (Random Forest)", font=fonts["h3"], fill=(105, 240, 174))
        d.text((64, 470), "One shared FastAPI + scikit-learn backend across *334# USSD and My OneApp.", font=fonts["body"], fill=(200, 214, 235))

    elif scene_id == 5:
        canceled = sub_phase >= 1
        card([20, 50, 990, 685], (67, 176, 42) if canceled else (255, 179, 0))
        d.text((56, 84), "SCENE 5 · 01:20–01:55 · LIVE DEMO: PROACTIVE PROTECTION", font=fonts["small"], fill=(105, 240, 174))
        # Left Phone: *334# USSD Simulator
        d.rounded_rectangle([54, 130, 500, 645], radius=24, fill=(12, 16, 24), outline=(70, 85, 115), width=2)
        d.text((80, 152), "USSD *334# Simulator", font=fonts["small"], fill=(160, 175, 200))
        d.rounded_rectangle([74, 195, 480, 540], radius=16, fill=(38, 40, 45), outline=(67, 176, 42) if canceled else (255, 179, 0), width=3)
        if not canceled:
            d.text((94, 218), "Unusual transaction detected", font=fonts["h3"], fill=(255, 195, 64))
            d.text((94, 260), "KSh 20,000 to NANCY KAMAU", font=fonts["mono"], fill=(255, 255, 255))
            d.text((94, 305), "This amount is higher than", font=fonts["mono"], fill=(230, 235, 242))
            d.text((94, 336), "what you usually transact.", font=fonts["mono"], fill=(230, 235, 242))
            d.text((94, 367), "Please confirm the recipient", font=fonts["mono"], fill=(230, 235, 242))
            d.text((94, 398), "name and amount.", font=fonts["mono"], fill=(230, 235, 242))
            d.text((94, 445), "1. Yes, continue", font=fonts["mono"], fill=(105, 240, 174))
            d.text((94, 480), "2. Cancel", font=fonts["mono"], fill=(255, 195, 64))
        else:
            d.text((94, 250), "Transaction cancelled.", font=fonts["h3"], fill=(105, 240, 174))
            d.text((94, 300), "No money was sent.", font=fonts["mono"], fill=(255, 255, 255))
            d.text((94, 355), "Balance intact: KSh 24,310.50", font=fonts["mono"], fill=(105, 240, 174))

        # Right Phone: Simulated My OneApp Android Warning Sheet
        d.rounded_rectangle([524, 130, 965, 645], radius=24, fill=(12, 16, 24), outline=(70, 85, 115), width=2)
        d.text((550, 152), "Simulated My OneApp (Android)", font=fonts["small"], fill=(160, 175, 200))
        d.rounded_rectangle([544, 195, 945, 595], radius=18, fill=(23, 30, 44), outline=(67, 176, 42) if canceled else (255, 179, 0), width=2)
        d.text((568, 222), "SafeUndo Protection Sheet", font=fonts["h3"], fill=(255, 195, 64) if not canceled else (105, 240, 174))
        d.text((568, 272), "Amount: KSh 20,000", font=fonts["body"], fill=(255, 255, 255))
        d.text((568, 312), "Sending to: NANCY KAMAU", font=fonts["body"], fill=(105, 240, 174))
        d.text((568, 355), "Unusualness score: 100 / 100", font=fonts["small"], fill=(255, 195, 64))
        d.text((568, 398), "Signals: Amount ratio + Balance", font=fonts["small"], fill=(185, 198, 220))
        d.rounded_rectangle([568, 455, 920, 505], radius=12, fill=(67, 176, 42))
        d.text((650, 466), "Cancel / Stop Transfer", font=fonts["small"], fill=(255, 255, 255))
        d.text((568, 530), "Warns, never blocks legitimate pay.", font=fonts["small"], fill=(155, 170, 195))

    elif scene_id == 6:
        card([20, 50, 990, 685], (67, 176, 42))
        d.text((56, 84), "SCENE 6 · 01:55–02:25 · GUIDED REVERSAL & PREDICTIVE TRACKING", font=fonts["small"], fill=(105, 240, 174))
        # Left Phone: USSD *334# > 3 > 2 Case View
        d.rounded_rectangle([54, 130, 500, 645], radius=24, fill=(12, 16, 24), outline=(70, 85, 115), width=2)
        d.text((80, 152), "USSD *334# > 3 > 2", font=fonts["small"], fill=(160, 175, 200))
        d.rounded_rectangle([74, 195, 480, 560], radius=16, fill=(38, 40, 45), outline=(67, 176, 42), width=3)
        d.text((94, 220), "SU-1042 Under review", font=fonts["h3"], fill=(105, 240, 174))
        d.text((94, 265), "KSh 5,000 Send Money", font=fonts["mono"], fill=(255, 255, 255))
        d.text((94, 305), "Est. 5-9 hours remaining", font=fonts["mono"], fill=(255, 255, 255))
        d.text((94, 345), "Delay risk 8% (Low)", font=fonts["mono"], fill=(105, 240, 174))
        d.text((94, 390), "No action needed. Wait", font=fonts["mono"], fill=(220, 228, 240))
        d.text((94, 422), "for the next update.", font=fonts["mono"], fill=(220, 228, 240))
        d.text((94, 470), "(simulated)  0. Back", font=fonts["mono"], fill=(165, 175, 190))

        # Right Phone: My OneApp Case Detail & Timeline
        d.rounded_rectangle([524, 130, 965, 645], radius=24, fill=(12, 16, 24), outline=(70, 85, 115), width=2)
        d.text((550, 152), "My OneApp · Case SU-1042", font=fonts["small"], fill=(160, 175, 200))
        d.rounded_rectangle([544, 195, 945, 605], radius=18, fill=(23, 30, 44), outline=(67, 176, 42), width=2)
        d.text((568, 220), "Step 1: Forward SMS to 456", font=fonts["h3"], fill=(105, 240, 174))
        d.text((568, 265), "Timeline (Simulated):", font=fonts["small"], fill=(180, 195, 220))
        d.text((568, 298), "[x] Submitted  ->  [*] Under review", font=fonts["mono"], fill=(255, 255, 255))
        d.text((568, 332), "[ ] Approved   ->  [ ] Completed", font=fonts["mono"], fill=(150, 165, 190))
        d.text((568, 382), "Random Forest ETA: 5-9 hours", font=fonts["body"], fill=(255, 255, 255))
        d.text((568, 420), "80% Prediction Interval · Low Risk", font=fonts["small"], fill=(105, 240, 174))
        d.text((568, 465), "Buy Goods / PayBill: Contact merchant", font=fonts["small"], fill=(255, 195, 64))
        d.text((568, 495), "with M-PESA ID (SU-1044 tracked).", font=fonts["small"], fill=(255, 195, 64))

    elif scene_id == 7:
        card([20, 110, 990, 620], (255, 120, 31))
        d.text((64, 155), "SCENE 7 · 02:25–02:45 · THE PAYOFF & VISUAL CALLBACK", font=fonts["small"], fill=(255, 163, 102))
        d.text((64, 210), "Same Thumb. Same Phone. A Better Decision.", font=fonts["h1"], fill=(255, 255, 255))
        d.text((64, 295), "Protecting your money is not only about detecting a mistake.", font=fonts["body"], fill=(220, 230, 245))
        d.text((64, 335), "It is about helping you pause before an unusual payment completes,", font=fonts["body"], fill=(220, 230, 245))
        d.text((64, 375), "and giving you clear, honest status tracking when a reversal is", font=fonts["body"], fill=(220, 230, 245))
        d.text((64, 415), "underway across both *334# USSD and My OneApp.", font=fonts["body"], fill=(220, 230, 245))
        d.rounded_rectangle([64, 475, 930, 565], radius=16, fill=(18, 38, 26), outline=(67, 176, 42), width=2)
        d.text((92, 506), "Visual Callback: Naruto pauses, verifies the recipient & amount, and stays in control.", font=fonts["small"], fill=(105, 240, 174))

    elif scene_id == 8:
        card([20, 95, 990, 635], (105, 240, 174))
        d.text((64, 140), "SCENE 8 · 02:45–03:00 · FINAL IMPACT", font=fonts["small"], fill=(105, 240, 174))
        d.text((64, 195), "SAFEUNDO", font=fonts["hero"], fill=(255, 255, 255))
        d.text((64, 295), "Catch the unusual. Guide the reversal. Protect the decision.", font=fonts["h2"], fill=(105, 240, 174))
        d.text((64, 365), "One mistake. A smarter way forward.", font=fonts["h3"], fill=(255, 163, 102))
        d.text((64, 435), "• Isolation Forest Pre-Transaction Warning + Hakikisha Name Display", font=fonts["body"], fill=(220, 230, 245))
        d.text((64, 475), "• Transaction-Type Guided Reversal (Send Money 456 / Till / PayBill)", font=fonts["body"], fill=(220, 230, 245))
        d.text((64, 515), "• Random Forest Resolution-Time Range & 24h Delay-Risk Tracker", font=fonts["body"], fill=(220, 230, 245))
        d.text((64, 570), "Prototype demonstration · 100% Synthetic Data · Exact 03:00 Runtime", font=fonts["small"], fill=(155, 170, 195))

    return panel


def main():
    tmp_dir = Path(tempfile.mkdtemp(prefix="safeundo_film_"))
    print("1/3 Synthesizing voice-over, Naruto dialogue, and 180.000s master audio mix...")
    wav_path, lip_amp = build_master_audio(tmp_dir)

    fonts = get_fonts()

    # Pre-render static Nairobi dusk background template
    bg_base = Image.new("RGB", (W, H), (8, 12, 20))
    bg_draw = ImageDraw.Draw(bg_base)
    for y in range(H):
        r = int(8 + 18 * (y / H))
        g = int(12 + 16 * (y / H))
        b = int(22 + 28 * (y / H))
        bg_draw.line([(0, y), (W, y)], fill=(r, g, b))
    # Nairobi dusk skyline silhouettes
    skyline = [(60, 740, 110, 340), (190, 680, 95, 400), (310, 620, 82, 460), (415, 720, 130, 360),
               (1380, 700, 105, 380), (1510, 650, 115, 430), (1650, 725, 140, 355)]
    for x, y, w, h in skyline:
        bg_draw.rectangle([x, y, x + w, y + h], fill=(12, 17, 28))

    # Pre-render character sprites (normal closed, normal open, shocked closed, shocked open) + thumb offsets
    char_sprites: dict[tuple[bool, bool, int], Image.Image] = {}
    for shocked in (False, True):
        for mouth_open in (False, True):
            for t_off in (-6, 0, 6):
                sp = Image.new("RGBA", (620, 680), (0, 0, 0, 0))
                sd = ImageDraw.Draw(sp)
                draw_naruto_avatar(sd, 310, 320, shocked, mouth_open, t_off, "SAFEUNDO")
                char_sprites[(shocked, mouth_open, t_off)] = sp

    # Pre-render right-hand scene cards
    right_panels: dict[tuple[int, int], Image.Image] = {}
    for s_id in range(1, 9):
        for sub in (0, 1):
            right_panels[(s_id, sub)] = render_right_panel(s_id, sub, fonts)

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    OUT_MP4.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        ffmpeg_exe, "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
        "-i", "-",
        "-i", str(wav_path),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        "-t", "180.000",
        str(OUT_MP4),
    ]

    print(f"2/3 Rendering {TOTAL_FRAMES} Full-HD (1920x1080 @ 30fps) frames into {OUT_MP4.name}...")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None

    for f_idx in range(TOTAL_FRAMES):
        sec = f_idx / FPS
        # Determine scene
        sc = SCENES[0]
        for s in SCENES:
            if sec >= s[1]:
                sc = s
        s_id, s_start, s_end, s_code, s_title, s_shot = sc

        # Determine active subtitle cue
        spk, sub_txt = "SAFEUNDO", ""
        for cst, cen, cspk, csub, _, _, _ in SCRIPT_CUES:
            if cst <= sec < cen:
                spk, sub_txt = cspk, csub
                break

        frame = bg_base.copy()
        fd = ImageDraw.Draw(frame)

        # Animated dusk traffic lights along highway
        for i in range(12):
            tx = int((sec * 140 + i * 165) % (W + 80)) - 40
            col = (255, 179, 0) if i % 2 == 0 else (255, 71, 87)
            fd.rectangle([tx, 935 + (i % 3) * 8, tx + 42, 939 + (i % 3) * 8], fill=col)

        # Scene 1 opening fade-in from black (first 1.0s)
        shocked = (s_id == 2 and sec >= 23.5) or (s_id == 3)
        mouth_open = lip_amp[f_idx] > 0.045
        t_off = (-6 if (f_idx // 8) % 3 == 0 else (6 if (f_idx // 8) % 3 == 1 else 0)) if s_id in (1, 7) else 0

        # Dramatic anime impact speed lines in Scene 2
        if s_id == 2 and sec >= 23.8:
            for k in range(24):
                ang = (k / 24.0) * 2 * math.pi + (f_idx * 0.05)
                x0 = int(430 + math.cos(ang) * 140)
                y0 = int(500 + math.sin(ang) * 140)
                x1 = int(430 + math.cos(ang) * 900)
                y1 = int(500 + math.sin(ang) * 900)
                fd.line([(x0, y0), (x1, y1)], fill=(95, 28, 38), width=2)

        # Composite Naruto character sprite on left stage
        sp = char_sprites[(shocked, mouth_open, t_off)]
        bob_y = int(math.sin(sec * 2.2) * 6)
        frame.paste(sp, (115, 180 + bob_y), sp)

        # Shot badge above Naruto
        fd.rounded_rectangle([180, 140, 640, 184], radius=20, fill=(255, 120, 31))
        fd.text((202, 150), s_shot, font=fonts["small"], fill=(15, 8, 0))

        # Composite right-hand visual card
        sub_phase = 1 if (s_id == 5 and sec >= 103.8) else 0
        rp = right_panels[(s_id, sub_phase)]
        frame.paste(rp, (820, 130), rp)

        # Top HUD Bar (Scene Pill + MM:SS / 03:00 Master Clock)
        fd.rounded_rectangle([48, 32, 980, 92], radius=28, fill=(14, 19, 30), outline=(45, 58, 86), width=2)
        fd.text((76, 48), f"SCENE {s_id}/8  ·  {s_code}  ·  {s_title}", font=fonts["small"], fill=(255, 255, 255))

        disp_sec = TOTAL_S if f_idx == TOTAL_FRAMES - 1 else int(sec)
        mm_ss = f"{disp_sec // 60:02d}:{disp_sec % 60:02d} / 03:00"
        fd.rounded_rectangle([1560, 32, 1872, 92], radius=28, fill=(14, 19, 30), outline=(67, 176, 42), width=3)
        fd.text((1602, 46), mm_ss, font=fonts["timer"], fill=(105, 240, 174))

        # Progress bar at top of caption box
        fd.rounded_rectangle([64, 955, 1856, 1052], radius=20, fill=(6, 9, 15), outline=(45, 58, 86), width=2)
        prog_w = int(1788 * ((f_idx + 1) / TOTAL_FRAMES))
        fd.rounded_rectangle([66, 957, 66 + max(8, prog_w), 963], radius=3, fill=(67, 176, 42))
        fd.text((96, 970), spk, font=fonts["small"], fill=(255, 163, 102))
        fd.text((96, 1000), sub_txt, font=fonts["body"], fill=(255, 255, 255))

        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    stderr_bytes = proc.stderr.read() if proc.stderr else b""
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"FFmpeg failed ({rc}): {stderr_bytes.decode('utf-8', errors='replace')}")

    shutil.copy2(OUT_MP4, DOWNLOADS_MP4)
    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"3/3 Rendered MP4 successfully: {OUT_MP4} ({OUT_MP4.stat().st_size / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    main()

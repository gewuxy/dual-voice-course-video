#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""片头配乐生成器（参数化，可复现）。

设计（2026-10-08 L3 片头定稿版）：
  100 BPM、C 大调 I–V/V–vi–IV 循环（C–G/B–Am–F），
  卡林巴式琶音（根-五-三-八度，八分音符）+ 低八度铺底 pad + 轻反拍沙锤 + 合成混响。
  卡点铃铛默认关闭（用户 2026-10-08 明确不要，见 SKILL.md 阶段 4d）。

依赖：numpy + scipy；WAV 用标准库 wave 写（不需要 soundfile）。

用法：
  python make_intro_music.py --out music.wav --duration 5.0
  python make_intro_music.py --out music.wav --duration 6.5 --bpm 92 --bells --bell-times "0.6,1.7,2.6,3.4"
"""
import argparse, struct, wave
import numpy as np
import scipy.signal as sig

# C 大调 I–V/V–vi–IV（首和弦三音/五音按听感排布；循环使用以覆盖任意时长）
CHORDS = {
    "C": [(261.63, 329.63, 392.00),   # C4 E4 G4
          (246.94, 293.66, 392.00),   # G/B（B3 D4 G4）
          (220.00, 261.63, 329.63),   # Am（A3 C4 E4）
          (174.61, 220.00, 261.63)],  # F（F3 A3 C4）
}


def pluck(f, sr, amp=1.0, tau=0.30):
    """卡林巴/马林巴式拨奏：1/2/3.5/5 次谐波 + 指数衰减"""
    L = int(sr * 1.6)
    t = np.arange(L) / sr
    env = np.exp(-t / tau) * (1 - np.exp(-t / 0.004))
    x = np.zeros(L, dtype=np.float32)
    for h, g in ((1, 1.0), (2, 0.42), (3.5, 0.16), (5.0, 0.07)):
        x += g * np.sin(2 * np.pi * f * h * t) * np.exp(-t / (tau / h ** 0.6))
    return x * env * amp


def add(buf, f, t0, sr, amp=1.0, tau=0.30):
    x = pluck(f, sr, amp, tau)
    i = int(t0 * sr)
    L = min(len(x), len(buf) - i)
    if L > 0:
        buf[i:i + L] += x[:L]


def write_wav(path, y, sr):
    y = np.clip(y, -1.0, 1.0)
    pcm = (y * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def build(duration=5.0, bpm=100.0, sr=44100, seed=11, bells=None, key="C",
          peak_db=-11.7, wet=1.9, dry=0.86, shaker=0.05):
    n = int(sr * duration)
    tail = sr  # 混响尾巴
    out = np.zeros(n + tail, dtype=np.float32)
    rng = np.random.default_rng(seed)
    beat = 60.0 / bpm
    prog = CHORDS[key]

    # 1) 琶音 + 铺底：每和弦 2 拍，循环到铺满时长
    ci = 0
    t0 = 0.0
    while t0 < duration + 1.0:
        ch = prog[ci % len(prog)]
        for k, f in enumerate([ch[0], ch[2], ch[1], ch[0] * 2]):   # 根-五-三-八度
            add(out, f, t0 + k * beat / 2, sr, amp=0.46, tau=0.28)
        L = int(1.25 * sr)
        t = np.arange(L) / sr
        e = np.clip(t / 0.22, 0, 1) * np.clip((1.25 - t) / 0.45, 0, 1)
        for f in ch:
            i = int(t0 * sr)
            L2 = min(L, len(out) - i)
            out[i:i + L2] += (0.085 * np.sin(2 * np.pi * f / 2 * t) * e)[:L2].astype(np.float32)
        t0 += 2 * beat
        ci += 1

    # 2) 卡点铃铛（可选，默认关闭）
    for ts in (bells or []):
        add(out, 1046.5, float(ts), sr, amp=0.30, tau=0.42)

    # 3) 反拍沙锤
    if shaker > 0:
        k = 0
        while k * beat / 2 + beat / 4 < duration:
            t0s = k * beat / 2 + beat / 4
            L = int(0.06 * sr)
            t = np.arange(L) / sr
            sh = rng.normal(0, 1, L).astype(np.float32) * np.exp(-t / 0.012)
            b, a = sig.butter(2, 6000 / (sr / 2), "high")
            sh = sig.lfilter(b, a, sh)
            i = int(t0s * sr)
            L2 = min(L, len(out) - i)
            if L2 > 0:
                out[i:i + L2] += sh[:L2] * shaker
            k += 1

    # 4) 合成混响 + 收尾
    L = int(1.0 * sr)
    t = np.arange(L) / sr
    ir = (rng.normal(0, 1, L) * np.exp(-t / 0.28)).astype(np.float32)
    ir = sig.lfilter(*sig.butter(2, 7000 / (sr / 2), "low"), ir)
    ir /= np.abs(ir).sum()
    wet_sig = sig.fftconvolve(out, ir)[:len(out)].astype(np.float32)
    mix = (out * dry + wet_sig * wet)[:n]
    mix = sig.lfilter(*sig.butter(2, 12000 / (sr / 2), "low"), mix).astype(np.float32)
    mix *= np.clip(np.arange(n) / (0.02 * sr), 0, 1) * np.clip((n - np.arange(n)) / (0.42 * sr), 0, 1)
    mix = mix / (np.abs(mix).max() + 1e-12) * (10 ** (peak_db / 20.0))
    return mix


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--duration", type=float, default=5.0)
    ap.add_argument("--bpm", type=float, default=100.0)
    ap.add_argument("--sr", type=int, default=44100)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--key", default="C", choices=list(CHORDS))
    ap.add_argument("--peak-db", type=float, default=-11.7)
    ap.add_argument("--bells", action="store_true", help="加卡点铃铛（默认不加）")
    ap.add_argument("--bell-times", default="0.60,1.05,1.70,1.92,2.14,2.62,3.05",
                    help="铃铛时刻（秒，逗号分隔），仅 --bells 生效")
    a = ap.parse_args()
    bells = [float(x) for x in a.bell_times.split(",") if x.strip()] if a.bells else []
    y = build(a.duration, a.bpm, a.sr, a.seed, bells, a.key, a.peak_db)
    write_wav(a.out, y, a.sr)
    print("配乐 -> %s  %.2fs  %d Hz  峰值 %.1f dBFS  铃铛 %s"
          % (a.out, len(y) / a.sr, a.sr, 20 * np.log10(np.abs(y).max() + 1e-12),
             ("开（%d 声）" % len(bells)) if bells else "关"))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""原创合成：激昂进行曲风纯器乐 BGM（BPM 132，C 大调）。

风格：energetic / march / fanfare / driving / cinematic —— 向儿童英雄主题曲的
"昂扬、号召感"编制靠拢，但旋律、和声走向完全原创，不复制任何在保作品。
乐器：铜管风格锯齿波号角 + 拨弦低音 + 定音鼓/军鼓 + hi-hat，无人声。
首尾各 2.5 秒淡入淡出；实际混音音量由 Remotion 侧控制在 12%。
完全原创合成，无版权顾虑。
"""
import math
import random
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "audio" / "bgm.wav"
OUT.parent.mkdir(parents=True, exist_ok=True)

SR = 22050
BPM = 132
BEAT = 60.0 / BPM          # 每拍秒数
BAR = BEAT * 4             # 每小节秒数
DURATION = 96.0            # 循环足够覆盖成片
FADE = 2.5                 # 首尾淡入淡出秒数
random.seed(3262026)

# 音名 -> 频率（C 大调）
N = {
    'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61,
    'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23,
    'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46,
    'G5': 783.99, 'A5': 880.00, 'C6': 1046.50,
}

# 8 小节原创号角旋律（每小节 8 个八分音符；'_' 休止）
# 动机：上行号角 C-E-G-C6，随后级进回应，完全自创走向
MELODY = [
    ['C5', 'E5', 'G5', 'C6', '_', 'G5', 'E5', '_'],    # C
    ['D5', 'G5', 'B4', 'D5', '_', 'B4', 'G4', '_'],    # G
    ['E5', 'G5', 'C6', 'A5', '_', 'G5', 'E5', 'D5'],   # Am
    ['F5', 'A5', 'C6', 'A5', 'G5', 'F5', 'E5', '_'],   # F
    ['G5', 'C6', 'E5', 'G5', 'C6', '_', 'B4', 'G4'],   # C
    ['A4', 'D5', 'F5', 'A5', 'F5', 'D5', 'B4', '_'],   # Dm
    ['F5', 'E5', 'D5', 'C5', 'D5', 'E5', 'F5', 'G5'],  # F->G 推进
    ['G5', 'B4', 'D5', 'G5', 'C6', '_', 'G5', '_'],    # G 收束回 C
]
# 每小节和弦垫音 + 低音根音（进行曲常见的 I-V-vi-IV 变体）
CHORDS = [
    (['C4', 'E4', 'G4'], 'C3'),
    (['D4', 'G4', 'B4'], 'G3'),
    (['A3', 'C4', 'E4'], 'A3'),
    (['F4', 'A4', 'C5'], 'F3'),
    (['C4', 'E4', 'G4'], 'C3'),
    (['D4', 'F4', 'A4'], 'D3'),
    (['F4', 'A4', 'C5'], 'F3'),
    (['D4', 'G4', 'B4'], 'G3'),
]

n = int(SR * DURATION)
buf = [0.0] * n


def add_tone(start_sample, freq, dur, amp, kind='brass'):
    """叠加音符。brass=号角(锯齿+方波泛音)，bass=拨弦，pad=柔和垫音。"""
    if freq <= 0:
        return
    length = int(SR * min(dur, DURATION - start_sample / SR))
    if length <= 0:
        return
    for j in range(length):
        t = j / SR
        if kind == 'brass':
            # 快速起音、平稳保持、快速释放，带锯齿感泛音
            env = min(1.0, t / 0.012) * min(1.0, (dur - t) / 0.06)
            env = max(0.0, env) * math.exp(-t * 1.6)
            phase = 2 * math.pi * freq * t
            v = (math.sin(phase)
                 + 0.45 * math.sin(2 * phase)
                 + 0.25 * math.sin(3 * phase)
                 + 0.14 * math.sin(4 * phase))
        elif kind == 'bass':
            env = math.exp(-t * 4.0)
            phase = 2 * math.pi * freq * t
            v = math.sin(phase) + 0.30 * math.sin(2 * phase)
        else:  # pad
            env = min(1.0, t / 0.10) * math.exp(-t * 0.9)
            v = math.sin(2 * math.pi * freq * t)
        idx = int(start_sample) + j
        if 0 <= idx < n:
            buf[idx] += v * env * amp


def add_noise(start_sample, dur, amp, decay, tone='hat'):
    """打击乐。snare=军鼓(带中低频)，kick=底鼓(低频正弦扫频)，hat=hi-hat。"""
    length = int(SR * min(dur, DURATION - start_sample / SR))
    if length <= 0:
        return
    if tone == 'kick':
        for j in range(length):
            t = j / SR
            f = 110 * math.exp(-t * 30) + 45
            v = math.sin(2 * math.pi * f * t) * math.exp(-t * 12)
            idx = int(start_sample) + j
            if 0 <= idx < n:
                buf[idx] += v * amp
        return
    prev = 0.0
    for j in range(length):
        t = j / SR
        white = random.uniform(-1, 1)
        high = white - prev  # 高通 -> 清脆
        prev = white
        env = math.exp(-t * decay)
        if tone == 'snare':
            body = math.sin(2 * math.pi * 190 * t) * math.exp(-t * 22)
            v = (high * 0.7 + body * 0.5) * env
        else:
            v = high * env
        idx = int(start_sample) + j
        if 0 <= idx < n:
            buf[idx] += v * amp


bar_index = 0
t = 0.0
while t < DURATION - BAR:
    chord_notes, bass_root = CHORDS[bar_index % len(CHORDS)]
    melody = MELODY[bar_index % len(MELODY)]
    bar_start = t

    # 垫音：整小节轻柔铺底
    for note in chord_notes:
        add_tone(bar_start * SR, N[note], BAR * 0.96, 0.045, 'pad')

    # 低音：每拍拨弦，第 1/3 拍加重（进行曲强弱）
    for b in range(4):
        amp = 0.16 if b in (0, 2) else 0.10
        add_tone((bar_start + b * BEAT) * SR, N[bass_root], BEAT * 1.5, amp, 'bass')

    # 号角旋律：8 个八分音符
    for k, note in enumerate(melody):
        if note != '_' and note in N:
            add_tone((bar_start + k * BEAT / 2) * SR, N[note], 0.40, 0.17, 'brass')

    # 打击：底鼓 1/3 拍，军鼓 2/4 拍，hi-hat 八分音符
    for b in range(4):
        if b in (0, 2):
            add_noise((bar_start + b * BEAT) * SR, 0.22, 0.28, 0, 'kick')
        else:
            add_noise((bar_start + b * BEAT) * SR, 0.18, 0.20, 18, 'snare')
    for k in range(8):
        add_noise((bar_start + k * BEAT / 2) * SR, 0.05, 0.012, 95, 'hat')

    t += BAR
    bar_index += 1

# 归一化 + 首尾淡入淡出
peak = max(abs(x) for x in buf) or 1.0
scale = 0.55 / peak
samples = []
for i, x in enumerate(buf):
    tt = i / SR
    fade = min(1.0, tt / FADE, (DURATION - tt) / FADE)
    fade = max(0.0, fade)
    samples.append(int(max(-1, min(1, x * scale * fade)) * 32767))

with wave.open(str(OUT), "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(struct.pack(f"<{len(samples)}h", *samples))

print(f"wrote {OUT} ({DURATION}s, BPM={BPM}, {OUT.stat().st_size / 1024 / 1024:.1f} MB)")

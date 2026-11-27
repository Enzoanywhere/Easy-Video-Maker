#!/usr/bin/env python3
"""原创合成：弦乐激昂进行曲 BGM（BPM 126，C 大调）。

参考 pawpatrol-script3/out/参考_汪汪队主题曲_第三方完整版.mp3 的
气质骨架（BPM≈126、全程高能量、主题曲式循环），但旋律、节奏动机、
和声走向完全原创，不复制、不变调、不采样任何在保作品。

编制（纯器乐，无人声）：
  - 小提琴 I：号角式主旋律，明亮丰富泛音 + 快速揉弦
  - 小提琴 II / 中提琴：和声长音铺底，温暖对位
  - 大提琴：低音旋律线，慢揉弦 + 温暖泛音
  - 拨弦 pizzicato：低音节奏
  - 定音鼓 + 军鼓 + 小镲：进行曲打击
首尾各 2.5 秒淡入淡出；实际混音音量由 Remotion 侧控制在 12%。
完全原创合成，无版权顾虑。
"""
import math
import random
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "audio" / "bgm-strings.wav"
OUT.parent.mkdir(parents=True, exist_ok=True)

SR = 22050
BPM = 126
BEAT = 60.0 / BPM
BAR = BEAT * 4
DURATION = 96.0
FADE = 2.5
random.seed(7262026)

# C 大调音阶音名表（含低音区给大提琴）
N = {
    'C2': 65.41, 'D2': 73.42, 'E2': 82.41, 'F2': 87.31, 'G2': 98.00, 'A2': 110.00, 'B2': 123.47,
    'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61, 'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46, 'G5': 783.99, 'A5': 880.00, 'B5': 987.77,
    'C6': 1046.50, 'D6': 1174.66, 'E6': 1318.51,
}

# 8 小节原创小提琴主旋律（每小节 8 个八分音符，'_' 休止）
# 动机：C-E-G-C6 号角起势 → 属和弦回应 → 八度推进 → 大调收束
MELODY = [
    ['C5', 'E5', 'G5', 'C6', '_', 'G5', 'E5', '_'],   # C  起势
    ['D5', 'G5', 'B5', 'D6', '_', 'B5', 'G5', '_'],   # G  回应
    ['E5', 'A5', 'C6', 'A5', 'G5', 'E5', 'D5', '_'],  # Am 推进
    ['F5', 'A5', 'C6', 'A5', 'G5', 'F5', 'E5', '_'],  # F  舒展
    ['G5', 'C6', 'E6', 'C6', 'G5', 'E5', 'C5', '_'],  # C  高潮
    ['A5', 'C6', 'E6', 'C6', 'A5', 'E5', 'C5', '_'],  # Am 回望
    ['F5', 'G5', 'A5', 'C6', 'A5', 'G5', 'F5', 'E5'], # F  全音阶冲刺
    ['G5', 'B5', 'D6', 'B5', 'G5', '_', 'D5', '_'],   # G  收束回 C
]

# 大提琴低音旋律：每小节 2 个长音，与高音小提琴形成八度/五度对位
CELLO = [
    [('C3', 0), ('G3', 4)],
    [('G2', 0), ('D3', 4)],
    [('A2', 0), ('E3', 4)],
    [('F2', 0), ('C3', 4)],
    [('C3', 0), ('G3', 4)],
    [('A2', 0), ('E3', 4)],
    [('F2', 0), ('C3', 4)],
    [('G2', 0), ('D3', 4)],
]

# 每小节和声垫（小提琴 II / 中提琴）与低音根音（拨弦 + 定音鼓）
CHORDS = [
    (['C4', 'E4', 'G4'], 'C2'),
    (['D4', 'G4', 'B4'], 'G2'),
    (['A3', 'C4', 'E4'], 'A2'),
    (['F3', 'A3', 'C4'], 'F2'),
    (['C4', 'E4', 'G4'], 'C2'),
    (['A3', 'C4', 'E4'], 'A2'),
    (['F3', 'A3', 'C4'], 'F2'),
    (['D4', 'G4', 'B4'], 'G2'),
]

n = int(SR * DURATION)
buf = [0.0] * n


def _add(i, v):
    if 0 <= i < n:
        buf[i] += v


def add_violin(start, freq, dur, amp):
    """小提琴：明亮丰富泛音，快速揉弦，适中起音（弓弦渐入）。"""
    length = int(SR * min(dur, DURATION - start / SR))
    if length <= 0:
        return
    vib_rate, vib_depth = 6.5, 0.010
    harm = (1.0, 0.78, 0.62, 0.48, 0.36, 0.25, 0.16, 0.10)
    for j in range(length):
        t = j / SR
        vib = 1.0 + vib_depth * math.sin(2 * math.pi * vib_rate * t)
        phase = 2 * math.pi * freq * vib * t
        env = min(1.0, t / 0.11) * min(1.0, (dur - t) / 0.09)
        env = max(0.0, env) * math.exp(-t * 0.55)
        v = 0.0
        for h, w in enumerate(harm, start=1):
            v += w * math.sin(phase * h)
        _add(int(start * SR) + j, v * env * amp / 3.6)


def add_cello(start, freq, dur, amp):
    """大提琴：低音区温暖音色，慢揉弦，泛音较少，起音更缓。"""
    length = int(SR * min(dur, DURATION - start / SR))
    if length <= 0:
        return
    vib_rate, vib_depth = 4.8, 0.013
    harm = (1.0, 0.52, 0.30, 0.16, 0.08, 0.04)
    for j in range(length):
        t = j / SR
        vib = 1.0 + vib_depth * math.sin(2 * math.pi * vib_rate * t)
        phase = 2 * math.pi * freq * vib * t
        env = min(1.0, t / 0.20) * min(1.0, (dur - t) / 0.16)
        env = max(0.0, env)
        v = 0.0
        for h, w in enumerate(harm, start=1):
            v += w * math.sin(phase * h)
        _add(int(start * SR) + j, v * env * amp / 2.1)


def add_pad(start, freq, dur, amp):
    """小提琴 II / 中提琴：柔和和声长音，弱揉弦铺底。"""
    length = int(SR * min(dur, DURATION - start / SR))
    if length <= 0:
        return
    for j in range(length):
        t = j / SR
        vib = 1.0 + 0.006 * math.sin(2 * math.pi * 5.8 * t)
        ph = 2 * math.pi * freq * vib * t
        env = min(1.0, t / 0.15) * min(1.0, (dur - t) / 0.20)
        env = max(0.0, env)
        v = math.sin(ph) + 0.28 * math.sin(2 * ph) + 0.10 * math.sin(3 * ph)
        _add(int(start * SR) + j, v * env * amp / 1.4)


def add_pizz(start, freq, amp):
    """拨弦 pizzicato：极快衰减的基音 + 泛音，低音节奏。"""
    length = int(SR * 0.42)
    for j in range(length):
        t = j / SR
        env = math.exp(-t * 9.0)
        ph = 2 * math.pi * freq * t
        v = math.sin(ph) + 0.35 * math.sin(2 * ph) + 0.12 * math.sin(3 * ph)
        _add(int(start * SR) + j, v * env * amp)


def add_perc(start, amp, kind):
    """打击：定音鼓（有音高的低鼓）、军鼓、小镲。"""
    length = int(SR * (0.6 if kind == 'timp' else 0.22))
    for j in range(length):
        t = j / SR
        if kind == 'timp':
            f = 68 * math.exp(-t * 16) + 52
            v = math.sin(2 * math.pi * f * t) * math.exp(-t * 5) + \
                0.08 * random.uniform(-1, 1) * math.exp(-t * 20)
        elif kind == 'snare':
            body = math.sin(2 * math.pi * 185 * t) * math.exp(-t * 20)
            white = random.uniform(-1, 1)
            v = (white * 0.55 + body * 0.45) * math.exp(-t * 16)
        else:  # cymbal
            v = 0.0
            for m in (1.0, 1.41, 1.87, 2.43, 3.09):
                v += math.sin(2 * math.pi * 4300 * m * t) * 0.19
            v *= math.exp(-t * 19)
            v += 0.3 * random.uniform(-1, 1) * math.exp(-t * 28)
        _add(int(start * SR) + j, v * amp)


bar_index = 0
t = 0.0
while t < DURATION - BAR:
    bar_start = t
    melody = MELODY[bar_index % len(MELODY)]
    cello = CELLO[bar_index % len(CELLO)]
    chord_notes, bass_root = CHORDS[bar_index % len(CHORDS)]

    # 和声垫：整小节柔和铺底（小提琴 II + 中提琴）
    for note in chord_notes:
        add_pad(bar_start, N[note], BAR * 0.95, 0.055)

    # 大提琴低音旋律：2 个长音铺满小节
    for note, offset in cello:
        add_cello(bar_start + offset * BEAT / 2, N[note], BEAT * 2.1, 0.14)

    # 拨弦低音：每拍根音，2/4 拍加五度
    for b in range(4):
        amp = 0.15 if b in (0, 2) else 0.08
        add_pizz(bar_start + b * BEAT, N[bass_root], amp)

    # 小提琴主旋律：8 个八分音符
    for k, note in enumerate(melody):
        if note != '_' and note in N:
            add_violin(bar_start + k * BEAT / 2, N[note], 0.35, 0.155)

    # 打击：定音鼓 1 拍、军鼓 2/4 拍、小镲八分音符
    add_perc(bar_start, 0.36, 'timp')
    for b in (1, 3):
        add_perc(bar_start + b * BEAT, 0.20, 'snare')
    for k in range(8):
        add_perc(bar_start + k * BEAT / 2, 0.026, 'cymbal')

    t += BAR
    bar_index += 1

# 归一化 + 首尾淡入淡出
peak = max(abs(x) for x in buf) or 1.0
scale = 0.55 / peak
samples = []
for i, x in enumerate(buf):
    tt = i / SR
    fade = max(0.0, min(1.0, tt / FADE, (DURATION - tt) / FADE))
    samples.append(int(max(-1, min(1, x * scale * fade)) * 32767))

with wave.open(str(OUT), "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(struct.pack(f"<{len(samples)}h", *samples))

print(f"wrote {OUT} ({DURATION}s, BPM={BPM}, C-major strings, {OUT.stat().st_size / 1024 / 1024:.1f} MB)")

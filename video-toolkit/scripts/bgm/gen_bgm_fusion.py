#!/usr/bin/env python3
"""原创合成：中国民乐 × 激昂进行曲 BGM（BPM 126，C 宫五声音阶）。

参考 pawpatrol-script3/out/参考_汪汪队主题曲_第三方完整版.mp3 的
气质骨架（BPM≈126、全程高能量、主题曲循环结构），但旋律、节奏动机、
和声走向完全原创，不复制、不变调、不采样任何在保作品。

编制（纯器乐，无人声）：
  - 唢呐：号角式主旋律，明亮双簧片音色 + 揉音 + 起音滑音
  - 二胡：抒情对位声部，弓弦揉弦（vibrato）+ 滑音
  - 琵琶式拨弦：低音根音 + 五度
  - 中国打击：大鼓、堂鼓、小镲，进行曲强弱规律
首尾各 2.5 秒淡入淡出；实际混音音量由 Remotion 侧控制在 12%。
完全原创合成，无版权顾虑。
"""
import math
import random
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "audio" / "bgm-fusion.wav"
OUT.parent.mkdir(parents=True, exist_ok=True)

SR = 22050
BPM = 126
BEAT = 60.0 / BPM          # 0.4762s
BAR = BEAT * 4             # 1.9048s
DURATION = 96.0            # 循环足够覆盖成片
FADE = 2.5
random.seed(4262026)

# C 宫五声音阶：宫 C / 商 D / 角 E / 徵 G / 羽 A
N = {
    'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'G3': 196.00, 'A3': 220.00,
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'G4': 392.00, 'A4': 440.00,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'G5': 783.99, 'A5': 880.00,
    'C6': 1046.50, 'D6': 1174.66,
}

# 8 小节原创主旋律（唢呐，每小节 8 个八分音符，'_' 休止）
# 动机：C-G-E-G 起势 → 上行推进 → 八度号角 → 五声收束
MELODY = [
    ['G4', 'C5', 'E5', 'G5', 'E5', 'C5', 'G4', '_'],   # 宫 起势
    ['A4', 'D5', 'G5', 'A5', 'G5', 'D5', 'A4', '_'],   # 羽 回应
    ['E5', 'G5', 'A5', 'C6', 'A5', 'G5', 'E5', 'D5'],  # 角 推进
    ['C5', '_', 'G5', '_', 'C6', '_', '_', '_'],        # 宫 号角收束
    ['D5', 'E5', 'G5', 'A5', 'G5', 'E5', 'D5', 'C5'],  # 商 再起
    ['A4', 'C5', 'D5', 'E5', 'D5', 'C5', 'A4', '_'],   # 羽 抒情
    ['G4', 'A4', 'C5', 'D5', 'E5', 'G5', 'A5', 'C6'],  # 徵 全音阶上行
    ['G5', '_', 'E5', '_', 'C5', '_', '_', '_'],        # 徵→宫 收束
]

# 二胡对位：每小节 2 个长音（跨小节连贯），与唢呐形成呼应
COUNTER = [
    [('C4', 0), ('G4', 4)],
    [('D4', 0), ('A4', 4)],
    [('E4', 0), ('C5', 4)],
    [('G4', 0), ('E4', 4)],
    [('A3', 0), ('E4', 4)],
    [('C4', 0), ('G4', 4)],
    [('D4', 0), ('A4', 4)],
    [('G3', 0), ('C4', 4)],
]

# 每小节低音根音（拨弦）与和声五度
BASS_ROOT = ['C3', 'D3', 'E3', 'C3', 'A3', 'C3', 'D3', 'G3']
FIFTH = ['G3', 'A3', 'B3', 'G3', 'E3', 'G3', 'A3', 'D3']
# 注：B3 不在五声音阶内，第 3 小节改用 D3 保持纯五声风味
FIFTH[2] = 'D3'

n = int(SR * DURATION)
buf = [0.0] * n


def _add(i, v):
    if 0 <= i < n:
        buf[i] += v


def add_suona(start, freq, dur, amp):
    """唢呐：双簧片明亮音色，强泛音 + 揉音，起音短滑音。"""
    length = int(SR * min(dur, DURATION - start / SR))
    if length <= 0:
        return
    vib_rate, vib_depth = 5.5, 0.012
    harm = (1.0, 0.72, 0.52, 0.38, 0.26, 0.17, 0.10)
    for j in range(length):
        t = j / SR
        # 起音 40ms 从下方大二度滑入（唢呐演奏特征）
        bend = 1.0 - 0.11 * math.exp(-t * 70)
        vib = 1.0 + vib_depth * math.sin(2 * math.pi * vib_rate * t)
        phase = 2 * math.pi * freq * bend * vib * t
        env = min(1.0, t / 0.008) * min(1.0, (dur - t) / 0.05)
        env = max(0.0, env) * math.exp(-t * 0.9)
        v = 0.0
        for h, w in enumerate(harm, start=1):
            v += w * math.sin(phase * h)
        _add(int(start * SR) + j, v * env * amp / 3.1)


def add_erhu(start, freq, dur, amp):
    """二胡：弓弦柔和音色，揉弦（vibrato）+ 起音滑音，连绵不断。"""
    length = int(SR * min(dur, DURATION - start / SR))
    if length <= 0:
        return
    vib_rate, vib_depth = 5.0, 0.010
    harm = (1.0, 0.34, 0.16, 0.07)
    for j in range(length):
        t = j / SR
        # 起音 90ms 从下方小二度滑入（二胡滑音）
        bend = 1.0 - 0.055 * math.exp(-t * 38)
        vib = 1.0 + vib_depth * math.sin(2 * math.pi * vib_rate * t)
        phase = 2 * math.pi * freq * bend * vib * t
        env = min(1.0, t / 0.09) * min(1.0, (dur - t) / 0.12)
        env = max(0.0, env)
        v = 0.0
        for h, w in enumerate(harm, start=1):
            v += w * math.sin(phase * h)
        _add(int(start * SR) + j, v * env * amp / 1.6)


def add_pluck(start, freq, amp):
    """琵琶式拨弦：快速衰减的基音 + 泛音，用于低音根音。"""
    length = int(SR * 0.55)
    for j in range(length):
        t = j / SR
        env = math.exp(-t * 6.5)
        ph = 2 * math.pi * freq * t
        v = math.sin(ph) + 0.32 * math.sin(2 * ph) + 0.12 * math.sin(3 * ph)
        _add(int(start * SR) + j, v * env * amp)


def add_drum(start, amp, kind):
    """中国打击：大鼓/堂鼓（低频鼓皮）、小镲（金属高频）。"""
    length = int(SR * (0.5 if kind in ('big', 'hall') else 0.22))
    for j in range(length):
        t = j / SR
        if kind == 'big':
            f = 78 * math.exp(-t * 22) + 48
            v = math.sin(2 * math.pi * f * t) * math.exp(-t * 7) + \
                0.12 * random.uniform(-1, 1) * math.exp(-t * 26)
        elif kind == 'hall':
            f = 150 * math.exp(-t * 34) + 95
            v = math.sin(2 * math.pi * f * t) * math.exp(-t * 15) + \
                0.2 * random.uniform(-1, 1) * math.exp(-t * 40)
        else:  # cymbal 小镲
            # 多个不谐和正弦模拟金属，高通噪声
            v = 0.0
            for m in (1.0, 1.42, 1.83, 2.37, 3.11):
                v += math.sin(2 * math.pi * 4200 * m * t) * 0.2
            v *= math.exp(-t * 20)
            v += 0.35 * random.uniform(-1, 1) * math.exp(-t * 30)
        _add(int(start * SR) + j, v * amp)


bar_index = 0
t = 0.0
while t < DURATION - BAR:
    bar_start = t
    melody = MELODY[bar_index % len(MELODY)]
    root = BASS_ROOT[bar_index % len(BASS_ROOT)]
    fifth = FIFTH[bar_index % len(FIFTH)]
    counter = COUNTER[bar_index % len(COUNTER)]

    # 二胡对位：2 个长音铺满整小节，连绵抒情
    for note, offset in counter:
        add_erhu(bar_start + offset * BEAT / 2, N[note], BEAT * 2.1, 0.10)

    # 低音拨弦：每拍根音，2/4 拍加五度（进行曲强弱）
    for b in range(4):
        amp = 0.16 if b in (0, 2) else 0.09
        add_pluck(bar_start + b * BEAT, N[root], amp)
        if b in (1, 3):
            add_pluck(bar_start + b * BEAT, N[fifth], 0.07)

    # 唢呐主旋律：8 个八分音符
    for k, note in enumerate(melody):
        if note != '_' and note in N:
            add_suona(bar_start + k * BEAT / 2, N[note], 0.36, 0.15)

    # 打击：大鼓 1 拍、堂鼓 2/4 拍、小镲八分音符点缀
    add_drum(bar_start, 0.34, 'big')
    for b in (1, 3):
        add_drum(bar_start + b * BEAT, 0.22, 'hall')
    for k in range(8):
        add_drum(bar_start + k * BEAT / 2, 0.028, 'cymbal')

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

print(f"wrote {OUT} ({DURATION}s, BPM={BPM}, C-pentatonic, {OUT.stat().st_size / 1024 / 1024:.1f} MB)")

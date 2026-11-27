#!/usr/bin/env python3
"""原创合成：抓耳式儿童英雄主题曲 BGM（BPM 126，C 大调）。

参考 pawpatrol-script3/out/参考_汪汪队主题曲_第三方完整版.mp3 的
气质骨架：开头短促的"呼喊式"节奏动机（短短长×2）、随后全程高能量、
主题曲式循环。旋律、动机音高、和声走向完全原创，不复制、不变调、
不采样任何在保作品——只借鉴"呼喊节奏 + 大调 + 进行曲"的通用风格。

为什么这次更好听：
  - 呼喊动机：八分-八分-四分（"短短长"），是儿童主题曲最抓耳的节奏
  - 歌唱旋律：以级进为主、小跳为辅，音域控制在一个八度内，好记好唱
  - 明亮音色：方波号角（奇次谐波，温暖不刺耳）+ 三角波主旋律 + 木琴点缀
  - 明确和声：I-V-vi-IV 经典进行，稳定又昂扬
  - 进行曲鼓点：底鼓 1/3 拍、军鼓 2/4 拍，全程推动力

编制（纯器乐，无人声采样）：号角 call、三角波 lead、木琴、弦乐垫、拨弦低音、鼓组。
首尾 2.5 秒淡入淡出；实际混音音量由 Remotion 侧控制在 12%。
"""
import math
import random
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "audio" / "bgm-catchy.wav"
OUT.parent.mkdir(parents=True, exist_ok=True)

SR = 22050
BPM = 126
BEAT = 60.0 / BPM          # 0.4762s
EIGHTH = BEAT / 2
BAR = BEAT * 4
DURATION = 96.0
FADE = 2.5
random.seed(11262026)

N = {
    'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61, 'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46, 'G5': 783.99, 'A5': 880.00, 'B5': 987.77,
    'C6': 1046.50,
}

# ============================================================
# 8 小节主题：呼喊动机 + 歌唱旋律（每小节 8 个八分音符网格）
# ============================================================
# 动机"短短长"：G4 G4 C5 _  → 像 "Paw-Patrol!" 的呼号节奏
# 主旋律以级进为主：C-D-E-G-E-D-C，唱起来顺口
CALL = [
    ['G4', 'G4', 'C5', '_', 'G4', 'G4', 'C5', '_'],   # 呼喊动机
    ['E5', 'E5', 'C5', '_', 'G4', 'G4', 'C5', '_'],   # 呼喊变奏
]
VERSE = [
    ['C5', 'D5', 'E5', 'G5', 'E5', 'D5', 'C5', '_'],  # 级进上行再回落
    ['D5', 'E5', 'F5', 'A5', 'F5', 'E5', 'D5', '_'],  # 模进
    ['E5', 'F5', 'G5', 'C6', 'G5', 'F5', 'E5', '_'],  # 推向高潮
    ['D5', 'C5', 'D5', 'E5', 'D5', 'C5', 'G4', '_'],  # 回落收束
]
BRIDGE = [
    ['G4', 'G4', 'C5', '_', 'G4', 'G4', 'C5', '_'],   # 呼喊再现
    ['E5', 'E5', 'C5', '_', 'C5', '_', '_', '_'],      # 收尾
]
PATTERN = CALL + VERSE + BRIDGE   # 8 小节

# 和声进行：I - I - ii - IV - vi - IV - V - I（稳定又昂扬）
CHORDS = [
    (['C4', 'E4', 'G4'], 'C3'),    # I
    (['C4', 'E4', 'G4'], 'C3'),    # I
    (['D4', 'F4', 'A4'], 'D3'),    # ii
    (['F4', 'A4', 'C5'], 'F3'),    # IV
    (['A3', 'C4', 'E4'], 'A3'),    # vi
    (['F4', 'A4', 'C5'], 'F3'),    # IV
    (['G4', 'B4', 'D5'], 'G3'),    # V
    (['C4', 'E4', 'G4'], 'C3'),    # I
]

n = int(SR * DURATION)
buf = [0.0] * n


def _add(i, v):
    if 0 <= i < n:
        buf[i] += v


def add_horn(start, freq, dur, amp):
    """号角/呼喊：方波（奇次谐波，明亮温暖），短促有力，轻微起音滑音。"""
    length = int(SR * min(dur, DURATION - start / SR))
    if length <= 0:
        return
    for j in range(length):
        t = j / SR
        bend = 1.0 - 0.04 * math.exp(-t * 60)
        ph = 2 * math.pi * freq * bend * t
        env = min(1.0, t / 0.006) * min(1.0, (dur - t) / 0.04)
        env = max(0.0, env) * math.exp(-t * 1.2)
        # 方波 = 奇次谐波叠加（1 + 1/3 + 1/5 + 1/7），温暖不刺耳
        v = (math.sin(ph) + 0.33 * math.sin(3 * ph) +
             0.20 * math.sin(5 * ph) + 0.12 * math.sin(7 * ph))
        _add(int(start * SR) + j, v * env * amp / 1.7)


def add_lead(start, freq, dur, amp):
    """主旋律：三角波（柔和歌唱性）+ 二次谐波，轻微揉音。"""
    length = int(SR * min(dur, DURATION - start / SR))
    if length <= 0:
        return
    for j in range(length):
        t = j / SR
        vib = 1.0 + 0.007 * math.sin(2 * math.pi * 5.5 * t)
        ph = 2 * math.pi * freq * vib * t
        env = min(1.0, t / 0.02) * min(1.0, (dur - t) / 0.05)
        env = max(0.0, env) * math.exp(-t * 0.9)
        # 三角波 = 奇次谐波 / 奇数平方，柔和
        v = (math.sin(ph) - 0.11 * math.sin(3 * ph) +
             0.04 * math.sin(5 * ph) + 0.22 * math.sin(2 * ph))
        _add(int(start * SR) + j, v * env * amp / 1.2)


def add_bell(start, freq, amp):
    """木琴/钟琴：纯正弦 + 高八度泛音，快速衰减，儿童感点缀。"""
    length = int(SR * 0.5)
    for j in range(length):
        t = j / SR
        env = math.exp(-t * 8.0)
        ph = 2 * math.pi * freq * t
        v = math.sin(ph) + 0.30 * math.sin(2 * ph) + 0.10 * math.sin(4.2 * ph)
        _add(int(start * SR) + j, v * env * amp)


def add_pad(start, freq, dur, amp):
    """弦乐垫：柔和铺底，弱揉音。"""
    length = int(SR * min(dur, DURATION - start / SR))
    if length <= 0:
        return
    for j in range(length):
        t = j / SR
        vib = 1.0 + 0.005 * math.sin(2 * math.pi * 5.0 * t)
        ph = 2 * math.pi * freq * vib * t
        env = min(1.0, t / 0.12) * min(1.0, (dur - t) / 0.18)
        env = max(0.0, env)
        v = math.sin(ph) + 0.24 * math.sin(2 * ph)
        _add(int(start * SR) + j, v * env * amp / 1.3)


def add_bass(start, freq, amp):
    """拨弦低音：基音 + 泛音，快速衰减。"""
    length = int(SR * 0.5)
    for j in range(length):
        t = j / SR
        env = math.exp(-t * 7.0)
        ph = 2 * math.pi * freq * t
        v = math.sin(ph) + 0.28 * math.sin(2 * ph)
        _add(int(start * SR) + j, v * env * amp)


def add_drum(start, amp, kind):
    """鼓组：底鼓、军鼓、hi-hat。"""
    length = int(SR * (0.4 if kind == 'kick' else 0.18))
    for j in range(length):
        t = j / SR
        if kind == 'kick':
            f = 120 * math.exp(-t * 25) + 48
            v = math.sin(2 * math.pi * f * t) * math.exp(-t * 10)
        elif kind == 'snare':
            body = math.sin(2 * math.pi * 200 * t) * math.exp(-t * 20)
            v = (random.uniform(-1, 1) * 0.6 + body * 0.5) * math.exp(-t * 16)
        else:
            v = (random.uniform(-1, 1) - (0 if j == 0 else buf[int(start * SR) + j - 1])) * math.exp(-t * 90)
        _add(int(start * SR) + j, v * amp)


bar_index = 0
t = 0.0
while t < DURATION - BAR:
    bar_start = t
    melody = PATTERN[bar_index % len(PATTERN)]
    chord_notes, bass_root = CHORDS[bar_index % len(CHORDS)]
    is_call = bar_index % 8 in (0, 1, 6, 7)   # 呼喊小节

    # 和声垫整小节
    for note in chord_notes:
        add_pad(bar_start, N[note], BAR * 0.95, 0.045)

    # 拨弦低音每拍，1/3 拍加重
    for b in range(4):
        add_bass(bar_start + b * BEAT, N[bass_root], 0.16 if b in (0, 2) else 0.09)

    # 主旋律：呼喊小节用号角（更亮），其余用三角波 lead（歌唱性）
    for k, note in enumerate(melody):
        if note == '_':
            continue
        if is_call:
            add_horn(bar_start + k * EIGHTH, N[note], 0.30, 0.19)
        else:
            add_lead(bar_start + k * EIGHTH, N[note], 0.32, 0.18)

    # 木琴：在长音位置（第 3 个八分）加高八度点缀
    if melody[2] != '_':
        add_bell(bar_start + 2 * EIGHTH, N[melody[2]] * 2, 0.055)

    # 鼓：底鼓 1/3、军鼓 2/4、hi-hat 八分
    add_drum(bar_start, 0.32, 'kick')
    add_drum(bar_start + 2 * BEAT, 0.28, 'kick')
    for b in (1, 3):
        add_drum(bar_start + b * BEAT, 0.22, 'snare')
    for k in range(8):
        add_drum(bar_start + k * EIGHTH, 0.02, 'hat')

    t += BAR
    bar_index += 1

# 归一化 + 淡入淡出
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

print(f"wrote {OUT} ({DURATION}s, BPM={BPM}, C-major catchy, {OUT.stat().st_size / 1024 / 1024:.1f} MB)")

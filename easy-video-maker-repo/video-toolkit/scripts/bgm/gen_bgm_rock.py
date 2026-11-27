#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
原创「儿童摇滚进行曲」BGM —— 参考曲风格 DNA 驱动，旋律完全原创。

参考曲分析得到的风格指纹（只取风格参数，不复制旋律/和声/节奏、不采样任何音频）：
  - BPM ≈ 126（自相关双峰 125/128）
  - 大调色彩（chroma 大调相关 +0.259，小调 -0.274）
  - 失真电吉他摇滚编制（chroma 近似均匀 + 大量 ±12/±24 八度泛音 = 宽频过载吉他）
  - 密集 onset（间隔 0.15-0.33s = 八分/十六分音符驱动）
  - 全程高能量、主题曲式 A-A'-B-A' 循环
  - 开头「呼喊式」短促动机（强-弱-强）

原创设计：
  - 全新旋律（级进 + 重复 + 呼应，好记但不抄原曲任何音型）
  - 全新和声走向（I-V-vi-IV 流行进行）
  - 全新节奏动机进行曲化
  - 编制：过载电吉他 power chord + 原声/电子鼓 + 贝斯 + 明亮号角 lead

纯 numpy/scipy 合成，输出 16bit PCM WAV。运行 0 token。
"""
import numpy as np
import wave
from scipy.signal import butter, sosfilt

SR = 44100
DUR = 96.0
BPM = 126.0
BEAT = 60.0 / BPM          # 一拍秒数
BAR = BEAT * 4             # 一小节
rng = np.random.default_rng(20261126)

# ---------- 音名 ----------
def hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)

def rnd(n):
    return rng.standard_normal(n)

# ---------- 基础波形 ----------
def phase(freq, dur, vib_hz=0, vib_depth=0):
    n = np.arange(int(dur * SR))
    t = n / SR
    if vib_hz:
        f = freq * (1 + vib_depth * np.sin(2 * np.pi * vib_hz * t))
        return 2 * np.pi * np.cumsum(f) / SR
    return 2 * np.pi * freq * t

def adsr(n, a=0.01, d=0.12, s=0.7, r=0.15):
    total = n
    a_n = int(a * SR); d_n = int(d * SR); r_n = int(r * SR)
    env = np.ones(total)
    if a_n:
        env[:a_n] = np.linspace(0, 1, a_n)
    if d_n:
        env[a_n:a_n+d_n] = np.linspace(1, s, d_n)
    if r_n:
        env[-r_n:] = env[-r_n:] * np.linspace(1, 0, r_n)
    return env

# ---------- 乐器 ----------
def overdrive(x, drive=8, mix=0.7):
    """波形整形过载：tanh 软削波 + 直流补偿，模拟电子管失真"""
    dr = np.tanh(drive * x) / np.tanh(drive)
    return (1 - mix) * x + mix * dr

def guitar_power(midi, dur, gain=0.5, drive=9):
    """失真电吉他强力和弦（根音 + 纯五度）：摇滚骨架"""
    f = hz(midi)
    ph = phase(f, dur)
    # 根音 + 五度 + 微失谐厚度
    raw = (np.sin(ph) + 0.7 * np.sin(ph * 1.5) + 0.35 * np.sin(ph * 2)
           + 0.15 * rnd(len(ph)))
    od = overdrive(raw, drive, 0.72)
    od = od / (np.abs(od).max() + 1e-9)
    env = adsr(len(od), a=0.004, d=0.05, s=0.85, r=min(0.12, dur*0.3))
    # 低通去掉部分毛刺
    sos = butter(2, 5200, btype='low', fs=SR, output='sos')
    return sosfilt(sos, od) * env * gain

def guitar_chord(midis, dur, gain=0.42):
    """大和弦扫弦：多个音错开 8ms 依次触发（strum）"""
    out = np.zeros(int(dur * SR))
    for i, m in enumerate(midis):
        seg = guitar_power(m, dur, gain=gain/len(midis)*1.7, drive=6)
        off = int(i * 0.008 * SR)
        out[off:off+len(seg)] += seg[:max(0, len(out)-off)]
    return out

def bass(midi, dur, gain=0.55):
    """贝斯：正弦 + 方波混合，稳定低音"""
    f = hz(midi)
    ph = phase(f, dur)
    raw = 0.6*np.sin(ph) + 0.4*np.sign(np.sin(ph))
    sos = butter(2, 400, btype='low', fs=SR, output='sos')
    y = sosfilt(sos, raw)
    env = adsr(len(y), a=0.006, d=0.04, s=0.9, r=min(0.1, dur*0.25))
    return y * env * gain

def lead(midi, dur, gain=0.42, bright=True):
    """明亮号角 lead：奇次谐波方波 + 轻微颤音，儿童主题曲主旋律音色"""
    f = hz(midi)
    ph = phase(f, dur, vib_hz=5.5, vib_depth=0.006)
    x = np.sign(np.sin(ph)) * 0.55 + np.sin(ph) * 0.25 + np.sin(ph*2) * 0.2
    if bright:
        x += np.sin(ph*3) * 0.1
    env = adsr(len(x), a=0.012, d=0.06, s=0.82, r=min(0.14, dur*0.3))
    sos = butter(2, 6500, btype='low', fs=SR, output='sos')
    return sosfilt(sos, x) * env * gain

def kick(gain=0.9):
    """底鼓：正弦频率快速下扫 130→45Hz"""
    dur = 0.32
    ph = phase(1, dur)
    t = np.arange(len(ph)) / SR
    f = 45 + 95 * np.exp(-t * 22)
    y = np.sin(2*np.pi*np.cumsum(f)/SR)
    return y * np.exp(-t * 11) * gain

def snare(gain=0.55):
    """军鼓：噪声 + 180Hz 鼓皮音"""
    dur = 0.22
    n = int(dur*SR); t = np.arange(n)/SR
    noise = rnd(n)
    sos = butter(2, [1200, 9000], btype='band', fs=SR, output='sos')
    body = np.sin(2*np.pi*180*t) * 0.35
    y = sosfilt(sos, noise) * 0.8 + body
    return y * np.exp(-t * 16) * gain

def hat(gain=0.22, open_hat=False):
    """踩镲/开镲：高通噪声"""
    dur = 0.16 if open_hat else 0.055
    n = int(dur*SR); t = np.arange(n)/SR
    sos = butter(2, 7000, btype='high', fs=SR, output='sos')
    y = sosfilt(sos, rnd(n))
    return y * np.exp(-t * (14 if open_hat else 55)) * gain

def clap(gain=0.4):
    """拍手：三次短噪声脉冲"""
    dur = 0.2; n = int(dur*SR); t = np.arange(n)/SR
    y = np.zeros(n)
    for off in [0, 0.012, 0.024]:
        i = int(off*SR)
        seg = rnd(n-i) * np.exp(-np.arange(n-i)/SR * 45)
        y[i:i+len(seg)] += seg
    sos = butter(2, [1000, 6000], btype='band', fs=SR, output='sos')
    return sosfilt(sos, y) * gain

# ---------- 原创旋律与和声 ----------
# 大调 I-V-vi-IV 进行（全新，非参考曲和声）
# 用 C 大调：C=48 G=43 Am=45 F=41
PROG = [48, 43, 45, 41]  # 每和弦持续 1 小节

# 原创 hook 旋律（MIDI 音高，相对小节起点的拍位与时长）
# 设计原则：级进为主 + 重复 + 响应，一个八度内，朗朗上口
# 8 小节主题：呼喊动机 → 级进上行 → 呼应下行 → 落主音
HOOK = [
    # (小节内拍位置, MIDI, 时长拍数)
    [(0, 72, 0.5), (0.5, 72, 0.5), (1.0, 76, 1.5), (2.5, 76, 0.5), (3.0, 79, 1.0)],  # G G C C E (呼应"短短长")
    [(0, 77, 1.0), (1.0, 76, 0.5), (1.5, 74, 0.5), (2.0, 72, 2.0)],                    # 级进下行
    [(0, 72, 0.5), (0.5, 74, 0.5), (1.0, 76, 1.0), (2.0, 76, 0.5), (2.5, 74, 0.5), (3.0, 72, 1.0)],
    [(0, 71, 1.0), (1.0, 72, 1.0), (2.0, 74, 2.0)],                                     # 落 ii 再解决
    [(0, 76, 0.5), (0.5, 76, 0.5), (1.0, 79, 1.5), (2.5, 77, 0.5), (3.0, 76, 1.0)],    # A' 变奏
    [(0, 74, 1.0), (1.0, 72, 0.5), (1.5, 71, 0.5), (2.0, 69, 2.0)],
    [(0, 72, 0.5), (0.5, 74, 0.5), (1.0, 76, 0.5), (1.5, 77, 0.5), (2.0, 79, 2.0)],
    [(0, 76, 1.0), (1.0, 72, 1.0), (2.0, 72, 2.0)],                                     # 落主音
]

# 结构：8 小节主题 × 多次，中段加变化（A-A'-B-A'）
SECTIONS = [
    ("A", 1.0), ("A", 1.05), ("B", 0.9), ("A", 1.1),
]

# ---------- 混音 ----------
N = int(DUR * SR)
mix = np.zeros(N)

def place(sig, start_s, gain=1.0):
    i = int(start_s * SR)
    if i >= N:
        return
    seg = sig * gain
    j = min(N, i + len(seg))
    mix[i:j] += seg[:j-i]

# 主题总时长
THEME_LEN = len(HOOK) * BAR

for si, (sec_type, energy) in enumerate(SECTIONS):
    base = si * THEME_LEN
    for bar in range(len(HOOK)):
        bt = base + bar * BAR
        root = PROG[bar % len(PROG)]
        # 和弦音（大三和弦）
        maj3 = root + 4
        fifth = root + 7
        # --- 鼓组：进行曲式 kick-snare 驱动 + 八分踩镲 ---
        for b in range(4):
            t = bt + b * BEAT
            place(kick(0.9 * energy), t)
            if b in (1, 3):
                place(snare(0.5 * energy), t)
                place(clap(0.28 * energy), t)
            place(hat(0.2 * energy), t)
            place(hat(0.13 * energy), t + BEAT/2, )
        # 小节末开镲 fill
        if bar % 4 == 3:
            place(hat(0.18, open_hat=True), bt + 3.5*BEAT)
        # --- 贝斯：根音-五度交替（八分驱动）---
        for b in range(8):
            note_m = root - 12 if b % 2 == 0 else fifth - 12
            place(bass(note_m, BEAT*0.48, 0.5 * energy), bt + b * BEAT/2)
        # --- 吉他：强力和弦 + 和弦扫弦（八分切分）---
        for b in range(8):
            g = guitar_power(root, BEAT*0.46, 0.34 * energy, drive=9)
            place(g, bt + b * BEAT/2)
        # 每小节前两拍加扫弦厚度
        place(guitar_chord([root+12, maj3+12, fifth+12], BEAT*1.6, 0.16 * energy), bt)
        # --- 主旋律 lead ---
        for pos, midi, nb in HOOK[bar]:
            # B 段：旋律降八度、减能量，做对比
            m = midi - 12 if sec_type == "B" else midi
            g = 0.34 * energy if sec_type != "B" else 0.26
            place(lead(m, nb * BEAT * 0.92, g), bt + pos * BEAT)

# ---------- 开头呼喊动机（短短长，模拟主题曲开头抓耳点）----------
# 完全原创音高型：G-G-C 上行呼喊（非参考曲音高）
for rep in range(2):
    st = rep * BAR
    for pos, midi, nb in [(0, 67, 0.5), (0.5, 67, 0.5), (1.0, 72, 1.5)]:
        place(lead(midi, nb*BEAT*0.9, 0.38), st + pos*BEAT)
    place(kick(0.9), st)
    place(snare(0.5), st + BEAT)
    place(guitar_power(48, BEAT*1.8, 0.3), st)

# ---------- 后处理：淡入淡出 + 限幅 ----------
fade = int(2.5 * SR)
mix[:fade] *= np.linspace(0, 1, fade)
mix[-fade:] *= np.linspace(1, 0, fade)

peak = np.abs(mix).max()
target = 0.86
mix = mix / peak * target
pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)

out = 'public/audio/bgm-rock.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

clip = int((np.abs(pcm) >= 32760).sum())
rms = float(np.sqrt(np.mean(mix**2)))
print(f'WROTE {out}  dur={DUR}s  peak={int(np.abs(pcm).max())}  rms={rms:.4f}  clip={clip}')

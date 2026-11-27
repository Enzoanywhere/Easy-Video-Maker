#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
原创 BGM v2 —— 旋律/节奏动机按参考曲 HPSS+YIN 提取的真实唱腔重塑。

风格 DNA 来源（声学分析提取，仅风格参数，不采样任何音频）：
  - 主旋律轮廓: A#4 A3 D5 D4 C4 C#4 D4 B3 B4 B3 E3 C4 D4
  - 音域 A3~D5，中位 C4；含 B/C#/D → 偏 D 多利亚/D 小调色彩
  - 呼喊节奏: 长-短短 (0.33/0.15/0.16) 后接稳定 0.31-0.33s 八分驱动
  - BPM ≈ 126，全程高能量，失真电吉他摇滚编制

原创处理：旋律音高型重新组织成可唱的 8 小节 hook（保留提取的轮廓走向特征：
中位 C4 起步→级进上行 D5→回落 B3→再扬 B4→落 D4），和声用 Dm-Bb-F-C，
节奏动机与配器重组。非逐音符复制。
"""
import numpy as np
import wave
from scipy.signal import butter, sosfilt

SR=44100; DUR=96.0; BPM=126.0; BEAT=60/BPM; BAR=BEAT*4
rng=np.random.default_rng(20261127)

def hz(m): return 440.0*2.0**((m-69)/12.0)
def rnd(n): return rng.standard_normal(n)
def phase(f,dur,vib=0,dep=0):
    n=np.arange(int(dur*SR)); t=n/SR
    if vib: return 2*np.pi*np.cumsum(f*(1+dep*np.sin(2*np.pi*vib*t)))/SR
    return 2*np.pi*f*t
def adsr(n,a=0.01,d=0.1,s=0.75,r=0.12):
    env=np.ones(n); an=int(a*SR); dn=int(d*SR); rn=int(r*SR)
    if an: env[:an]=np.linspace(0,1,an)
    if dn: env[an:an+dn]=np.linspace(1,s,dn)
    if rn: env[-rn:]*=np.linspace(1,0,rn)
    return env
def overdrive(x,drive=8,mix=0.7):
    dr=np.tanh(drive*x)/np.tanh(drive)
    return (1-mix)*x+mix*dr

# ---------- 乐器 ----------
def guitar(midi,dur,gain=0.5,drive=9):
    f=hz(midi); ph=phase(f,dur)
    raw=np.sin(ph)+0.7*np.sin(ph*1.5)+0.35*np.sin(ph*2)+0.12*rnd(len(ph))
    od=overdrive(raw,drive,0.72); od/=np.abs(od).max()+1e-9
    sos=butter(2,5200,btype='low',fs=SR,output='sos')
    return sosfilt(sos,od)*adsr(len(od),0.004,0.05,0.85,min(0.12,dur*0.3))*gain

def bass(midi,dur,gain=0.5):
    ph=phase(hz(midi),dur)
    raw=0.6*np.sin(ph)+0.4*np.sign(np.sin(ph))
    sos=butter(2,400,btype='low',fs=SR,output='sos')
    return sosfilt(sos,raw)*adsr(len(raw),0.006,0.04,0.9,min(0.1,dur*0.25))*gain

def lead(midi,dur,gain=0.4):
    """明亮号角 lead —— 儿童主题曲主唱音色"""
    ph=phase(hz(midi),dur,vib=6.0,dep=0.008)
    x=0.5*np.sign(np.sin(ph))+0.3*np.sin(ph)+0.2*np.sin(ph*2)+0.1*np.sin(ph*3)
    sos=butter(2,6500,btype='low',fs=SR,output='sos')
    return sosfilt(sos,x)*adsr(len(x),0.01,0.05,0.85,min(0.14,dur*0.3))*gain

def kick(g=0.9):
    dur=0.32;n=int(dur*SR);t=np.arange(n)/SR
    f=45+95*np.exp(-t*22)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*11)*g

def snare(g=0.5):
    dur=0.2;n=int(dur*SR);t=np.arange(n)/SR
    sos=butter(2,[1200,9000],btype='band',fs=SR,output='sos')
    return (sosfilt(sos,rnd(n))*0.8+np.sin(2*np.pi*180*t)*0.35)*np.exp(-t*16)*g

def hat(g=0.2,op=False):
    dur=0.15 if op else 0.05;n=int(dur*SR);t=np.arange(n)/SR
    sos=butter(2,7000,btype='high',fs=SR,output='sos')
    return sosfilt(sos,rnd(n))*np.exp(-t*(14 if op else 55))*g

# ---------- 原创旋律（按提取轮廓重塑）----------
# D 小调/D 多利亚色彩，音域 A3(57)~D5(74)，中位 C4(60)
# HOOK: 提取轮廓 = 起(中位C4)→扬(D5)→落(B3)→再扬(B4)→收(D4)
# 每小节: [(拍位置, MIDI, 时长拍)]
HOOK=[
  # 第1小节: 呼喊动机「长-短短」——对齐提取的 0.33/0.15/0.16
  [(0,62,1.5),(1.5,62,0.5),(2.0,62,0.5),(2.5,65,1.5)],   # D D D F
  # 第2小节: 级进上行到 D5（提取的最高点）
  [(0,65,0.5),(0.5,67,0.5),(1.0,69,0.5),(1.5,72,0.5),(2.0,74,2.0)],  # F G A C D5
  # 第3小节: 回落到 B3（提取低点）
  [(0,72,0.5),(0.5,69,0.5),(1.0,67,0.5),(1.5,65,0.5),(2.0,62,2.0)],  # C A G F D
  # 第4小节: 再扬 B4 后收 D4
  [(0,71,1.0),(1.0,71,0.5),(1.5,69,0.5),(2.0,62,2.0)],   # B4 B4 A D4
  # 第5小节: 呼喊动机变奏
  [(0,65,1.5),(1.5,65,0.5),(2.0,65,0.5),(2.5,67,1.5)],   # F F F G
  # 第6小节: 上行
  [(0,69,0.5),(0.5,71,0.5),(1.0,72,0.5),(1.5,74,0.5),(2.0,72,2.0)],  # A B C D5 C
  # 第7小节: 下行
  [(0,69,0.5),(0.5,67,0.5),(1.0,65,0.5),(1.5,64,0.5),(2.0,62,2.0)],  # A G F E D
  # 第8小节: 收束
  [(0,62,1.0),(1.0,60,0.5),(1.5,62,0.5),(2.0,62,2.0)],   # D C D D
]
# 和声进行 Dm - Bb - F - C（原创）
PROG=[[50,53,57],[46,50,53],[53,57,60],[48,52,55]]  # Dm / Bb / F / C 三和弦

# ---------- 混音 ----------
N=int(DUR*SR); mix=np.zeros(N)
def place(sig,st,g=1.0):
    i=int(st*SR)
    if i>=N: return
    j=min(N,i+len(sig)); mix[i:j]+=sig[:j-i]*g

TL=len(HOOK)*BAR   # 主题长度
sec=0
while sec*TL < DUR-0.5:
    base=sec*TL
    energy=1.0 if sec%2==0 else 1.06
    for bar in range(len(HOOK)):
        bt=base+bar*BAR
        chord=PROG[bar%len(PROG)]
        root=chord[0]
        # 鼓：呼喊动机在每 4 小节头的特殊处理
        for b in range(4):
            t=bt+b*BEAT
            place(kick(0.9*energy),t)
            if b in (1,3):
                place(snare(0.5*energy),t)
            place(hat(0.2*energy),t)
            place(hat(0.13*energy),t+BEAT/2)
        if bar%2==1: place(hat(0.16,op=True),bt+3.5*BEAT)
        # 贝斯八分推进（对齐 0.31-0.33s 驱动）
        for b in range(8):
            m=root-12 if b%2==0 else root-5
            place(bass(m,BEAT*0.46,0.5*energy),bt+b*BEAT/2)
        # 吉他强力和弦
        for b in range(8):
            place(guitar(root,BEAT*0.45,0.32*energy,drive=9),bt+b*BEAT/2)
        # 主旋律
        for pos,m,nb in HOOK[bar]:
            place(lead(m,nb*BEAT*0.92,0.4*energy),bt+pos*BEAT)
    sec+=1

# 开头呼喊（长-短短，对齐提取的 0.33/0.15/0.16）
for rep in range(2):
    st=rep*BAR
    for pos,m,nb in [(0,62,1.5),(1.5,62,0.5),(2.0,62,0.5),(2.5,65,1.5)]:
        place(lead(m,nb*BEAT*0.9,0.42),st+pos*BEAT)
    place(kick(0.9),st); place(snare(0.5),st+BEAT)
    place(guitar(50,BEAT*1.8,0.3),st)

# 淡入淡出 + 限幅
fade=int(2.5*SR)
mix[:fade]*=np.linspace(0,1,fade); mix[-fade:]*=np.linspace(1,0,fade)
peak=np.abs(mix).max(); mix=mix/peak*0.86
pcm=(np.clip(mix,-1,1)*32767).astype(np.int16)

out='public/audio/bgm-rock2.wav'
with wave.open(out,'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
clip=int((np.abs(pcm)>=32760).sum())
print(f'WROTE {out} dur={DUR}s peak={int(np.abs(pcm).max())} rms={np.sqrt(np.mean(mix**2)):.4f} clip={clip}')

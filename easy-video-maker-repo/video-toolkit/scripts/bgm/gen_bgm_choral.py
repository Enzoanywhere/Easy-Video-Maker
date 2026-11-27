#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
原创 BGM —— A 大调 + 共振峰合成童声合唱 + 摇滚编制。

听感来源定位（librosa 专业分析）：
  - 调性: A 大调 / F# 小调（STFT/CQT/CENS 三种 chroma 一致；音阶归属 A 大调 78%）
  - 听感核心: 真人童声合唱 —— 频谱平坦度 0.033（强谐波性）+ 共振峰序列
              441/603/829/1034/1211/1373/1766/2008 Hz
  - 节奏: 长-短短呼喊动机 + 0.31-0.33s 稳定八分驱动, BPM≈126
  - 编制: 失真电吉他摇滚 + 鼓 + 贝斯

童声合唱用「共振峰合成」：声门脉冲激励 → 并联带通滤波器组塑形元音 → 多声部
轻微失谐(±8音分) + 错峰起音 + 短混响，模拟一群孩子唱「啊」。纯合成，非采样真人，0 版权风险。

旋律/和声原创：A 大调音阶，I-vi-IV-V 进行，8 小节 hook，不复制参考曲任何音型。
"""
import numpy as np
import wave
from scipy.signal import butter, sosfilt

SR=44100; DUR=96.0; BPM=126.0; BEAT=60/BPM; BAR=BEAT*4
rng=np.random.default_rng(20261127)

def hz(m): return 440.0*2.0**((m-69)/12.0)
def rnd(n): return rng.standard_normal(n)
def adsr(n,a=0.01,d=0.1,s=0.78,r=0.14):
    e=np.ones(n); an=int(a*SR); dn=int(d*SR); rn=int(r*SR)
    if an: e[:an]=np.linspace(0,1,an)
    if dn: e[an:an+dn]=np.linspace(1,s,dn)
    if rn: e[-rn:]*=np.linspace(1,0,rn)
    return e

# ============ 童声共振峰合成 ============
# 童声道短，共振峰比成人高约 15%。元音 F1/F2/F3（Hz）
VOWELS={
    'a': [(820,110,1.0),(1250,130,0.65),(2800,180,0.28)],  # 啊（明亮开口）
    'o': [(560,90,1.0),(950,110,0.6),(2600,180,0.22)],     # 哦
    'e': [(620,90,1.0),(1750,150,0.5),(2700,180,0.25)],    # 诶
}
_VOICE_FILTERS={}
def vowel_filters(v):
    if v not in _VOICE_FILTERS:
        _VOICE_FILTERS[v]=[butter(2,[max(50,fc-bw/2),min(SR/2-100,fc+bw/2)],
                                  btype='band',fs=SR,output='sos') for fc,bw,_ in VOWELS[v]]
    return _VOICE_FILTERS[v]

def child_voice(midi,dur,vowel='a',gain=0.3,detune_cents=0):
    """单个童声声部：声门脉冲激励 + 共振峰滤波 + 颤音"""
    f=hz(midi)*2.0**(detune_cents/1200)
    n=int(dur*SR); t=np.arange(n)/SR
    # 声门脉冲串：用窄脉冲模拟声带振动（比正弦谐波丰富，更像人声）
    period=SR/f
    # 相位累加生成脉冲串
    ph=np.cumsum(np.full(n,f/SR))%1.0
    # 声门波形：上升慢下降快的脉冲（Rosenberg 模型近似）
    pulse=np.where(ph<0.5, np.sin(np.pi*ph/0.5), -0.6*np.sin(np.pi*(ph-0.5)/0.5))
    # 加轻微气声
    pulse+=0.03*rnd(n)
    # 颤音（童声自然抖动）
    vib=1+0.006*np.sin(2*np.pi*5.2*t)
    # 共振峰滤波（对脉冲串塑形）—— 颤音通过重采样近似（轻微频率漂移）
    filt=vowel_filters(vowel)
    out=np.zeros(n)
    for sos,(_,_,amp) in zip(filt,VOWELS[vowel]):
        out+=sosfilt(sos,pulse)*amp
    out/=np.abs(out).max()+1e-9
    # 颤音：用包络调制近似亮度起伏
    out*= (0.94+0.06*np.sin(2*np.pi*5.2*t))
    env=adsr(n,0.03,0.08,0.8,min(0.18,dur*0.35))
    return out*env*gain

def child_choir(midi,dur,vowel='a',gain=0.42):
    """童声合唱：3 声部（主 + 低八度 + 五度）轻微失谐、错峰起音 + 短混响"""
    n=int(dur*SR)
    out=np.zeros(n)
    # 主声部
    out+=child_voice(midi,dur,vowel,gain=gain,detune_cents=-6)
    out+=child_voice(midi,dur,vowel,gain=gain*0.8,detune_cents=+7)
    # 低八度和声（合唱厚度）
    low=child_voice(midi-12,dur,'o',gain=gain*0.45,detune_cents=+4)
    out[:len(low)]+=low
    # 五度和声
    fifth=child_voice(midi+7,dur,vowel,gain=gain*0.3,detune_cents=-9)
    out[:len(fifth)]+=fifth
    # 简单混响：两个延迟抽头
    for dl,att in [(int(0.09*SR),0.18),(int(0.17*SR),0.1)]:
        out[dl:]+=out[:-dl]*att
    return out

# ============ 摇滚编制 ============
def guitar(midi,dur,gain=0.4,drive=9):
    f=hz(midi); n=int(dur*SR); t=np.arange(n)/SR
    ph=2*np.pi*f*t
    raw=np.sin(ph)+0.7*np.sin(ph*1.5)+0.35*np.sin(ph*2)+0.12*rnd(n)
    dr=np.tanh(drive*raw)/np.tanh(drive)
    od=0.28*raw+0.72*dr; od/=np.abs(od).max()+1e-9
    sos=butter(2,5200,btype='low',fs=SR,output='sos')
    return sosfilt(sos,od)*adsr(n,0.004,0.05,0.85,min(0.12,dur*0.3))*gain

def bass(midi,dur,gain=0.5):
    f=hz(midi); n=int(dur*SR); t=np.arange(n)/SR
    ph=2*np.pi*f*t
    raw=0.6*np.sin(ph)+0.4*np.sign(np.sin(ph))
    sos=butter(2,400,btype='low',fs=SR,output='sos')
    return sosfilt(sos,raw)*adsr(n,0.006,0.04,0.9,min(0.1,dur*0.25))*gain

def kick(g=0.9):
    n=int(0.32*SR); t=np.arange(n)/SR
    f=45+95*np.exp(-t*22)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*11)*g

def snare(g=0.5):
    n=int(0.2*SR); t=np.arange(n)/SR
    sos=butter(2,[1200,9000],btype='band',fs=SR,output='sos')
    return (sosfilt(sos,rnd(n))*0.8+np.sin(2*np.pi*180*t)*0.35)*np.exp(-t*16)*g

def hat(g=0.2,op=False):
    n=int((0.15 if op else 0.05)*SR); t=np.arange(n)/SR
    sos=butter(2,7000,btype='high',fs=SR,output='sos')
    return sosfilt(sos,rnd(n))*np.exp(-t*(14 if op else 55))*g

# ============ 原创旋律（A 大调）============
# A大调音阶: A=69 B=71 C#=73 D=74 E=76 F#=78 G#=80 (取A4-E5区)
# 8小节 hook，级进+重复+呼应，呼喊动机在1/5小节
HOOK=[
  # 长-短短呼喊 + 落音
  [(0,69,1.5,'a'),(1.5,69,0.5,'a'),(2.0,69,0.5,'a'),(2.5,73,1.5,'a')],
  # 级进上行到 E5
  [(0,76,0.5,'a'),(0.5,74,0.5,'o'),(1.0,73,0.5,'a'),(1.5,71,0.5,'o'),(2.0,69,2.0,'a')],
  # 折返上行
  [(0,68,0.5,'o'),(0.5,69,0.5,'a'),(1.0,71,0.5,'o'),(1.5,73,0.5,'a'),(2.0,74,2.0,'a')],
  # 回落收
  [(0,73,1.0,'a'),(1.0,71,0.5,'o'),(1.5,69,0.5,'a'),(2.0,69,2.0,'a')],
  # 呼喊变奏
  [(0,71,1.5,'a'),(1.5,71,0.5,'a'),(2.0,71,0.5,'a'),(2.5,74,1.5,'a')],
  # 上行
  [(0,76,0.5,'a'),(0.5,78,0.5,'o'),(1.0,76,0.5,'a'),(1.5,74,0.5,'o'),(2.0,73,2.0,'a')],
  # 下行
  [(0,71,0.5,'o'),(0.5,69,0.5,'a'),(1.0,68,0.5,'o'),(1.5,66,0.5,'a'),(2.0,69,2.0,'a')],
  # 收束
  [(0,69,1.0,'a'),(1.0,73,0.5,'a'),(1.5,69,0.5,'o'),(2.0,69,2.0,'a')],
]
# 和声进行 A - F#m - D - E (I-vi-IV-V)
PROG=[[45,49,52],[42,45,49],[38,42,45],[40,44,47]]  # A2/F#2/D2/E2 附近根音

N=int(DUR*SR); mix=np.zeros(N)
def place(sig,st,g=1.0):
    i=int(st*SR)
    if i>=N: return
    j=min(N,i+len(sig)); mix[i:j]+=sig[:j-i]*g

TL=len(HOOK)*BAR
sec=0
while sec*TL<DUR-0.5:
    base=sec*TL; en=1.0 if sec%2==0 else 1.05
    for bar in range(len(HOOK)):
        bt=base+bar*BAR; root=PROG[bar%len(PROG)][0]
        # 鼓：进行曲驱动
        for b in range(4):
            t=bt+b*BEAT
            place(kick(0.9*en),t)
            if b in (1,3): place(snare(0.5*en),t)
            place(hat(0.2*en),t); place(hat(0.13*en),t+BEAT/2)
        if bar%2==1: place(hat(0.16,op=True),bt+3.5*BEAT)
        # 贝斯八分
        for b in range(8):
            place(bass((root if b%2==0 else root+7)-12,BEAT*0.46,0.5*en),bt+b*BEAT/2)
        # 吉他强力和弦（弱化，给童声让位）
        for b in range(8):
            place(guitar(root,BEAT*0.44,0.24*en,drive=9),bt+b*BEAT/2)
        # 童声合唱主旋律
        for pos,m,nb,v in HOOK[bar]:
            place(child_choir(m,nb*BEAT*0.94,v,gain=0.4*en),bt+pos*BEAT)
    sec+=1

# 开头呼喊（长-短短）—— 童声合唱喊出
for rep in range(2):
    st=rep*BAR
    for pos,m,nb in [(0,69,1.5),(1.5,69,0.5),(2.0,69,0.5),(2.5,73,1.5)]:
        place(child_choir(m,nb*BEAT*0.9,'a',gain=0.44),st+pos*BEAT)
    place(kick(0.9),st); place(snare(0.5),st+BEAT)
    place(guitar(45,BEAT*1.8,0.28),st)

# 淡入淡出 + 限幅
fade=int(2.5*SR)
mix[:fade]*=np.linspace(0,1,fade); mix[-fade:]*=np.linspace(1,0,fade)
peak=np.abs(mix).max(); mix=mix/peak*0.86
pcm=(np.clip(mix,-1,1)*32767).astype(np.int16)

out='public/audio/bgm-choral.wav'
with wave.open(out,'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
clip=int((np.abs(pcm)>=32760).sum())
print(f'WROTE {out} dur={DUR}s peak={int(np.abs(pcm).max())} rms={np.sqrt(np.mean(mix**2)):.4f} clip={clip}')

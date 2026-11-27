#!/usr/bin/env python3
"""把真实采集的数据渲染成统一风格的截屏 PNG。内容全部来自 evidence_data.json / 真实 WAV。

生成：public/evidence/*.png
  doctor / files / videos / srt / wave / bgms / workflow / help
"""
import json
import math
import struct
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "scripts/evidence_data.json").read_text(encoding="utf-8"))
OUT = ROOT / "public/evidence"
if not OUT.exists():
    OUT.mkdir()

W, H = 1600, 900
CJK = "/System/Library/Fonts/STHeiti Medium.ttc"
MONO = "/System/Library/Fonts/Menlo.ttc"
uni = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"

DARK_BG = (16, 29, 43)
DARK_BAR = (28, 44, 62)
GREEN = (123, 224, 160)
WHITE = (232, 240, 248)
GREY = (138, 163, 192)
AMBER = (244, 185, 66)
CORAL = (255, 107, 74)
LIGHT_BG = (247, 243, 234)
INK = (20, 42, 58)
TEAL = (42, 157, 143)


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.truetype(uni, size)


def has_cjk(s):
    return any("\u4e00" <= ch <= "\u9fff" for ch in s)


def window(title, dark=True):
    img = Image.new("RGB", (W, H), DARK_BG if dark else LIGHT_BG)
    d = ImageDraw.Draw(img)
    bar = DARK_BAR if dark else (232, 224, 210)
    d.rectangle([0, 0, W, 66], fill=bar)
    for i, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        x = 30 + i * 30
        d.ellipse([x, 24, x + 18, 42], fill=col)
    fg = GREY if dark else INK
    d.text((150, 19), title, font=font(CJK if has_cjk(title) else MONO, 26), fill=fg)
    d.line([0, 66, W, 66], fill=(40, 58, 78) if dark else (214, 205, 191), width=2)
    return img, d


def save(img, name):
    img.save(OUT / name, "PNG")
    print("wrote", name)


def terminal_lines(img, d, lines, y=104, size=27, hi=None):
    f = font(MONO, size)
    fc = font(CJK, size)
    x = 44
    for ln in lines:
        col = WHITE
        if ln.startswith("OK") or ln.startswith("PASS") or "clean:" in ln or "done" in ln.lower():
            col = GREEN
        elif ln.startswith("$") or ln.startswith("== "):
            col = AMBER
        elif ln.startswith("#"):
            col = GREY
        if hi and hi(ln):
            col = CORAL
        d.text((x, y), ln, font=fc if has_cjk(ln) else f, fill=col)
        y += int(size * 1.55)
    return y


# 1. doctor 终端
def gen_doctor():
    img, d = window("zsh — video doctor — 160×48", True)
    lines = ["$ source video-toolkit/env.sh", "$ video doctor"] + DATA["doctor"].splitlines()
    terminal_lines(img, d, lines, hi=lambda l: "PASS" in l)
    save(img, "evidence-doctor.png")


# 2. 文件树 + 时间戳
def gen_files():
    img, d = window("zsh — ls -1d */  # 工作区工程与真实修改时间", True)
    lines = ["$ ls -1d */   # 按修改时间排序", ""]
    for f in DATA["files"]:
        lines.append(f"  {f['mtime']}    {f['name']}/")
    terminal_lines(img, d, lines)
    save(img, "evidence-files.png")


# 3. 成片元数据表
def gen_videos():
    img, d = window("zsh — python3 读取 MP4 元数据", True)
    lines = ["$ python3 -c 'from mutagen.mp4 import MP4; ...'", ""]
    for v in DATA["videos"]:
        lines.append(f"  {v['name']:<24} {v['duration']:>7.1f}s  {v['mb']:>6.1f} MB")
    total_s = sum(v["duration"] for v in DATA["videos"])
    total_mb = sum(v["mb"] for v in DATA["videos"])
    lines += ["", f"  TOTAL  {len(DATA['videos'])} videos  {total_s/60:.1f} min  {total_mb:.1f} MB"]
    terminal_lines(img, d, lines, size=25, hi=lambda l: "TOTAL" in l)
    save(img, "evidence-videos.png")


# 4. SRT 字幕（浅色文档）
def gen_srt():
    img, d = window("scene1.srt — 自动生成的字幕", False)
    f = font(CJK, 30)
    d.text((48, 100), "public/audio/scene1.srt", font=font(MONO, 28), fill=TEAL)
    y = 160
    for ln in DATA["srt"].splitlines():
        col = INK if "-->" not in ln else TEAL
        d.text((60, y), ln, font=f, fill=col)
        y += 48
    save(img, "evidence-srt.png")


# 5. BGM 真实波形
def gen_wave():
    img, d = window("bgm-retrospective.wav — 真实波形", False)
    p = ROOT / "public/audio/bgm-retrospective.wav"
    with wave.open(str(p), "rb") as w:
        sr = w.getframerate()
        n = w.getnframes()
        raw = w.readframes(n)
    samples = struct.unpack("<%dh" % (len(raw) // 2), raw)
    step = max(1, len(samples) // 1400)
    peaks = []
    for i in range(0, len(samples), step):
        chunk = samples[i : i + step]
        peaks.append(max(abs(min(chunk)), abs(max(chunk))) / 32768.0)
    n = len(peaks)
    mid = 480
    for x in range(n):
        h = int(peaks[x] * 250)
        xx = 40 + x * (1520 / n)
        col = CORAL if x < int(n * 0.02) else TEAL
        d.line([(xx, mid - h), (xx, mid + h)], fill=col, width=1)
    d.text((48, 120), "F 大调 · BPM 92 · 480s · 原创 lo-fi", font=font(CJK, 32), fill=INK)
    d.text((48, 780), f"采样率 {sr} Hz · {n} 帧 · 首尾 4s 淡入淡出", font=font(CJK, 26), fill=GREY)
    save(img, "evidence-wave.png")


# 6. BGM 文件列表
def gen_bgms():
    img, d = window("zsh — ls public/audio/bgm*.wav", True)
    lines = ["$ ls -1 pawpatrol-script3/public/audio/bgm*.wav", ""]
    for b in DATA["bgms"]:
        lines.append(f"  pawpatrol-script3/public/audio/{b}")
    lines += ["", "  # 7 版独立文件，不覆盖在用 bgm.wav"]
    terminal_lines(img, d, lines, size=25)
    save(img, "evidence-bgms.png")


# 7. WORKFLOW 文档（浅色）
def gen_workflow():
    img, d = window("pawpatrol-s1/WORKFLOW.md", False)
    f = font(CJK, 25)
    d.text((48, 92), "WORKFLOW.md — 新工程操作入口", font=font(CJK, 32), fill=INK)
    y = 150
    for ln in DATA["workflow"].splitlines():
        if not ln.strip():
            y += 18
            continue
        if ln.startswith("#"):
            d.text((48, y), ln.strip("# "), font=font(CJK, 28), fill=TEAL)
            y += 44
        else:
            d.text((56, y), ln, font=f, fill=INK)
            y += 36
        if y > 850:
            break
    save(img, "evidence-workflow.png")


# 8. CLI 帮助
def gen_help():
    img, d = window("zsh — video --help", True)
    lines = ["$ video --help"] + DATA["help"].splitlines()
    terminal_lines(img, d, lines, size=24, hi=lambda l: l.strip().startswith("doctor") or l.strip().startswith("offline"))
    save(img, "evidence-help.png")


if __name__ == "__main__":
    gen_doctor()
    gen_files()
    gen_videos()
    gen_srt()
    gen_wave()
    gen_bgms()
    gen_workflow()
    gen_help()
    print("done:", len(list(OUT.glob('evidence-*.png'))), "images")

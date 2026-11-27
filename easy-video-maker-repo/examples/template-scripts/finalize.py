#!/usr/bin/env python3
"""把 Remotion 渲染出的 in-progress 临时文件复制为最终 MP4 并做基本校验。"""
import shutil
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "out"
final = OUT / "pawpatrol-s1-guide.mp4"
candidates = list(OUT.glob("*.remotion-in-progress"))

if not final.exists() and candidates:
    src = max(candidates, key=lambda p: p.stat().st_size)
    shutil.copyfile(src, final)
    print(f"copied {src.name} -> {final.name}")

data = final.read_bytes()
checks = {
    "size_bytes": len(data),
    "has_ftyp": data[4:8] == b"ftyp",
    "has_moov": b"moov" in data,
    "has_mdat": b"mdat" in data,
}
for k, v in checks.items():
    print(f"{k}: {v}")

idx = data.find(b"mvhd")
if idx > 0:
    version = data[idx + 4]
    if version == 0:
        timescale = int.from_bytes(data[idx + 16 : idx + 20], "big")
        duration = int.from_bytes(data[idx + 20 : idx + 24], "big")
    else:
        timescale = int.from_bytes(data[idx + 24 : idx + 28], "big")
        duration = int.from_bytes(data[idx + 28 : idx + 36], "big")
    print(f"duration_sec: {duration / timescale:.2f}")

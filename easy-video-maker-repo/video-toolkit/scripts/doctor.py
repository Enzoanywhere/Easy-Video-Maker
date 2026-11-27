#!/usr/bin/env python3
"""检查视频流水线依赖是否齐全，避免其他对话重复安装。"""
import os
import shutil
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

EXPECTED = {
    "edge-tts": "7.3.1",
    "mutagen": "1.48.1",
    "numpy": "2.5.5",
    "scipy": "1.18.1",
    "librosa": "1.0.1",
    "soundfile": "0.14.0",
    "numba": "0.68.1",
    "llvmlite": "0.50.0",
    "matplotlib": "3.11.2",
}


def main():
    bad = 0
    print("== python packages ==")
    for name, expected in EXPECTED.items():
        try:
            got = version(name)
        except PackageNotFoundError:
            got = None
        if got == expected:
            print(f"OK      {name}=={got}")
        else:
            bad += 1
            print(f"MISSING {name}: expected {expected}, got {got}")

    print("\n== commands ==")
    for cmd in ("python3", "edge-tts", "node", "npx", "afconvert"):
        path = shutil.which(cmd)
        if path:
            print(f"OK      {cmd}: {path}")
        else:
            bad += 1
            print(f"MISSING {cmd}")
    afinfo = shutil.which("afinfo")
    print(f"{'OK     ' if afinfo else 'OPTIONAL'} afinfo: {afinfo or 'not found'}")

    root = Path(os.environ.get("WB_ROOT", "/Users/a123/WorkBuddy/2026-11-25-10-23-46"))
    node_modules = Path(os.environ.get("WB_NODE_MODULES", str(root / "workbuddy-intro" / "node_modules")))
    browser = Path(
        os.environ.get(
            "WB_REMOTION_BROWSER",
            str(node_modules / ".remotion/chrome-headless-shell/158.0.8127.2-remotion-v3/mac-arm64/chrome-headless-shell-mac-arm64/chrome-headless-shell"),
        )
    )
    print("\n== shared assets ==")
    for label, path in (("node_modules", node_modules), ("remotion browser", browser)):
        if path.exists():
            print(f"OK      {label}: {path}")
        else:
            bad += 1
            print(f"MISSING {label}: {path}")

    if bad:
        print(f"\nFAILED: {bad} item(s) missing. Install with: python3 -m pip install -r {root}/video-toolkit/requirements.txt")
        return 1
    print("\nPASS: 依赖齐全；无需重复安装。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""把 examples/evidence/*.png.b64 还原成 PNG。

用法：
    python3 examples/evidence/decode.py [输出目录]

默认输出到运行目录下的 evidence/ 文件夹。
"""
import base64
import sys
from pathlib import Path


def main() -> None:
    here = Path(__file__).resolve().parent
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / "evidence"
    out.mkdir(parents=True, exist_ok=True)

    files = sorted(here.glob("*.png.b64"))
    if not files:
        raise SystemExit(f"没有找到 base64 存档: {here}")

    for src in files:
        raw = base64.b64decode("".join(src.read_text(encoding="ascii").split()))
        dst = out / src.name.removesuffix(".b64")
        dst.write_bytes(raw)
        print(f"{dst}  {len(raw) / 1024:.1f} KB")

    print(f"完成：{len(files)} 张截屏 -> {out}")


if __name__ == "__main__":
    main()

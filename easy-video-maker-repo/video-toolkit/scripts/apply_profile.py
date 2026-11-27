#!/usr/bin/env python3
"""把语速/音色档位写入新工程。由 video new 调用，不直接面向用户。"""
import argparse
import re
from pathlib import Path

PROFILES = {
    "child": {
        "voice": "zh-CN-XiaoyiNeural",
        "rate": "-15%",
        "theme": "bright",
        "audience": "陪 2 岁孩子看动画的中国家长",
        "comment": "面向低龄孩子家长，语速放慢，便于边看边讲",
    },
    "five": {
        "voice": "zh-CN-XiaoyiNeural",
        "rate": "+5%",
        "theme": "bright",
        "audience": "5 分钟导览，信息密度中等",
        "comment": "5 分钟导览版，语速略快",
    },
    "adult": {
        "voice": "zh-CN-XiaoyiNeural",
        "rate": "+15%",
        "theme": "dark",
        "audience": "成人向行业/文化拆解",
        "comment": "面向成人观众，语速明快、有激情",
    },
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dest", help="新工程目录")
    ap.add_argument("--profile", choices=list(PROFILES), default="child")
    ap.add_argument("--voice", help="覆盖档案默认音色")
    ap.add_argument("--rate", help="覆盖档案默认语速，如 +15%")
    args = ap.parse_args()

    root = Path(args.dest).resolve()
    if not root.is_dir():
        raise SystemExit(f"工程目录不存在: {root}")

    p = PROFILES[args.profile]
    voice = args.voice or p["voice"]
    rate = args.rate or p["rate"]

    (root / "video-profile.env").write_text(
        "\n".join(
            [
                f"WB_PROFILE={args.profile}",
                f"WB_VOICE={voice}",
                f"WB_RATE={rate}",
                f"WB_THEME={p['theme']}",
                f"WB_AUDIENCE={p['audience']}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    ga = root / "scripts" / "gen_audio.py"
    if ga.exists():
        s = ga.read_text(encoding="utf-8")
        s = re.sub(r"^VOICE\s*=.*$", f'VOICE = "{voice}"', s, flags=re.M)
        s = re.sub(
            r"^RATE\s*=.*$",
            f'RATE = "{rate}"  # {p["comment"]}',
            s,
            flags=re.M,
        )
        ga.write_text(s, encoding="utf-8")

    ep = root / "EPISODE.md"
    if ep.exists():
        s = ep.read_text(encoding="utf-8")
        s = re.sub(
            r"^- 配音:.*$",
            f"- 配音: {voice}（语速 {rate}，档位 {args.profile}）",
            s,
            flags=re.M,
        )
        ep.write_text(s, encoding="utf-8")

    # 注释不能进配音：清掉 new-episode.sh 模板写入的说明行。
    script = root / "script.txt"
    if script.exists():
        lines = script.read_text(encoding="utf-8").splitlines()
        cleaned = [line for line in lines if not line.lstrip().startswith("#")]
        script.write_text("\n".join(cleaned).lstrip("\n"), encoding="utf-8")

    print(f"profile={args.profile} voice={voice} rate={rate} theme={p['theme']}")


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# 离线出片：跳过联网配音，用本地已有音频直接渲染。
# 适用：断网时，或改了画面（Scene*.tsx）但不想重新配音时。
# 注意：改了 script.txt 文案需要重新配音，那一步要联网（edge-tts），断网做不了。
set -e
cd "$(dirname "$0")/.."

echo "== 0/4 检查本地素材 =="
need=0
for i in 1 2 3 4 5 6; do
  if [ ! -f "public/audio/scene${i}.mp3" ]; then echo "缺少 public/audio/scene${i}.mp3"; need=1; fi
done
[ -f public/audio/bgm.wav ] || { echo "缺少 public/audio/bgm.wav"; need=1; }
[ -f src/data/scenes.ts ] || { echo "缺少 src/data/scenes.ts（时间轴数据）"; need=1; }
if [ "$need" -ne 0 ]; then
  echo "本地素材不全。断网无法重新配音，请先联网跑一次 bash scripts/build.sh 生成素材。"
  exit 1
fi
echo "本地素材齐全，开始离线渲染（不联网、不消耗 token）"

echo "== 1/4 类型检查 =="
npx tsc --noEmit

echo "== 2/4 渲染（纯本地）=="
BROWSER_ROOT="/Users/a123/WorkBuddy/2026-11-25-10-23-46/workbuddy-intro/node_modules/.remotion/chrome-headless-shell/158.0.8127.2-remotion-v3/mac-arm64/chrome-headless-shell-mac-arm64/chrome-headless-shell"
export NODE_OPTIONS="${NODE_OPTIONS:+$NODE_OPTIONS }--require=$PWD/scripts/tmpdir-patch.cjs"
npx remotion render src/index.ts PawPatrolS1 out/pawpatrol-s1-guide.mp4 \
  --browser-executable="$BROWSER_ROOT" --concurrency=4

echo "== 3/4 成片校验 =="
python3 scripts/finalize.py

echo "== 4/4 清理临时文件 =="
for i in $(seq 1 30); do
  OUT=$(python3 scripts/cleanup.py 2>&1) || true
  echo "$OUT" | tail -n 1
  echo "$OUT" | grep -q 'clean:' && break
done

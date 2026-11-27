#!/usr/bin/env bash
# 一键重建：改 script.txt 后重生成配音+字幕，再渲染 MP4，最后自动清理临时文件。
# 沙箱绕过：--browser-executable 指向已下载浏览器；NODE_OPTIONS 预加载 tmpdir 补丁。
set -e
cd "$(dirname "$0")/.."

echo "== 0/5 清理上次渲染残留 =="
for i in $(seq 1 30); do
  OUT=$(python3 scripts/cleanup.py 2>&1) || true
  echo "$OUT" | tail -n 1
  echo "$OUT" | grep -q 'clean:' && break
done

echo "== 1/5 配音与字幕 =="
python3 scripts/gen_audio.py

echo "== 2/5 BGM（若已存在则跳过生成，见下）=="
if [ ! -f public/audio/bgm.wav ]; then python3 scripts/gen_bgm.py; else echo "bgm.wav exists, skip"; fi

echo "== 3/5 类型检查 =="
npx tsc --noEmit

echo "== 4/5 渲染 =="
BROWSER_ROOT="/Users/a123/WorkBuddy/2026-11-25-10-23-46/workbuddy-intro/node_modules/.remotion/chrome-headless-shell/158.0.8127.2-remotion-v3/mac-arm64/chrome-headless-shell-mac-arm64/chrome-headless-shell"
export NODE_OPTIONS="--require=$PWD/scripts/tmpdir-patch.cjs"
npx remotion render src/index.ts PawPatrolS1 out/pawpatrol-s1-guide.mp4 \
  --browser-executable="$BROWSER_ROOT" --concurrency=4

python3 scripts/finalize.py

echo "== 5/5 清理本轮临时文件 =="
for i in $(seq 1 30); do
  OUT=$(python3 scripts/cleanup.py 2>&1) || true
  echo "$OUT" | tail -n 1
  echo "$OUT" | grep -q 'clean:' && break
done

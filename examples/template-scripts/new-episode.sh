#!/usr/bin/env bash
# 从 pawpatrol-s1 模板创建「新一集」工程骨架。
# 每个新工程是独立的 Remotion 项目，组件名沿用 PawPatrolS1 即可（互不冲突）。
# 用法：bash scripts/new-episode.sh <英文标识> <中文标题>
# 例：  bash scripts/new-episode.sh characters "认识 8 位队友"
set -e

SRC="$(cd "$(dirname "$0")/.." && pwd)"
BASE="$(dirname "$SRC")"

ID="${1:-}"
TITLE="${2:-}"
if [ -z "$ID" ] || [ -z "$TITLE" ]; then
  echo "用法: bash scripts/new-episode.sh <英文标识> <中文标题>"
  echo "例:   bash scripts/new-episode.sh characters '认识 8 位队友'"
  exit 1
fi

DEST="$BASE/pawpatrol-$ID"
if [ -e "$DEST" ]; then
  echo "目标已存在: $DEST （请先删除或换一个标识）"
  exit 1
fi

echo "== 创建工程骨架: $DEST =="
mkdir -p "$DEST/src/scenes" "$DEST/src/data" "$DEST/public/audio" "$DEST/scripts" "$DEST/out"

# 复制脚本、源码与静态配置（不含渲染产物/音频/临时目录）
cp "$SRC"/scripts/*.py "$SRC"/scripts/*.sh "$SRC"/scripts/*.cjs "$DEST/scripts/"
cp -R "$SRC"/src/. "$DEST/src/"
cp "$SRC"/tsconfig.json "$SRC"/remotion.config.ts "$SRC"/package.json "$DEST/"

# 复用已安装的依赖（软链，避免重复占用 1.1G）
ln -s "$BASE/workbuddy-intro/node_modules" "$DEST/node_modules"

# 参数化输出文件名（模板里的 MP4 名需要改成新一集的标识）
python3 - "$DEST" "$ID" "$TITLE" <<'PY'
import sys
from pathlib import Path
dest, ident, title = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
out_name = f'pawpatrol-{ident}-guide.mp4'

b = dest / 'scripts' / 'build.sh'
b.write_text(b.read_text().replace('out/pawpatrol-s1-guide.mp4', f'out/{out_name}'))

f = dest / 'scripts' / 'finalize.py'
f.write_text(f.read_text().replace('pawpatrol-s1-guide.mp4', out_name))

# render-offline.sh 也硬编码了输出名，同样需要参数化
r = dest / 'scripts' / 'render-offline.sh'
r.write_text(r.read_text().replace('out/pawpatrol-s1-guide.mp4', f'out/{out_name}'))

# 不要写 # 注释：注释会被 edge-tts 读进配音。写作提示放 EPISODE.md。
(dest / 'script.txt').write_text(
    '在这里写第一段的解说词。\n\n在这里写第二段的解说词。\n',
    encoding='utf-8',
)
(dest / 'EPISODE.md').write_text(
    f'# {title}\n\n- 标识: `{ident}`\n- 输出: `{out_name}`\n- 配音: zh-CN-XiaoyiNeural（语速由 video new --profile 写入，默认 child=-15%）\n\n'
    f'## 制作步骤\n'
    f'1. 编辑 `script.txt`：每段=一个镜头，用空行分隔。\n'
    f'2. 按新主题修改 `src/scenes/Scene*.tsx` 里的标题、卡片文案（模板里是第一季内容）。\n'
    f'3. 需要增减镜头时，同步改 `src/Composition.tsx` 的 COMPONENTS 数组与 scenes 数量。\n'
    f'4. 运行 `video build {dest}` 出片；只改画面/断网时 `video offline {dest}`。\n',
    encoding='utf-8',
)
print(f'OUT={out_name}')
PY

echo ""
echo "== 骨架已就绪 =="
echo "  工程目录: $DEST"
echo "  下一步:   编辑 $DEST/script.txt 与 src/scenes/，然后 bash $DEST/scripts/build.sh"

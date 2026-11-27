# 06 · 离线渲染与成本

## 核心边界

| 操作 | 断网 | 说明 |
|---|---|---|
| 渲染 MP4（画面、字幕、混音） | ✅ | Remotion + 本地浏览器 + 本地音频 |
| 调画面版式、颜色、动效 | ✅ | 改 `src/FullScene.tsx` / `board.ts` 后重跑 |
| 调 BGM 音量、淡入淡出 | ✅ | 改 `src/Composition.tsx` 的 `BGM_LEVEL` |
| 换 BGM 文件 | ✅ | 纯 Python 生成器在本地，改 `Audio src` |
| 改口播稿并重新配音 | ❌ | edge-tts 需联网，须先联网跑 `build` |
| 安装新依赖 | ❌ | 先 `video doctor`；PASS 就不要重装 |

## 一条命令

```bash
video offline /path/to/project
# 等价写法（不依赖 CLI）：
bash /path/to/project/scripts/render-offline.sh
```

以复盘片为例，脚本内部已经写死绝对路径，任意目录执行都可以：

```bash
bash /Users/a123/WorkBuddy/2026-11-25-10-23-46/retrospective-8min/scripts/render-offline.sh
python3 /Users/a123/WorkBuddy/2026-11-25-10-23-46/retrospective-8min/scripts/finalize.py
python3 /Users/a123/WorkBuddy/2026-11-25-10-23-46/retrospective-8min/scripts/cleanup.py
```

## 交接给其他 AI 工具

直接复制这段：

```text
进入 /path/to/project，
执行 bash scripts/render-offline.sh 完成 Remotion 离线渲染。
不要运行 python3 scripts/gen_audio.py，也不要调用 edge-tts（断网且会覆盖已有配音）。
渲染完成后运行 python3 scripts/finalize.py 校验 MP4，
再运行 python3 scripts/cleanup.py 清理临时文件。
最终成片路径：out/<name>.mp4。
```

如果对方愿意用统一 CLI：

```bash
source /path/to/video-toolkit/env.sh
video doctor            # 全部 PASS；PASS 就不要重复安装
video offline /path/to/project
```

## token 边界

- **消耗 token 的部分**：写脚本、设计镜头、给 AI 的 prompt、判断试听结果。
- **不消耗 token 的部分**：edge-tts 生成 WAV、本地 Python 合成 BGM、Remotion 渲染、调参、抽帧、清理缓存。

所以正确的做法是：**一次性把稿子和参数定下来，之后所有迭代都在本地完成。**

## 离线渲染脚本做了什么

1. 检查每段 `scene*.mp3`、BGM、时间轴和 `node_modules` 软链是否齐全。
2. `npx tsc --noEmit` 类型检查。
3. `npx remotion render ... --concurrency=4`。
4. `finalize.py` 校验 `ftyp / moov / mdat` 和时长。
5. `cleanup.py` 分批清 `.tmp`、`*.remotion-in-progress` 和检查图。

> 沙箱可能对批量删除有拦截。清理脚本用 `shutil.rmtree` 一次删除整个 `.tmp/`，比逐文件 `unlink` 更稳。

下一步：[07 · 故障排查](07-troubleshooting.md)。

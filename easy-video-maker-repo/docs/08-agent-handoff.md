# 08 · AI 协作入口

> 给任何新对话窗口 / 其他 AI 工具（如 DSH）的一页操作手册。先读本页，再动手。
> 目标：复用已装依赖和共享工具，**不要重复安装、不要重新找路径**。

## 1. 先加载环境

```bash
source /path/to/video-toolkit/env.sh
video doctor
```

`doctor` 输出 `PASS` 即依赖齐全。只有报 `MISSING` 才执行：

```bash
python3 -m pip install -r video-toolkit/requirements.txt
```

## 2. 常用命令

```bash
# 新工程：档位 child=-15% / five=+5% / adult=+15%
video new s7 "第 7 季观看指南" --profile child

# 改过 script.txt 后联网重建；只改画面时离线渲染
video build ../pawpatrol-s7
video offline ../pawpatrol-s7

# 原创 BGM，独立文件，不覆盖在用 BGM
video bgm ../pawpatrol-s7 --style choral

# 分析参考曲（只取风格参数，不复制旋律）
video analyze /path/to/reference.mp3 --format text

# 清理临时文件 / 打印共享路径
video clean ../pawpatrol-s7
video scripts
```

## 3. 必须遵守的创作规则

1. **脚本**：优先用用户给的本地 `script.rtf / script.txt`；注释不进配音；不手改自动生成的 `src/data/scenes.ts`。
2. **配音**：默认 `zh-CN-XiaoyiNeural`。儿童导览 `-15%`，5 分钟版 `+5%`，成人向 `+15%`；用户另有要求以用户为准。
3. **画面**：emoji + 抽象色块信息图；角色只做无对应关系的抽象马赛克；禁止官方 LOGO、角色剪影、原片画面。
4. **BGM**：官方/第三方音频只作参考，不进成片；原创、不采样、不变调；音量 8%–15%（默认 12%），首尾淡入淡出；每版独立输出 A/B。
5. **BGM prompt 优先级**：调性 > 听感来源（人声/器乐）> 编制 > 节奏动机 > 旋律。先分析再创作；pYIN 不可靠时以用户试听为准。
6. **离线 / token**：脚本生成后，本地渲染与调参 0 token；断网只能复用已生成音频。
7. **清理**：每轮渲染后跑 `video clean`；不要删除 `node_modules` 软链。
8. **版权**：不搬运官方角色/原片/主题曲；抽象马赛克不能和具体角色一一对应。

## 4. 不要做的事

- 不要因为"看起来没装"就重新 `pip install`；先 `video doctor`。
- 不要把第三方或官方主题曲塞进成片。
- 不要用系统 ffmpeg（没装也不需要）。
- 不要恢复 `/tmp` 里的旧分析文件；分析逻辑已固化在 `analyze_reference.py`。
- 不要重新配音已存在的段落；`gen_audio.py` 会复用非空音频。

## 5. 断网交接模板

复制下面整段给另一个 AI 工具：

```text
进入 <工程目录>，执行 bash scripts/render-offline.sh 完成 Remotion 离线渲染。
不要运行 python3 scripts/gen_audio.py，也不要调用 edge-tts。
渲染完成后运行 python3 scripts/finalize.py 校验 MP4，
再运行 python3 scripts/cleanup.py 清理。
最终成片路径：out/<name>.mp4。
```

## 6. 开工判定表

| 用户意图 | 动作 |
|---|---|
| 做下一条 / 做某主题 | `video new` → 写 `script.txt` → 改画面 → `video build` |
| 改现有这集的文案/画面/音色 | 按 [03 · 流水线详解](03-pipeline.md) 的定位表改对应文件 |
| 渲染报错 | 查 [07 · 故障排查](07-troubleshooting.md) |
| 断网出片 | `video offline <dir>` |
| 想知道有哪些文件 | 查 `README.md` 工程结构 |

下一步：[09 · 案例研究](09-case-study.md)。

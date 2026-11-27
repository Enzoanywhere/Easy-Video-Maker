# 03 · 流水线详解

## 数据怎么流动

```
script.txt  ──gen_audio.py──▶  sceneN.mp3 + sceneN.srt
                                   │
                                   └──▶  src/data/scenes.ts（每段 duration + start/end）

src/data/board.ts ─┐
sceneN.mp3 ────────┼──▶ Remotion Composition ──▶ MP4
bgm.wav ───────────┘
```

**唯一的手工输入是 `script.txt` 和画面数据。** `src/data/scenes.ts` 是生成物，永远不要手改——字幕时间轴来自 edge-tts 的 SRT。

## 步骤 1：脚本

`script.txt` 的约定：

- 每段 = 一个镜头，段与段之间**空一行**。
- 每段 1–3 句，约 35–60 字，对应 10–16 秒。
- 注释不要写进文件；`new-episode.sh` 已修正为不再生成 `#` 注释行。
- 数字写中文，避免 TTS 读错。
- 角色介绍类内容同时给中文旁白与英文口头禅原句。

## 步骤 2：配音与字幕

`gen_audio.py` 调用 edge-tts，对每段生成：

| 文件 | 内容 |
|---|---|
| `public/audio/sceneN.mp3` | 该段口播音频 |
| `public/audio/sceneN.srt` | 由语音边界生成的时间码字幕 |
| `src/data/scenes.ts` | 汇总的 `duration/start/end`，供 Remotion 排时间线 |

**防抖设计**：脚本会复用已存在的非空音频；edge-tts 偶发 `NoAudioReceived` 时重试 5 次。因此只补生成新增段落，不会重录已有内容。

## 步骤 3：BGM

`scripts/bgm/` 下七个纯 Python 生成器，用 `math/wave/struct/random` 与 `numpy/scipy` 合成 16bit PCM WAV。每个风格输出独立文件，不覆盖在用的 `bgm.wav`（`march` 档除外）。

混音在 `src/Composition.tsx`：

- 电平：`BGM_LEVEL = 0.12`（导览片）或 `0.10`（复盘片）
- 首尾淡入淡出：2–4 秒
- 片长超过 BGM 长度时循环播放，转场处不做硬切

## 步骤 4：画面

`src/FullScene.tsx` 提供版式，`src/data/board.ts` 提供每段内容：

| 版式 | 用途 |
|---|---|
| `hero` | 大数字 + 一句话主张 |
| `origin` | 时间线圆点 |
| `flow` | 三列流程图 |
| `screen` | 终端 / 文件树窗口 |
| `compare` | 左右对比 |
| `layers` | 三层金字塔 |
| `wave` | 波形 + 优先级阶梯 |
| `ending` | 大标题 + 成片网格 |
| `shot` | 真实截屏 PNG（`Img`） |
| `clip` | 真实成片画面（`OffthreadVideo` 静音、从指定帧裁剪） |

镜头数量变化时，同步更新 `board.ts` 与 `scenes.ts`（后者由配音脚本重新生成）。

## 步骤 5：渲染与校验

```bash
bash scripts/render-offline.sh
```

脚本内部顺序：

1. 检查 51/6/N 段 mp3、BGM、时间轴、`node_modules` 软链是否齐全
2. `npx tsc --noEmit` 类型检查
3. `npx remotion render ... --concurrency=4`
4. `finalize.py` 校验 `ftyp / moov / mdat` 与时长
5. 分批 `cleanup.py` 清 `.tmp`、`*.remotion-in-progress`、`check*.png`

沙箱环境下用 `NODE_OPTIONS="--require=$PWD/scripts/tmpdir-patch.cjs"` 把临时目录重定向到工程内 `.tmp/`，并吞掉无害的删除错误。

## CLI 命令速查

| 命令 | 作用 |
|---|---|
| `video doctor` | 检查依赖，PASS 就不重装 |
| `video new <id> "<标题>" --profile child` | 建新工程并写入语速档位 |
| `video build <dir>` | 联网重建配音 + 渲染 |
| `video offline <dir>` | 离线渲染，0 token |
| `video audio <dir>` | 只重生成配音/SRT/时间轴 |
| `video bgm <dir> --style choral` | 原创 BGM，独立文件 |
| `video analyze <音频> --format text` | 参考曲调性/听感/编制初筛 |
| `video clean <dir>` | 清缓存 |

## 工程结构模板

```
project/
├── script.txt                 # 口播稿（手工编辑）
├── src/
│   ├── index.ts / Root.tsx    # Remotion 入口与合成注册
│   ├── Composition.tsx        # 时间线 + 混音
│   ├── FullScene.tsx          # 版式渲染
│   ├── SubtitleOverlay.tsx    # 字幕
│   ├── theme.ts / lib.ts      # 色板与动效原语
│   └── data/
│       ├── scenes.ts          # 自动生成的时间轴
│       └── board.ts           # 每段画面内容
├── public/audio/              # mp3 / srt / bgm.wav
├── scripts/                   # gen_audio / render / finalize / cleanup
└── out/                       # 成片
```

下一步：[04 · 视觉系统](04-visual-system.md)。

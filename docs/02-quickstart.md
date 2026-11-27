# 02 · 快速上手

## 前置条件

| 依赖 | 版本 | 说明 |
|---|---|---|
| Python | 3.13 | `edge-tts` 生成配音；`numpy/scipy/librosa` 做音频分析与合成 |
| Node | 22 | Remotion 4 + React 19 渲染 |
| macOS | — | 使用系统自带 `afconvert` / `afinfo` 解码音频；**不需要系统 ffmpeg** |
| 磁盘 | 约 1.3 GB | 主要是 Remotion 无头浏览器；多个工程用软链共享 |

> 浏览器由 Remotion 管理。如果下载被拦截，直接指定已下载的 `chrome-headless-shell` 路径，见 [07 · 故障排查](07-troubleshooting.md)。

## 安装

```bash
python3 -m pip install -r video-toolkit/requirements.txt
```

依赖清单固定了验证过的版本：`edge-tts 7.3.1`、`mutagen 1.48.1`、`numpy 2.5.5`、`scipy 1.18.1`、`librosa 1.0.1`、`soundfile 0.14.0`、`numba 0.68.1`、`llvmlite 0.50.0`、`matplotlib 3.11.2`。

## 加载环境

```bash
source video-toolkit/env.sh
video doctor
```

`doctor` 输出 `PASS` 表示依赖齐全。**不要因为"看起来没装"就重复 pip install**。

### 迁移到自己的机器

`env.sh` 里几个变量写死了原作者的本机路径，按实际情况改：

| 变量 | 含义 | 新机器怎么填 |
|---|---|---|
| `WB_ROOT` | 工作区根目录 | 你的项目父目录绝对路径 |
| `WB_PYTHON_BIN` | Python 可执行文件所在目录 | `dirname "$(command -v python3)"` |
| `WB_NODE_MODULES` | 共享的 `node_modules` | 你安装 Remotion 的目录 |
| `WB_REMOTION_BROWSER` | 无头浏览器 | `WB_NODE_MODULES/.remotion/.../chrome-headless-shell` |
| `WB_TEMPLATE` | 模板工程 | 从 `pawpatrol-s1` 复制出的模板目录 |

## 第一条视频

```bash
# 1. 建工程：档位 child=-15% / five=+5% / adult=+15%
video new demo "我的第一条视频" --profile child

# 2. 编辑新工程 script.txt
#    每段 = 一个镜头；空行分隔；不要写 # 注释（会被配音）
#    数字写中文，例如「二十六集」而不是「26集」

# 3. 按主题改 src/scenes/ 里的标题与卡片文字

# 4. 出片（联网生成配音 + 本地渲染）
video build ../pawpatrol-demo
```

产物：`out/pawpatrol-demo-guide.mp4`。`build.sh` 会自动完成清理 → 配音 → BGM 检查 → 类型检查 → 渲染 → 校验 → 清理。

## 只改画面时

```bash
video offline ../pawpatrol-demo
```

`offline` 跳过联网配音，复用已有 mp3/SRT/时间轴，**断网可用、0 token**。若改了 `script.txt` 文案，必须先联网跑一次 `build`。

## 语速档位怎么选

| 档位 | 语速 | 场景 |
|---|---|---|
| `child` | `-15%` | 陪低龄孩子，家长需要边看边讲 |
| `five` | `+5%` | 5 分钟导览，信息密度中等 |
| `adult` | `+15%` | 成人向拆解，明快有激情 |

音色默认 `zh-CN-XiaoyiNeural`。也可以显式指定：`video new demo "标题" --voice zh-CN-YunyangNeural --rate +10%`。

## 验收清单

- [ ] `finalize.py` 打印 `has_ftyp / has_moov / has_mdat: True`，时长合理
- [ ] 抽帧目视：文字不溢出、字幕不遮挡、emoji 正常
- [ ] 画面没有官方角色、Logo、原片画面
- [ ] BGM 原创、未采样/变调；音量 8%–15%，首尾淡入淡出
- [ ] `video clean <工程目录>` 已执行，无 `.tmp/`、无 in-progress 视频、无 check PNG

下一步：[03 · 流水线详解](03-pipeline.md)。

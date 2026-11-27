# 真实截屏示例

这 8 张 PNG 来自复盘片第 39–47 段，内容全部是本工作区真实运行留下的痕迹：

| 文件 | 内容 |
|---|---|
| `evidence-doctor.png` | `video doctor` 全部 PASS 的终端输出 |
| `evidence-files.png` | 工程目录与真实文件修改时间 |
| `evidence-videos.png` | 脚本直读 10 条 MP4 的时长与体积 |
| `evidence-srt.png` | 自动生成的 SRT 字幕片段 |
| `evidence-bgms.png` | 7 版原创 BGM 文件名 |
| `evidence-wave.png` | 复盘片 BGM 的真实波形 |
| `evidence-workflow.png` | WORKFLOW.md 文档页面 |
| `evidence-help.png` | `video --help` 输出 |

## 为什么是 `.b64`

GitHub 的远程写入接口只接受文本，无法直接上传二进制 PNG。因此这里以标准 base64 文本存档（`*.png.b64`），内容与原 PNG 完全一致。

一键还原：

```bash
python3 examples/evidence/decode.py
# 输出到当前目录的 evidence/ 下
```

或单文件：

```bash
base64 -D -i evidence-doctor.png.b64 -o evidence-doctor.png
```

## 重新生成

原始渲染脚本在 `examples/gen_evidence.py`，采集的数据样例在 `examples/evidence-data.sample.json`。它用 Pillow 把真实数据渲染为统一风格截屏：终端深色窗、文档浅色窗、中文用 STHeiti 回退。

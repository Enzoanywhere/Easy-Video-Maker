# 视频流水线统一环境。用 source 加载，不要直接执行。
# 用法：source /Users/a123/WorkBuddy/2026-11-25-10-23-46/video-toolkit/env.sh

export WB_ROOT="/Users/a123/WorkBuddy/2026-11-25-10-23-46"
export WB_TOOLKIT="$WB_ROOT/video-toolkit"
export WB_TEMPLATE="$WB_ROOT/pawpatrol-s1"

export WB_PYTHON_BIN="/Users/a123/.workbuddy/binaries/python/versions/3.13.12/bin"
export WB_PYTHON="$WB_PYTHON_BIN/python3"
export PATH="$WB_PYTHON_BIN:$WB_TOOLKIT/bin:$PATH"

export WB_NODE_MODULES="$WB_ROOT/workbuddy-intro/node_modules"
export WB_REMOTION_BROWSER="$WB_NODE_MODULES/.remotion/chrome-headless-shell/158.0.8127.2-remotion-v3/mac-arm64/chrome-headless-shell-mac-arm64/chrome-headless-shell"

# 默认配音参数；具体档位由 video new --profile 写入工程，不靠这里覆盖。
export WB_VOICE="${WB_VOICE:-zh-CN-XiaoyiNeural}"
export WB_BGM_LEVEL="${WB_BGM_LEVEL:-0.12}"

# 说明：ffmpeg 不需要；Mac 自带 afconvert / afinfo 足够做音频解码与元信息读取。

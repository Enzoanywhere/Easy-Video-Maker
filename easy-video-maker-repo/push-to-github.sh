#!/usr/bin/env bash
# 一键把本目录的技术文档推送到 GitHub。
# 用途：绕过 WorkBuddy GitHub 连接器的 contents:write 权限限制，使用你本机已登录的 git 凭据。
set -euo pipefail

REPO_URL="https://github.com/Enzoanywhere/Easy-Video-Maker.git"
BRANCH="main"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git init -b "$BRANCH"
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "$REPO_URL"
else
  git remote set-url origin "$REPO_URL"
fi

git add .
git -c user.name="Enzoanywhere" -c user.email="enzoanywhere@users.noreply.github.com" \
  commit -m "docs: publish Easy Video Maker workflow documentation" || true

git branch -M "$BRANCH"
git push -u origin "$BRANCH"

echo ""
echo "已推送: $REPO_URL"

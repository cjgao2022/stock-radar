#!/usr/bin/env bash
# Stock-Radar 一键启动脚本
# 用法：./start.sh   （首次需 chmod +x start.sh）
set -e

cd "$(dirname "$0")"

# 首次运行自动创建虚拟环境并安装依赖
if [ ! -d ".venv" ]; then
  echo "==> 未检测到 .venv，正在创建虚拟环境并安装依赖..."
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -U pip
  pip install -r requirements.txt
else
  source .venv/bin/activate
fi

echo "==> 启动 Stock-Radar：http://127.0.0.1:8000/"
exec uvicorn main:app --reload --host 127.0.0.1 --port 8000

#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0
# Copyright (C) 2026 wentywenty


# 定义基础目录（自动识别当前用户家目录下的绝对路径）
BASE_DIR="$HOME/actions"
SESSION_NAME="github-runners"

# 检查 tmux 会话是否已经存在
tmux has-session -t $SESSION_NAME 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "\033[33m[!] 会话 '$SESSION_NAME' 已经在运行中。请先运行 ./stop_runners.sh 关闭它们。\033[0m"
    exit 1
fi

echo -e "\033[32m[*] 开始无中生有，构建 4 路自建 Runner 阵列...\033[0m"

# 1. 创建 tmux 虚拟会话并拉起第 1 个：roboparty_bms
cd "$BASE_DIR/roboparty_bms" && tmux new-session -d -s $SESSION_NAME -n "BMS" "./run.sh"
echo -e "\033[32m[✓] 成功拉起 -> roboparty_bms\033[0m"

# 2. 派生新窗口拉起第 2 个：roboparty_imu
cd "$BASE_DIR/roboparty_imu" && tmux new-window -t $SESSION_NAME -n "IMU" "./run.sh"
echo -e "\033[32m[✓] 成功拉起 -> roboparty_imu\033[0m"

# 3. 派生新窗口拉起第 3 个：roboparty_inference
cd "$BASE_DIR/roboparty_inference" && tmux new-window -t $SESSION_NAME -n "Inference" "./run.sh"
echo -e "\033[32m[✓] 成功拉起 -> roboparty_inference\033[0m"

# 4. 派生新窗口拉起第 4 个：roboparty_motors
cd "$BASE_DIR/roboparty_motors" && tmux new-window -t $SESSION_NAME -n "Motors" "./run.sh"
echo -e "\033[32m[✓] 成功拉起 -> roboparty_motors\033[0m"

echo -e "\033[34m--------------------------------------------------------\033[0m"
echo -e "\033[32m[🎉] 4 个自建物理机全部进入后台狂飙状态！\033[0m"
echo -e "\033[36m👉 提示：输入 'tmux a -t github-runners' 可随时切进后台看它们的实时 Log\033[0m"
echo -e "\033[34m--------------------------------------------------------\033[0m"

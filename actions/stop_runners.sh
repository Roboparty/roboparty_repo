#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0
# Copyright (C) 2026 wentywenty


SESSION_NAME="github-runners"

tmux has-session -t $SESSION_NAME 2>/dev/null

if [ $? -eq 0 ]; then
    # 暴力但优雅地直接 kill 掉整个虚拟会话，里面挂载的 4 个 run.sh 会随之安全退出
    tmux kill-session -t $SESSION_NAME
    echo -e "\033[33m[OFF] 4 路自建 Runner 已全部安全下线，后台已清空。\033[0m"
else
    echo -e "\033[31m[!] 后台没有发现正在运行的 '$SESSION_NAME' 会话。\033[0m"
fi

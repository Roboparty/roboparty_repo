#!/bin/bash

# SPDX-License-Identifier: GPL-3.0
# Copyright (C) 2026 wentywenty

#=================================================
# APT 源服务端 Github Action 机器人注入脚本 v1.0
# 用于静默处理 /srv/apt-incoming 目录中的所有 deb 包
# 无需任何交互界面，直接由 Github Action 的流水线B触发
#=================================================

APT_DIR="/srv/apt"
INCOMING_DIR="/srv/apt-incoming"
SUITES=("common" "robopi1" "robopi2" "robopi3" "x86")

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
ROUTING="$REPO_DIR/routing.yaml"
ROUTE_DEBS="$SCRIPT_DIR/route_debs.py"

export PATH=$PATH:/usr/bin:/bin

# 检查必备工具
command -v reprepro &>/dev/null || { echo "❌ [Bot] 缺少必备工具: reprepro"; exit 1; }

if [ ! -d "$INCOMING_DIR" ]; then
    echo "⚠️ [Bot] 找不到 incoming 目录: $INCOMING_DIR，跳过注入。"
    exit 0
fi

echo "========================================"
echo " 🤖 RoboParty APT 自动注入机器人启动"
echo " 时间: $(date)"
echo "========================================"

for suite in "${SUITES[@]}"; do
    expected=$(python3 "$ROUTE_DEBS" --print-expected "$ROUTING" "$suite" 2>/dev/null)
    if [ -n "$expected" ]; then
        current=$(reprepro -b "$APT_DIR" list "$suite" 2>/dev/null | sed 's/^[^:]*: //' | awk '{print $1}' | sort -u)
        if [ -n "$current" ]; then
            stale=$(comm -23 <(echo "$current") <(echo "$expected"))
            if [ -n "$stale" ]; then
                while IFS= read -r pkg; do
                    [ -z "$pkg" ] && continue
                    echo "🧹 清理残留包: $pkg ($suite)"
                    reprepro -b "$APT_DIR" remove "$suite" "$pkg" >/dev/null 2>&1
                done <<< "$stale"
            fi
        fi
    fi

    shopt -s nullglob
    debs=("$INCOMING_DIR/$suite"/*.deb)
    shopt -u nullglob
    
    if [ ${#debs[@]} -gt 0 ]; then
        echo "📦 发现 [$suite] 源有 ${#debs[@]} 个包裹，正在开始静默注入..."
        for deb in "${debs[@]}"; do
            pkg_name=$(dpkg-deb -f "$deb" Package 2>/dev/null)
            pkg_arch=$(dpkg-deb -f "$deb" Architecture 2>/dev/null)
            echo "👉 [注入] $pkg_name ($pkg_arch) : $(basename "$deb")"
            
            # 先卸载特定架构旧包防止Hash冲突
            if [ -n "$pkg_arch" ] && [ "$pkg_arch" != "all" ]; then
                reprepro -b "$APT_DIR" removefilter "$suite" "Package (== $pkg_name), Architecture (== $pkg_arch)" >/dev/null 2>&1
            else
                reprepro -b "$APT_DIR" remove "$suite" "$pkg_name" >/dev/null 2>&1
            fi
            
            # 注入新包并清理
            if reprepro -b "$APT_DIR" includedeb "$suite" "$deb"; then
                rm -f "$deb"
                echo "   ✅ 入库成功并已清理缓存: $(basename "$deb")"
            else
                echo "   ❌ 入库失败，已保留文件: $(basename "$deb")"
            fi
        done
    fi
done

# 清理无引用包
echo "🧹 正在执行 deleteunreferenced 回收无效空间..."
reprepro -b "$APT_DIR" deleteunreferenced >/dev/null 2>&1

echo "🎉 自动入库流程执行完毕！"

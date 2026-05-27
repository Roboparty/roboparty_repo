#!/usr/bin/env python3

# SPDX-License-Identifier: GPL-3.0
# Copyright (C) 2026 wentywenty

"""route_debs.py - 下载所有 repo 的 deb，集中后按 routing.yaml 分拣到 incoming/<suite>/"""

import fnmatch
import json
import os
import shutil
import subprocess
import sys

import yaml

TMP_DIR = 'tmp_debs'
MANIFEST_FILE = 'manifest.json'


def download_all(repos):
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)
    os.makedirs(TMP_DIR)

    for repo in repos:
        print(f'📥 拉取 {repo} ...')
        try:
            ret = subprocess.run(
                ['gh', 'release', 'download', '-R', repo, '-p', '*.deb', '-D', TMP_DIR],
                capture_output=True, text=True, timeout=300,
            )
            if ret.returncode != 0:
                print(f'   ⚠️ 无 release 或下载失败，跳过。')
        except subprocess.TimeoutExpired:
            print(f'   ⚠️ 下载超时（300s），跳过。')


def route_all(routing, incoming):
    suites = list(routing.keys())
    for s in suites:
        os.makedirs(os.path.join(incoming, s), exist_ok=True)

    debs = sorted(f for f in os.listdir(TMP_DIR) if f.endswith('.deb'))
    if not debs:
        print('(无 .deb 包)')
        return []

    manifest = []

    for basename in debs:
        src = os.path.join(TMP_DIR, basename)
        dests = []

        for suite in suites:
            for entry in routing[suite]:
                p = entry['pattern']
                ver = entry.get('version', 'auto')
                if fnmatch.fnmatch(basename, p):
                    if ver != 'auto' and ver not in basename:
                        continue
                    if suite not in dests:
                        dests.append(suite)
                    break

        if not dests:
            dests.append('common')
            print(f'   ⚠️ 无匹配规则，落入 common: {basename}')

        for s in dests:
            print(f'   📍 {basename} -> {s}')
            shutil.copy2(src, os.path.join(incoming, s, basename))

        manifest.append({'deb': basename, 'suites': dests})

    return manifest


def main():
    if len(sys.argv) < 3:
        print('Usage: route_debs.py <routing.yaml> <incoming_dir>')
        sys.exit(1)

    config_path = sys.argv[1]
    incoming = sys.argv[2]

    with open(config_path) as f:
        config = yaml.safe_load(f)

    repos = config['repos']
    routing = config['routing']

    print('=' * 50)
    print('  阶段 1: 下载所有仓库的 release .deb')
    print('=' * 50)
    download_all(repos)

    print()
    print('=' * 50)
    print('  阶段 2: 按 routing.yaml 分拣')
    print('=' * 50)
    manifest = route_all(routing, incoming)

    shutil.rmtree(TMP_DIR, ignore_errors=True)

    manifest_path = os.path.join(incoming, MANIFEST_FILE)
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f'\n✅ 分拣完成，共 {len(manifest)} 个包，清单: {manifest_path}')


if __name__ == '__main__':
    main()
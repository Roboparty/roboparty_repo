# roboparty_apt_tools

RoboParty APT 源自动化管理仓库。当各个子仓库发版后，由本仓库的 GitHub Actions 将 `.deb` 包自动同步到公网 APT 服务器并入库。

---

## 第一步：发布新版本

在子仓库（如 `roboparty_motors`）中执行：

```bash
# 1. 更新 changelog
dch -v 2.1.1-1 "一些新功能和修复"

# 2. (可选) 同步 package.xml 版本号
sed -i 's/<version>.*<\/version>/<version>2.1.1<\/version>/' package.xml

# 3. 提交代码
git add .
git commit -m "Bump version to 2.1.1"

# 4. 打 tag 并推送
git tag v2.1.1
git push origin HEAD --tags
```

推送到 GitHub 后，子仓库自己的 GitHub Actions 会：

- 触发 `ubuntu-22.04` 和 `ubuntu-22.04-arm` 构建实例
- 通过 `dpkg-buildpackage` 自动编译出 `.deb`
- 检测到 `v2.1.1` tag 后自动创建 Release 并将 `.deb` 挂载到 Release Assets

### 仅修改打包逻辑（不打 tag，不发 Release）

如果只是修了 `debian/control`、`debian/rules` 等打包脚本，源代码版本没变：

```bash
dch -v 2.1.0-2 "Fix build dependencies in control file"
git add debian/
git commit -m "Fix debian build scripts"
git push origin HEAD
```

Action 会被触发生成 `.deb` Artifact 供你测试，但因为没打 tag，不会发布新 Release。

---

## 第二步：运行 Action 同步到 APT 服务器

当子仓库的 Release 就绪后，本仓库 (`roboparty_apt_tools`) 的 GitHub Actions 负责将包搬运到公网 APT 服务器。

### 流水线 A：拉取并分拣

编辑 `routing.yaml`，确认新仓库或新包名已在路由规则中，然后推送：

```bash
git add routing.yaml
git commit -m "Update routing for v2.1.1"
git push origin HEAD
```

推送后自动触发**流水线 A** (`1-sync-apps.yml`)：

1. 在自建 Runner（RK3588 物理机）上运行 `scripts/route_debs.py`
2. 根据 `routing.yaml` 中的 `repos` 列表，通过 `gh release download` 拉取所有仓库最新 Release 的 `.deb`
3. 按 `routing` 规则分拣到 `incoming/<suite>/` 目录
4. 通过 rsync 将 `incoming/` 同步到公网服务器 `/srv/apt-incoming/`

### 流水线 B：入库

流水线 A 完成后自动接力触发**流水线 B** (`2-process-apt.yml`)，也可在 GitHub Actions 页面手动触发：

1. SSH 连接到公网 APT 服务器
2. 将 `bot_inject.sh` 推送到服务器并执行
3. `bot_inject.sh` 遍历 `/srv/apt-incoming/` 下各 suite 的 `.deb`，调用 `reprepro includedeb` 入库
4. 完成后执行 `deleteunreferenced` 清理残留

### 自建 Runner 管理

自建 Runner 运行在 RK3588 物理机上，通过 tmux 管理：

```bash
./actions/start_runners.sh    # 启动所有 Runner
./actions/stop_runners.sh     # 关闭所有 Runner
tmux a -t github-runners      # 查看实时日志
```

### routing.yaml 配置

```yaml
repos:                          # 要下载的 GitHub 仓库
  - wentywenty/roboparty_base
  - wentywenty/roboparty_motors
  # ...

routing:
  common:
    - pattern: "roboparty-motors_*_arm64.deb"        # 包名 glob，* 为通配符
    - pattern: "ethercat-igh_*-rockchip-rk3588_arm64.deb"
      version: 1.7.1-6.1.99-rt36                   # 锁定版本（可选）
```

### 辅助脚本

| 脚本 | 说明 |
|------|------|
| `scripts/route_debs.py` | 下载所有 repo 的 deb，按 routing.yaml 分拣 |
| `bot_inject.sh` | 服务器端 reprepro 入库机器人 |
| `sync_from_gh.sh` | 桌面端 TUI 工具：手动从 Release 拉包 → rsync 到服务器 |
| `apt_server_sync.sh` | 服务器端 TUI 工具：手动拉取/注入/清理 |
| `check_v8.sh` | 扫描目录中 .so/.a/ELF 的 ARM v8.3+ 非法指令 |

### 环境配置

`env` 文件（已 gitignore）包含代理和服务器连接信息，`sync_from_gh.sh` 启动时会自动 source。

---

## 第三步：导入 APT 源

在你的机器（x86 或 arm64）上执行：

```bash
# 1. 下载 GPG 钥匙
sudo curl -fsSL "http://apt.roboparty.com/roboparty.gpg" | \
  sudo gpg --dearmor -o /usr/share/keyrings/roboparty-archive-keyring.gpg
sudo chmod 644 /usr/share/keyrings/roboparty-archive-keyring.gpg

# 2. 写入源列表（x86 机器用 amd64，arm64 机器改成 arm64）
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/roboparty-archive-keyring.gpg] http://apt.roboparty.com common main" | \
  sudo tee /etc/apt/sources.list.d/roboparty.list

# 3. 刷新并安装
sudo apt-get update
sudo apt-get install roboparty-motors
```

可用 suite：
- `common` — 通用包（所有架构）
- `robopi1` — RoboPi1 专用内核
- `robopi2` — RoboPi2 专用内核
- `robopi3` — RoboPi3 专用内核
- `x86` — x86 专用包

# roboparty_repo

RoboParty APT 源自动化管理仓库。

---

## 第一步：子仓库发版

在子仓库（如 `roboparty_motors`）中：

```bash
# 1. 更新 changelog
dch -v 2.1.1-1 "新功能和修复"

# 2. 提交并打 tag
git add .
git commit -m "Bump version to 2.1.1"
git tag v2.1.1
git push origin HEAD --tags
```

推送后子仓库自己的 Actions 会编译出 `.deb` 并创建 GitHub Release。

> **注意**：CI 会校验 tag（如 `v2.1.1`）与 `debian/changelog` 中的版本号是否一致，不一致则构建直接失败。必须先用 `dch` 更新 changelog 再打 tag。

### 仅修改打包脚本（不打 tag）

如果只改了 `debian/control`、`debian/rules` 等，源代码版本不变：

```bash
dch -v 2.1.0-2 "Fix build deps"
git add debian/
git commit -m "Fix debian build scripts"
git push origin HEAD
```

Actions 会生成 `.deb` Artifact 供测试，但不会发布 Release。

---

## 第二步：同步到 APT 源

在 APT 服务器上手动执行脚本，从各仓库 Release 拉包并入库。

### 流程

```bash
cd /path/to/roboparty_repo
export GH_TOKEN=<GitHub Personal Access Token>
python3 scripts/route_debs.py routing.yaml /srv/apt-incoming/
bash scripts/bot_inject.sh
```

```
route_debs.py  → 从 GitHub Release 下载 .deb，按 routing.yaml 分拣到 /srv/apt-incoming/
bot_inject.sh  → 调用 reprepro 将 /srv/apt-incoming/ 入库到 /srv/apt/
```

服务器重建详见 [server.md](server.md)。

### routing.yaml 配置

```yaml
repos:                        # 要下载的 GitHub 仓库
  - wentywenty/roboparty_motors
  - Roboparty/roboparty_base

routing:
  common:                     # suite 名称
    - pattern: "roboparty-motors_*_arm64.deb"
    - pattern: "ethercat-igh_*-rockchip-rk3588_arm64.deb"
      version: 1.7.1-6.1.99-rt36   # 锁定版本（可选，默认拉最新）
```

---

## 第三步：用户安装

```bash
# 1. 导入 GPG 公钥
sudo curl -fsSL "https://apt.roboparty.com/roboparty.gpg" | \
  sudo gpg --dearmor --yes -o /usr/share/keyrings/roboparty-archive-keyring.gpg
sudo chmod 644 /usr/share/keyrings/roboparty-archive-keyring.gpg

# 2. 添加源（x86 用 amd64，arm64 改成 arm64）
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/roboparty-archive-keyring.gpg] https://apt.roboparty.com common main" | \
  sudo tee /etc/apt/sources.list.d/roboparty.list

# 3. 安装
sudo apt-get update
sudo apt-get install roboparty-motors
```

可用 suite：`common` / `robopi1` / `robopi2` / `robopi3` / `x86`

---

## 编译看板

`dashboard.yml` 每小时拉取 routing.yaml 中所有仓库的最新 Actions 状态。

所有仓库均为 public，无需额外配置 token。

---

## 文件结构

```
roboparty_repo/
├── .github/workflows/
│   ├── sync-and-inject.yml                  # APT 入库 workflow
│   └── dashboard.yml                        # 编译状态看板
├── scripts/
│   ├── route_debs.py                        # 下载并分拣 deb
│   ├── bot_inject.sh                        # reprepro 入库脚本
│   └── dashboard.py                         # 看板脚本
├── routing.yaml                             # 仓库及路由规则
├── distributions                            # reprepro 仓库配置（参考用）
├── server.md                                # APT 服务器重建指南
└── env                                      # 代理等环境变量（gitignore）
```

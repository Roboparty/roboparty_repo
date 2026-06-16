# roboparty APT 服务器重建指南

## 前提条件

- 本机就是 APT 服务器
- 需要一个 GitHub Personal Access Token（classic，`repo` 或 `public_repo` scope）
- 代码仓库在 `/home/robo/roboto/roboparty_repo/`

---

## 1. 安装系统依赖

```bash
sudo apt-get update
sudo apt-get install -y reprepro nginx python3-pip
pip install pyyaml
```

确认 `gh` CLI 是否已装：

```bash
gh --version
```

没装的话：

```bash
type -p curl >/dev/null || sudo apt-get install curl -y
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod 644 /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt-get update
sudo apt-get install gh -y
```

---

## 2. 生成新 GPG 密钥

```bash
gpg --batch --gen-key <<'EOF'
Key-Type: RSA
Key-Length: 4096
Name-Real: RoboParty APT Repository
Name-Email: apt@roboparty.com
Expire-Date: 0
%no-protection
EOF
```

记下 Key ID（下一步要用）：

```bash
gpg --list-keys --keyid-format LONG "RoboParty APT Repository"
```

输出示例：

```
pub   rsa4096/ABCDEF1234567890 2026-06-17 [SC]
```

其中 `ABCDEF1234567890` 就是 Key ID。这个只是示例，别傻乎乎的写上去。。。。。

---

## 3. 创建 reprepro 仓库配置

```bash
sudo mkdir -p /srv/apt/conf
```

写入 `/srv/apt/conf/distributions`，**把所有的 `<KEY_ID>` 替换为步骤2拿到的 Key ID**：
这个只是示例，别傻乎乎的写上去。。。。。
```
Origin: RoboParty
Label: RoboParty APT Repository
Codename: common
Architectures: amd64 arm64 source
Components: main
Description: RoboParty common packages
SignWith: <KEY_ID>

Origin: RoboParty
Label: RoboParty APT Repository
Codename: robopi1
Architectures: amd64 arm64 source
Components: main
Description: RoboParty RoboPi1 packages
SignWith: <KEY_ID>

Origin: RoboParty
Label: RoboParty APT Repository
Codename: robopi2
Architectures: amd64 arm64 source
Components: main
Description: RoboParty RoboPi2 packages
SignWith: <KEY_ID>

Origin: RoboParty
Label: RoboParty APT Repository
Codename: robopi3
Architectures: amd64 arm64 source
Components: main
Description: RoboParty RoboPi3 packages
SignWith: <KEY_ID>

Origin: RoboParty
Label: RoboParty APT Repository
Codename: x86
Architectures: amd64 source
Components: main
Description: RoboParty x86 packages
SignWith: <KEY_ID>
```

可用一条命令完成（这个只是示例，别傻乎乎的写上去。。。。。在正确位置执行，`<KEY_ID>` 需提前替换）：

```bash
sudo tee /srv/apt/conf/distributions > /dev/null <<'EOF'
Origin: RoboParty
Label: RoboParty APT Repository
Codename: common
Architectures: amd64 arm64 source
Components: main
Description: RoboParty common packages
SignWith: <KEY_ID>

Origin: RoboParty
Label: RoboParty APT Repository
Codename: robopi1
Architectures: amd64 arm64 source
Components: main
Description: RoboParty RoboPi1 packages
SignWith: <KEY_ID>

Origin: RoboParty
Label: RoboParty APT Repository
Codename: robopi2
Architectures: amd64 arm64 source
Components: main
Description: RoboParty RoboPi2 packages
SignWith: <KEY_ID>

Origin: RoboParty
Label: RoboParty APT Repository
Codename: robopi3
Architectures: amd64 arm64 source
Components: main
Description: RoboParty RoboPi3 packages
SignWith: <KEY_ID>

Origin: RoboParty
Label: RoboParty APT Repository
Codename: x86
Architectures: amd64 source
Components: main
Description: RoboParty x86 packages
SignWith: <KEY_ID>
EOF
```

---

## 4. 创建 incoming 目录

```bash
sudo mkdir -p /srv/apt-incoming/{common,robopi1,robopi2,robopi3,x86}
sudo chown -R $(whoami):$(whoami) /srv/apt /srv/apt-incoming
```

---

## 5. 拉取所有仓库的 deb 包

```bash
export GH_TOKEN=<你的 GitHub token>
cd /home/robo/roboto/roboparty_repo
python3 scripts/route_debs.py routing.yaml /srv/apt-incoming/
```

脚本会：
- 遍历 `routing.yaml` 中的 15 个 GitHub 仓库
- 从每个仓库的 GitHub Release 下载所有 `.deb` 文件到 `tmp_debs/`
- 按 `routing.yaml` 的 pattern 规则分拣到 `/srv/apt-incoming/<suite>/`
- 生成 `/srv/apt-incoming/manifest.json`
- 清理 `tmp_debs/`

---

## 6. 注入到 APT 仓库

```bash
bash scripts/bot_inject.sh
```

脚本会逐 suite 遍历 incoming 目录，调用 `reprepro` 入库（先 remove 旧版本避免 hash 冲突，再 includedeb）。

---

## 7. 导出 GPG 公钥

```bash
sudo mkdir -p /var/www/html
gpg --export -a "RoboParty APT Repository" | sudo tee /var/www/html/roboparty.gpg > /dev/null
```

---

## 8. 配置 nginx

写入 `/etc/nginx/sites-available/apt`：

```nginx
server {
    listen 80;
    server_name apt.roboparty.com;

    root /srv/apt;
    autoindex on;

    location /roboparty.gpg {
        root /var/www/html;
    }
}
```

启用：

```bash
sudo ln -sf /etc/nginx/sites-available/apt /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

---

## 9. 验证

```bash
# 检查 reprepro 仓库状态
reprepro -b /srv/apt list common | head -20

# 测试 nginx 可访问
curl -I http://apt.roboparty.com/dists/common/Release

# 模拟用户端安装
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/roboparty-archive-keyring.gpg] http://apt.roboparty.com common main" | \
  sudo tee /etc/apt/sources.list.d/roboparty.list
sudo apt-get update
```

---

## ⚠️ GPG 公钥变更通知

GPG 私钥已丢失并重新生成，**所有用户端**必须更新公钥：

```bash
sudo curl -fsSL "http://apt.roboparty.com/roboparty.gpg" | \
  sudo gpg --dearmor -o /usr/share/keyrings/roboparty-archive-keyring.gpg
sudo chmod 644 /usr/share/keyrings/roboparty-archive-keyring.gpg
```

否则 `apt-get update` 会报 `NO_PUBKEY` 错误。

---

## 后续维护

### 新包上线

1. 子仓库打 tag →_push → GitHub Actions 编译出 `.deb` 并创建 Release
2. 在本服务器上执行：

```bash
cd /home/robo/roboto/roboparty_repo
export GH_TOKEN=<token>
python3 scripts/route_debs.py routing.yaml /srv/apt-incoming/
bash scripts/bot_inject.sh
```

### 添加新仓库到 APT 源

1. 编辑 `routing.yaml`，在 `repos:` 下追加仓库 full name，在对应 suite 下添加 pattern
2. 执行步骤 5-6

### 只注入已有包（不从 GitHub 重新下载）

```bash
bash scripts/bot_inject.sh
```

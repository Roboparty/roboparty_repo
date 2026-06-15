**当你要发布新版本 2.1.1 时：**

1. **更新 Changelog（记录版本号和改动）：**
   ```bash
   dch -v 2.1.1-1 "一些新功能和修复"
   后面可以加
   dch -D stable ""
   ```
   （此时 `debian/changelog` 的顶端变成了 2.1.1-1）

2. **如果想在 ROS2 生态里也同步版本，顺手改一下（可选）：**
   把 package.xml 里的 `<version>` 改成 `2.1.1`

3. **提交代码：**
   ```bash
   git add .
   git commit -m "Bump version to 2.1.1"
   ```

4. **打 Git 标签：**
   我们要发 2.1.1 版了，打上名字为 `v2.1.1`（或者你喜欢的任何格式，比如 `motors-v2.1.1`，只要你记住就好）的标签：
   ```bash
   git tag v2.1.1
   ```

5. **推送到 GitHub（注意一定要带上 tags）：**
   ```bash
    git push origin HEAD --tags
   ```

相比于直接 git tag v1.2.0，老鸟更喜欢加 -a 和 -m，这样会在 Git 历史里永久记录是谁、在什么时候、因为什么发的这个版本：

Bash
git tag -a v1.2.0 -m "Apply GPL-v3 license"
2. 单独把这个标签推上去

Bash
git push origin v1.2.0

当推送到 GitHub 后：
- **触发构建**：GitHub Actions 检测到代码 Push，马上拉起 `ubuntu-22.04` 和 `ubuntu-22.04-arm` 的构建实例。
- **自动编译**：通过 `dpkg-buildpackage` 自动构建。
- **构建 Artifacts**：按照新版本号 `2.1.1` 给 `.deb` 文件命名，变成 `roboto-motors-v2.1.1-amd64` 供下载。
- **自动 Release**：因为它检测到了你这次推送带有一个叫 `v2.1.1` 的 tag，它会自动在 GitHub 右侧建一个 `v2.1.1` 的 Release 发版区，并把两个架构的 `.deb` 包挂靠在里面。
在那里！

是不是极其优雅连贯？这就是现代开源库的发版标准流程。


如果你**只是修改了打包逻辑**（比如改了 `debian/control`、`debian/rules` 或 `build-deb.yml`），而**程序的源代码功能本身并没有改变**。

在这种情况下，有两种做法：

### 做法一：常规打包修正（推荐，不发 Release）

既然你的开源程序本身没升级（仍然是 `2.1.0`），你**不需要**发一个新的 GitHub Release，也不需要去打 `v2.1.1` 的 Git Tag。

但是，因为打包逻辑变了，你应该更新 Debian 的“修订号”（Revision Number）。
Debian 的版本号规范是 `<上游版本>-<Debian打包修订号>`，比如 `2.1.0-1`。如果你修改了由于打包原因导致的小 bug，你应该：

1. **更新 debian 记录：**
   ```bash
   dch -v 2.1.0-2 "Fix build dependencies in control file"
   ```
   *注意这里上游版本还是 2.1.0，但 Debian 修订号变成了 2*。

2. **提交并推送代码（不打 tag）：**
   ```bash
   git add debian/
   git commit -m "Fix debian build scripts"
   git push origin HEAD
   ```

**结果：** GitHub Actions 被触发，编译生成 `roboto-motors-v2.1.0-amd64` 的 Artifact 构件**供你测试**，但因为没有 tag，**不会发布新的 Release**。

---

### 做法二：强制发一个修复版 Release（如果你想替换掉之前的缺陷包）

如果之前的打包逻辑有严重错误，导致之前发出去的 `v2.1.0` 根本不能用，你希望用户下载到一个全新的好包。

你可以直接顺水推舟，把这当成一个正式的补丁版本发布：

1. `dch -v 2.1.1-1 "Fix debian build packaging"`
2. 改 package.xml 为 2.1.1
3. 提交、`git tag v2.1.1`、最后 `git push origin HEAD --tags`。
这样就会发一个新的 Release。

大多数情况下，如果只是自己修修建建打包脚本，用**做法一**更新 `-2` 修订号并在 Action 的 Artifacts 里下载下来测试，是最干净合理的做法。等到积攒了代码改动后再发全新的 Release。


robo@roboa100:~/roboto/roboto_example$ dch -v 1.0.2-1 "Update standard deb package"
robo@roboa100:~/roboto/roboto_example$ dch -D stable ""
robo@roboa100:~/roboto/roboto_example$ git add .
robo@roboa100:~/roboto/roboto_example$ git commit -m "Update standard deb package"
[master 29b86c9] Update standard deb package
 8 files changed, 52 insertions(+), 60 deletions(-)
 delete mode 100755 build_deb.sh
 create mode 100644 debian/changelog
 delete mode 100644 debian/conffiles
 create mode 100644 debian/install
 create mode 100755 debian/rules
robo@roboa100:~/roboto/roboto_example$ git tag v1.0.2
robo@roboa100:~/roboto/roboto_example$ git push origin v1.0.2
Enumerating objects: 18, done.
Counting objects: 100% (18/18), done.
Delta compression using up to 128 threads
Compressing objects: 100% (9/9), done.
Writing objects: 100% (11/11), 1.77 KiB | 1.77 MiB/s, done.
Total 11 (delta 1), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (1/1), completed with 1 local object.
To https://github.com/wentywenty/roboto_example
 * [new tag]         v1.0.2 -> v1.0.2
robo@roboa100:~/roboto/roboto_example$ 



# 1. 直接从你的私有源下载最新的钥匙（此时服务器上的钥匙已经对齐了）
sudo curl -fsSL "http://apt.roboparty.com/roboparty.gpg" | sudo gpg --dearmor -o /usr/share/keyrings/roboparty-archive-keyring.gpg
sudo chmod 644 /usr/share/keyrings/roboparty-archive-keyring.gpg

# 2. 写入你的 x86 软件源列表
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/roboparty-archive-keyring.gpg] http://apt.roboparty.com common main" | sudo tee /etc/apt/sources.list.d/roboparty.list

# 3. 刷新
sudo apt-get update



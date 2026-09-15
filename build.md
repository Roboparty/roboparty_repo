# Ubuntu 24.04 构建状态

更新日期：2026-09-15

本文记录 `/home/robo/roboparty_repo` 当前本地文件中的 Debian 构建矩阵。
CI 已完成状态按项目确认记录；workflow 具体配置以本地同步副本的静态检查为准。
尚未完成的代码、实机和发布工作见 [todo.md](todo.md)。

## 发布范围

- 正式构建只面向 Ubuntu 24.04（Noble）。
- `Architecture: all` 包构建一次。
- C/C++ `Architecture: any` 包分别构建 AMD64 和 ARM64。
- 板卡专用包只构建 ARM64。
- `roboparty-camera`、`roboparty-rp-head` 和 `roboparty-go` 暂不进入本轮发布。
- `roboparty_deb_template` 是模板，不计入发布包数量。

当前目标为 **15 个包、22 个 deb**：

| 类型 | 包 | deb 数量 |
|---|---|---:|
| `all` | `all`、`base`、`description`、`example`、`rp-server`、`robopi-analyze` | 6 |
| AMD64 + ARM64 | `motors`、`imu`、`bms`、`dexhand`、`inference`、`lidar`、`onnxruntime` | 14 |
| ARM64 板卡包 | `robopi-addon`、`robopi-config` | 2 |

## 当前构建矩阵

| 源码目录 | 包版本 | Debian 架构 | 当前 workflow runner | 当前状态 |
|---|---:|---|---|---|
| `roboparty_all` | `1.3.2-1` | `all` | `ubuntu-latest` | CI 已确认完成；本地 workflow 尚未固定为 24.04 |
| `roboparty_base` | `1.1.8-1` | `all` | `ubuntu-latest` | CI 已确认完成；待 24.04 安装验证 |
| `roboparty_description` | `1.2.1-1` | `all` | `ubuntu-latest` | CI 已确认完成；待安装验证 |
| `roboparty_example` | `1.1.0-1` | `all` | `ubuntu-latest` | CI 已确认完成；运行时依赖仍需整理 |
| `roboparty_rp_server` | `1.4.0-1` | `all` | `ubuntu-24.04` | CI 已确认完成；仍有 inference 配置隐式依赖 |
| `robopi_analyze` | `1.0.0-1` | `all` | `ubuntu-24.04` | HPM 和通信诊断已从 addon 拆分 |
| `roboparty_motors` | `2.3.0-1` | `any` | AMD64 24.04 + ARM64 自托管 24.04 | 双架构 CI 已确认完成；待 pybind 验证 |
| `roboparty_imu` | `1.4.0-1` | `any` | AMD64 24.04 + ARM64 自托管 24.04 | 双架构 CI 已确认完成；待 pybind 验证 |
| `roboparty_bms` | `1.5.1-1` | `any` | AMD64 24.04 + ARM64 自托管 24.04 | 双架构 CI 已确认完成；待服务、串口和 OTA 验证 |
| `roboparty_dexhand` | `0.5.0-1` | `any` | AMD64 24.04 + ARM64 自托管 24.04 | 双架构 CI 已确认完成；待 ARM64 厂商库验证 |
| `roboparty_inference` | `1.3.0-1` | `any` | AMD64 24.04 + ARM64 自托管 24.04 | Jazzy 双架构 CI 已确认完成；待节点、模型和 `robot_py` 验证 |
| `roboparty_lidar` | `0.1.1-1` | `any` | AMD64 24.04 + ARM64 自托管 24.04 | 双架构 CI 已确认完成；待补 changelog |
| `roboparty_onnxruntime` | `1.21.0-1` | `amd64 arm64` | AMD64 24.04 + ARM64 托管 24.04 | inference 的双架构运行时依赖 |
| `robopi_addon` | `1.7.18-1` | `arm64` | ARM64 自托管 24.04 | CI 已确认完成；目标内核为 `6.18.51-current-rockchip64` |
| `robopi_config` | `0.1.14-1` | `arm64` | `ubuntu-24.04-arm` | CI 已确认完成；待目标板功能验证 |

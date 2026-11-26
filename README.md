# sagit (Xiaomi 6) 4.4.302 KernelSU 系内核镜像

小米 6（sagit / MSM8998）LineageOS 23.1 内核（Linux 4.4.302）的 KernelSU 系 root 方案适配与 boot 镜像。

## 基线

| 项目 | 值 |
|---|---|
| 机型 | Xiaomi 6 (sagit), MSM8998 |
| 内核基线 | `Nanhumly-Staging/android_kernel_xiaomi_msm8998` @ `2f6ba5671b2` |
| 内核版本串 | `Linux version 4.4.302-canary-gc6830e35c`（保持原厂，vendor 模块可兼容） |
| 原厂 boot | `boot_stock_original.img`（SHA256 `4f4ac1bb…fb29af`） |

## 镜像状态

| 变体 | 文件（Release 附件） | 状态 | 管理器 |
|---|---|---|---|
| SukiSU Nova `v3.0.0-r1`（builtin 内置） | `boot_sagit_231_ksu.img` | ✅ 已构建 | `com.sukisu.nova` |
| BakaSU（manual hook） | `boot_sagit_231_bakasu.img` | ✅ 已构建 | BakaSU 管理器 |
| KernelSU-Next（legacy 分支，manual hook） | — | 🚧 进行中 | KernelSU-Next 管理器 |
| KernelSU 官方（main） | — | ⏳ 待评估（新版架构对 4.4 兼容差） | KernelSU 管理器 |

> 镜像均为 67,108,864 字节，ramdisk 与原厂逐字节一致，仅替换内核（Image.gz + 原厂 DTB）。

## 刷入 / 回滚

```bash
# 刷入（任选一个变体）
fastboot flash boot boot_sagit_231_ksu.img
fastboot reboot

# 回滚原厂
fastboot flash boot boot_stock_original.img
```

## 已启用的内核能力

- `CONFIG_KSU=y`（内置，非模块），手动 hook：execveat / faccessat / stat / vfs_fstat / vfs_read / reboot
- Droidspaces 依赖：UTS/PID/IPC/USER/NET namespace、SYSVIPC、POSIX_MQUEUE、
  CGROUP_SCHED/CFS_BANDWIDTH/PIDS/DEVICE/FREEZER/MEMCG(+SWAP)、DEVTMPFS(_MOUNT)、
  OVERLAY_FS、VETH/MACVLAN/BRIDGE/TUN、IP6_NF_NAT/MASQUERADE、KPROBES、CGROUP_BPF、SECCOMP_FILTER
- 版本串保持 `4.4.302-canary-gc6830e35c`

## 已知限制

- 「隐藏 SELinux 修改」（`KSU_FEATURE_SELINUX_HIDE`）在 SukiSU/BakaSU 中要求内核 ≥5.10 的新 SELinux 架构
  （`selinux_state` / `struct selinux_policy`）。4.4 为老的全局 `policydb`/`sidtab` 架构，当前未启用该特性，
  不影响 root 与 Droidspaces。
- 各变体的实际功能（root 授权、模块、Droidspaces 检测）需实机验证。

## 仓库内容

| 路径 | 说明 |
|---|---|
| `patches/kernel-4.4-ksu.patch` | 内核侧改动：KSU 驱动挂载、手动 hook、selinux/namespace 适配 |
| `patches/sukisu-builtin-4.4.patch` | SukiSU builtin 分支的 4.4 兼容补丁 |
| `patches/ksunext-legacy-4.4-adbroot.patch` | KernelSU-Next legacy 的 4.4 小补丁 |
| `configs/config.ksunext-legacy` | 当前 KSU-Next 构建使用的内核配置 |
| `scripts/build_kernel.sh` | 编译命令（clang-14 + GNU ld） |
| `scripts/pack_boot.py` | 用原厂 boot 作模板打包新 boot.img |
| `SHA256SUMS` | 已发布镜像的校验值 |

## 构建方法（简述）

```bash
# 1. 准备内核树并切到基线
git clone https://github.com/Nanhumly-Staging/android_kernel_xiaomi_msm8998
cd android_kernel_xiaomi_msm8998 && git checkout 2f6ba5671b2

# 2. 应用内核补丁
git apply /path/to/patches/kernel-4.4-ksu.patch

# 3. 放入对应 root 方案源码（本仓库不包含第三方 KSU 源码）
#    SukiSU:        git clone -b builtin https://github.com/SukiSU-Ultra/SukiSU-Ultra KernelSU
#    BakaSU:        git clone https://github.com/Baka-SU/BakaSU
#    KSU-Next:      git clone -b legacy https://github.com/KernelSU-Next/KernelSU-Next
#    并建立 drivers/kernelsu 指向其 kernel/ 目录，drivers/Kconfig、drivers/Makefile 已由补丁接入

# 4. 配置并编译
./scripts/build_kernel.sh        # 生成 out_231/arch/arm64/boot/Image.gz

# 5. 打包 boot.img（使用原厂 boot 作模板）
python3 scripts/pack_boot.py \
  --kernel-gz out_231/arch/arm64/boot/Image.gz \
  --src boot_stock_original.img \
  --out boot_sagit_231_<variant>.img
```

## 免责声明

仅供个人设备研究与备份使用。刷机有风险，请自行确认机型、分区与回滚镜像；因刷入导致的变砖、数据丢失等后果自负。

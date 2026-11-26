#!/bin/bash
# sagit 4.4.302 lineage-23.1 修复版构建（WiFi/振动/指纹驱动补齐）
set -e

K=/workspace/build/kernel-231
OUT=$K/out_231
BASE=/workspace/work/sagit-handover/changes/config_final_231.txt
STOCK=/workspace/work/sagit-handover/boot_stock_original.img
PACK=$K/handover_pack_boot_v2.py
JOBS=${JOBS:-3}

cd "$K"

# 源码改动 1：删除 localversion-cip
rm -f localversion-cip
# 源码改动 2：kernel/bpf/core.c 补 u32 tmp;
if ! grep -q $'^\tu32 tmp;$' kernel/bpf/core.c; then
  sed -i 's/^\tu32 tail_call_cnt = 0;$/\tu32 tail_call_cnt = 0;\n\tu32 tmp;/' kernel/bpf/core.c
fi

mkdir -p "$OUT"
cp "$BASE" "$OUT/.config"

./scripts/config --file "$OUT/.config" \
  -e QCA_CLD_WLAN \
  -e LEDS_QPNP_HAPTICS \
  -e INPUT_FINGERPRINT -e FINGERPRINT_GOODIX_TA -e FINGERPRINT_FPC1268_TEE \
  -e SPI_PEELIR -e QCOM_PRESERVE_MEM -e PGTABLE_MAPPING

MK=(ARCH=arm64
    CC=clang-14
    LD=aarch64-linux-gnu-ld
    AR=llvm-ar-14
    NM=llvm-nm-14
    OBJCOPY=llvm-objcopy-14
    OBJDUMP=llvm-objdump-14
    STRIP=llvm-strip-14
    CLANG_TRIPLE=aarch64-linux-gnu-
    CROSS_COMPILE=aarch64-linux-gnu-
    CROSS_COMPILE_ARM32=arm-linux-gnueabi-
    HOSTCC=gcc HOSTCXX=g++
    HOSTCFLAGS=-fcommon
    KBUILD_BUILD_USER=builder KBUILD_BUILD_HOST=localhost
    KCFLAGS=-Wno-error
    LOCALVERSION=)

make O=$OUT "${MK[@]}" olddefconfig

grep -E "CONFIG_(QCA_CLD_WLAN|LEDS_QPNP_HAPTICS|INPUT_FINGERPRINT|FINGERPRINT_GOODIX_TA|FINGERPRINT_FPC1268_TEE|QCOM_PRESERVE_MEM|PGTABLE_MAPPING)=" "$OUT/.config" || true

nice -n 5 make O=$OUT "${MK[@]}" -j"$JOBS" Image.gz

ls -l "$OUT/arch/arm64/boot/Image.gz"
strings -a "$OUT/arch/arm64/boot/Image" | grep -m1 "Linux version 4.4.302"

python3 "$PACK" --kernel-gz "$OUT/arch/arm64/boot/Image.gz" \
  --src "$STOCK" \
  --out /workspace/work/sagit-handover/boot_sagit_231_fixed.img
sha256sum /workspace/work/sagit-handover/boot_sagit_231_fixed.img

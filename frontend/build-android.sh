#!/bin/bash
# Android APK 构建脚本（适配低内存服务器）
# 用法：cd frontend && ./build-android.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SWAP_FILE="/tmp/android_build_swap"
ANDROID_HOME="${ANDROID_HOME:-$HOME/android-sdk}"
CAPACITOR_CONFIG="$SCRIPT_DIR/capacitor.config.json"

# 检查并增加临时 swap（当可用内存 < 2G 时）
ensure_swap() {
  local available_kb=$(free -k | awk '/^Mem:/ {print $7}')
  local threshold_kb=$((2 * 1024 * 1024)) # 2G
  if [ "$available_kb" -lt "$threshold_kb" ] && [ ! -f "$SWAP_FILE" ]; then
    echo "[build] 可用内存不足，创建 4G 临时 swap..."
    sudo fallocate -l 4G "$SWAP_FILE" || dd if=/dev/zero of="$SWAP_FILE" bs=1M count=4096
    sudo chmod 600 "$SWAP_FILE"
    sudo mkswap "$SWAP_FILE"
    sudo swapon "$SWAP_FILE"
  fi
}

# 清理临时 swap
cleanup_swap() {
  if [ -f "$SWAP_FILE" ]; then
    echo "[build] 清理临时 swap..."
    sudo swapoff "$SWAP_FILE" 2>/dev/null || true
    sudo rm -f "$SWAP_FILE"
  fi
}

# 退出时清理 swap 并恢复 capacitor 配置
trap cleanup_swap EXIT

cd "$SCRIPT_DIR"
ensure_swap

echo "[build] 安装依赖（如有缺失）..."
npm install

echo "[build] 构建移动端资源..."
npm run build:mobile

# Capacitor 要求 webDir 内必须包含 index.html，而 Vite 输出的是 index.mobile.html
echo "[build] 重命名入口文件为 index.html..."
if [ -f "$SCRIPT_DIR/dist-mobile/index.mobile.html" ]; then
  mv "$SCRIPT_DIR/dist-mobile/index.mobile.html" "$SCRIPT_DIR/dist-mobile/index.html"
fi

# 临时将 Capacitor webDir 切换为 dist-mobile，复制完成后再恢复
echo "[build] 同步 Capacitor（使用 dist-mobile）..."
if [ -f "$CAPACITOR_CONFIG" ]; then
  cp "$CAPACITOR_CONFIG" "$CAPACITOR_CONFIG.bak"
  sed -i 's/"webDir": *"[^"]*"/"webDir": "dist-mobile"/' "$CAPACITOR_CONFIG"
fi

npx cap copy android

if [ -f "$CAPACITOR_CONFIG.bak" ]; then
  mv "$CAPACITOR_CONFIG.bak" "$CAPACITOR_CONFIG"
fi

echo "[build] 构建 debug APK..."
cd android
export ANDROID_HOME
./gradlew assembleDebug --no-daemon

APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
echo "[build] 完成: $SCRIPT_DIR/android/$APK_PATH"
ls -lh "$APK_PATH"

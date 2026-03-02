#!/bin/bash
set -e

echo "==================================================="
echo "   KlipperCortex: C++ Runner Builder"
echo "==================================================="

ARCH="${1:-${TARGET_ARCH:-cortex-a53}}"

echo "Target Architecture: $ARCH"

BUILD_DIR="build_${ARCH}"

# Additional CMake flags for cross-compilation can be passed via env vars
CMAKE_FLAGS=""

# Auto-detect if we're on an x86 host and need cross-compilers
if [ "$(uname -m)" == "x86_64" ]; then
    echo "Detected x86_64 host. Enabling cross-compilation toolchain..."
    if [ "$ARCH" == "cortex-a7" ]; then
        CMAKE_FLAGS="-DCMAKE_SYSTEM_NAME=Linux -DCMAKE_SYSTEM_PROCESSOR=arm -DCMAKE_C_COMPILER=arm-linux-gnueabihf-gcc -DCMAKE_CXX_COMPILER=arm-linux-gnueabihf-g++"
    else
        CMAKE_FLAGS="-DCMAKE_SYSTEM_NAME=Linux -DCMAKE_SYSTEM_PROCESSOR=aarch64 -DCMAKE_C_COMPILER=aarch64-linux-gnu-gcc -DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++"
    fi
fi

if [ "$ARCH" == "cortex-a7" ]; then
    echo "Configuring for Cortex-A7 (Raspberry Pi 2)..."
    CMAKE_FLAGS="$CMAKE_FLAGS -DCMAKE_C_FLAGS=-mcpu=cortex-a7 -DCMAKE_CXX_FLAGS=-mcpu=cortex-a7"
elif [ "$ARCH" == "cortex-a53" ]; then
    echo "Configuring for Cortex-A53 (Raspberry Pi 3B+ / Pi Zero 2W)..."
    CMAKE_FLAGS="$CMAKE_FLAGS -DCMAKE_C_FLAGS=-mcpu=cortex-a53 -DCMAKE_CXX_FLAGS=-mcpu=cortex-a53"
elif [ "$ARCH" == "cortex-a72" ]; then
    echo "Configuring for Cortex-A72 (Raspberry Pi 4 / Pi 400)..."
    CMAKE_FLAGS="$CMAKE_FLAGS -DCMAKE_C_FLAGS=-mcpu=cortex-a72 -DCMAKE_CXX_FLAGS=-mcpu=cortex-a72"
elif [ "$ARCH" == "cortex-a76" ]; then
    echo "Configuring for Cortex-A76 (Raspberry Pi 5)..."
    CMAKE_FLAGS="$CMAKE_FLAGS -DCMAKE_C_FLAGS=-mcpu=cortex-a76 -DCMAKE_CXX_FLAGS=-mcpu=cortex-a76"
fi

echo "Cleaning old build directory: $BUILD_DIR..."
rm -rf "$BUILD_DIR"

echo "Running CMake Generate..."
cmake -B "$BUILD_DIR" $CMAKE_FLAGS

echo "Running CMake Build..."
cmake --build "$BUILD_DIR" --target model_runner -j$(nproc)

echo ""
echo "✅ Build successful!"
echo "Runner executable is located at: ${BUILD_DIR}/model_runner"

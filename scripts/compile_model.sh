#!/bin/bash
set -e

echo "==================================================="
echo "   KlipperCortex: Model Compiler (IREE)"
echo "==================================================="

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <path_to_model.onnx|.tflite> [cpu_architecture]"
    echo ""
    echo "You can also set the TARGET_ARCH environment variable."
    echo "Supported Architectures:"
    echo "  - cortex-a53 (Default, Raspberry Pi 3B+ / Pi Zero 2 W)"
    echo "  - cortex-a7  (Raspberry Pi 2)"
    echo "  - cortex-a72 (Raspberry Pi 4 / Pi 400)"
    echo "  - cortex-a76 (Raspberry Pi 5)"
    echo "  - generic    (Fallback, no CPU-specific optimizations)"
    exit 1
fi

MODEL_FILE="$1"
# Priority: 1) CLI argument, 2) Environment variable, 3) Default 
ARCH="${2:-${TARGET_ARCH:-cortex-a53}}"

if [ ! -f "$MODEL_FILE" ]; then
    echo "Error: File '$MODEL_FILE' not found."
    exit 1
fi

BASENAME=$(basename "$MODEL_FILE")
EXTENSION="${BASENAME##*.}"
FILENAME="${BASENAME%.*}"
DIRNAME=$(dirname "$MODEL_FILE")

OUTPUT_VMFB="${DIRNAME}/${FILENAME}_${ARCH}.vmfb"
MLIR_TMP="/tmp/klipper_cortex_compilation_${FILENAME}.mlir"

echo "Target Architecture: $ARCH"
echo "Input Model: $MODEL_FILE"

# 1. Translate to MLIR (TOSA dialect)
if [ "$EXTENSION" == "onnx" ]; then
    echo "Step 1: Converting ONNX to TFLite (via onnx2tf)"
    # ONNX -> TFLite conversion is used because IREE's TFLite frontend
    # is the most robust path for vision models like MobileNetV2
    onnx2tf -i "$MODEL_FILE" -o "/tmp/model_tflite" > /dev/null 2>&1
    TFLITE_MODEL="/tmp/model_tflite/model.tflite"
    
    echo "Step 2: Importing TFLite to MLIR"
    iree-import-tflite "$TFLITE_MODEL" -o "$MLIR_TMP"
    rm -rf "/tmp/model_tflite"

elif [ "$EXTENSION" == "tflite" ]; then
    echo "Step 1: Importing TFLite to MLIR"
    iree-import-tflite "$MODEL_FILE" -o "$MLIR_TMP"
else
    echo "Error: Unsupported file extension .$EXTENSION. Use .onnx or .tflite"
    exit 1
fi

# 2. Compile MLIR to VMFB bytecode for the target architecture
echo "Step 3: Compiling to IREE VMFB bytecode for $ARCH..."
iree-compile \
    --iree-hal-target-backends=llvm-cpu \
    --iree-llvmcpu-target-cpu="$ARCH" \
    "$MLIR_TMP" \
    -o "$OUTPUT_VMFB"

rm -f "$MLIR_TMP"

echo ""
echo "✅ Compilation successful!"
echo "Output: $OUTPUT_VMFB"
echo ""
echo "You can now update your connections.json or .env to point MODEL_PATH to this file."

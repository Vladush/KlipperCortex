# Use a standard multi-architecture base image
FROM ubuntu:22.04

# Install necessary build dependencies
RUN apt-get update && apt-get install -y \
    wget \
    git \
    python3 \
    python3-pip \
    bash \
    cmake \
    g++-aarch64-linux-gnu \
    g++-arm-linux-gnueabihf \
    && rm -rf /var/lib/apt/lists/*

# Install the IREE compiler
# By running this on your native x86 machine but compiling for the Cortex-A53 target later, 
# you bypass slow emulation layers.
# Install Python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Install IREE compiler and conversion tools.
# Strategy: Use onnx2tf to convert ONNX -> TFLite, then compile TFLite -> IREE.
# This avoids direct ONNX import issues and supports both model formats.
# Install IREE compiler and conversion tools.
# Strategy: Use onnx2tf to convert ONNX -> TFLite, then compile TFLite -> IREE.
RUN pip3 install iree-compiler iree-tools-tflite

RUN pip3 install onnx==1.16.1 onnx2tf tensorflow-cpu==2.16.1 tf-keras psutil ai-edge-litert

RUN pip3 install sng4onnx onnx-graphsurgeon simple_onnx_processing_tools onnxsim

WORKDIR /workspace

# Runtime Environment Variables (for inference verification or containerized execution)
ENV PRINTER_HOST="localhost" \
    MOONRAKER_PORT="7125" \
    MODEL_PATH="/workspace/models/spaghetti_v2.vmfb" \
    THRESHOLD="0.85"


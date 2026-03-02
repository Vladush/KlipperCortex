# KlipperCortex

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-green.svg)](https://python.org)

Edge-node spaghetti detection for Klipper 3D printers. Runs a MobileNetV2 model compiled to [IREE](https://iree.dev/) bytecode directly on a Raspberry Pi, bypassing TFLite interpreter overhead.

When a failed print is detected with high confidence, it automatically pauses the printer via Moonraker API.

## Requirements

**Hardware:**

- Raspberry Pi 3B+ (Cortex-A53) or newer
- USB webcam or Pi Camera Module
- Network connection to your Klipper/Moonraker instance

**Software:**

- Python 3.10+
- Klipper + Moonraker running on your printer
- IREE runtime (`iree-runtime` pip package)

## Quick Start

```bash
# 1. Clone & install
git clone https://github.com/Vladush/KlipperCortex.git
cd KlipperCortex
bash scripts/install.sh

# 2. Download a model
python3 scripts/download_models.py

# 3. Configure your printer connection
cp connections.json.example connections.json
nano connections.json

# 4. Run
source .venv/bin/activate
python3 src/inference_loop.py
```

## Directory Structure

- **`models/`** — AI models (source `.tflite`, compiled `.vmfb`)
- **`scripts/`** — Deployment, installation, and verification utilities
- **`src/`** — Inference loop and native model runner
- **`docs/`** — Detailed documentation
- **`config/`** — Systemd service template

## Building the C++ Model Runner (Optional)

The Python inference loop (`src/inference_loop.py`) is the primary way to run detection. The C++ model runner is an alternative for lower-overhead execution, and is highly recommended for low-RAM devices like the Raspberry Pi 2.

```bash
# Initialize the IREE submodule (if not already done)
git submodule update --init --recursive

# Build natively for Raspberry Pi 3/4 (cortex-a53)
bash scripts/build_runner.sh

# Or, build natively for Raspberry Pi 2 (cortex-a7)
bash scripts/build_runner.sh cortex-a7
```

*Note: If you are cross-compiling from a PC instead of building directly on the Pi, you will need an ARM toolchain file and pass it via the `CMAKE_FLAGS` environment variable (e.g., `CMAKE_FLAGS="-DCMAKE_TOOLCHAIN_FILE=..." bash scripts/build_runner.sh`).*

## Configuration

All runtime settings are controlled via environment variables:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PRINTER_HOST` | `localhost` | Moonraker host |
| `MOONRAKER_PORT` | `7125` | Moonraker port |
| `MODEL_PATH` | `models/spaghetti_v2.vmfb` | Path to compiled model |
| `THRESHOLD` | `0.85` | Confidence threshold for pausing |
| `CAMERA_TYPE` | `http` | `http` or `local` |
| `DRY_RUN` | `false` | Test without hardware |

See [docs/inference.md](docs/inference.md) for the full list.

## Documentation

- [Compilation Guide](docs/compilation.md) — Compiling models (ONNX/TFLite) to IREE VMFB
- [Inference Loop](docs/inference.md) — Camera, lighting, and runtime configuration
- [Architecture](docs/architecture_and_flow.md) — System design overview
- [MCP Integration](docs/mcp_integration.md) — Model Context Protocol usage

## Deploying to a Printer

```bash
python3 scripts/deploy.py
```

This transfers the model and inference script to the Pi and restarts the systemd service. See `config/klipper-cortex.service` for the service template.

## Roadmap

- [x] Multi-architecture model compilation via `scripts/compile_model.sh` — tested on `cortex-a53` (Pi 3B+).
- [ ] Verify and test on `cortex-a7` (Pi 2), `cortex-a72` (Pi 4), and `cortex-a76` (Pi 5).
- [ ] Support for additional object detection models.
- [ ] Integration with more 3D printer firmwares seamlessly.
- [ ] Advanced confidence heuristics for automated pausing.

## Contributing

PRs are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security & Permissions

> [!IMPORTANT]
> `connections.json` contains your printer credentials — keep it restricted (`chmod 600`).
> Deployment and service management may require `sudo` on the Pi.

## License

[MIT](LICENSE)

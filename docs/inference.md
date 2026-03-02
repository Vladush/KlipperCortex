# Inference Loop & Features

The implementation in `src/inference_loop.py` provides a robust detection loop with hardware integration.

## Key Features

1. **Model Support**: Runs both Legacy TFLite and Modern ONNX models via IREE runtime.
2. **Lighting Control**: Synchronizes LED lighting with camera capture to ensure consistent image quality.
3. **Resolution Control**: Optimizes local USB camera input for performance.
4. **Dry Run Mode**: Simulutes the entire pipeline for safe testing without hardware.

## Configuration

Control the behavior using environment variables in your `.env` file.

### General

| Variable | Default | Description |
| :--- | :--- | :--- |
| `MODEL_PATH` | `models/spaghetti_v2.vmfb` | Path to the compiled IREE module. |
| `THRESHOLD` | `0.5` | Confidence threshold for detection. |
| `DRY_RUN` | `false` | Set to `true` to simulate hardware interactions. |

### Camera & Resolution

| Variable | Default | Description |
| :--- | :--- | :--- |
| `CAMERA_TYPE` | `http` | `local` (USB) or `http` (MJPEG stream). |
| `CAMERA_WIDTH` | `640` | Resolution width for local camera. |
| `CAMERA_HEIGHT` | `480` | Resolution height for local camera. |

### Lighting Control

| Variable | Default | Description |
| :--- | :--- | :--- |
| `LIGHTING_ENABLED` | `false` | Enable/Disable lighting synchronization. |
| `LIGHTING_GCODE_ON` | `SET_LED...` | G-code to turn lights ON. |
| `LIGHTING_GCODE_OFF` | `SET_LED...` | G-code to turn lights OFF. |

## Testing with Dry Run

To verify the logic without connecting a printer or camera:

```bash
DRY_RUN=true \
CAMERA_TYPE=local \
LIGHTING_ENABLED=true \
MODEL_PATH=models/model.vmfb \
python3 src/inference_loop.py
```

This will:

- Log G-code commands instead of sending them.
- Generate mock images.
- Use a mock model (no inference).
- Log pause commands.

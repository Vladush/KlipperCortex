# Model Enhancement & Feedback Loop Proposal

This document outlines strategies to enhance the KlipperCortex AI model using real-world data captured directly from your printer. By collecting and categorizing **False Positives (FP)**, **False Negatives (FN)**, **True Positives (TP)**, and **True Negatives (TN)**, a custom dataset can be created to fine-tune the model for your specific environment.

## 1. Data Definitions

* **True Positive (TP)**: The model detected spaghetti, and it **was** spaghetti.
  * *Value*: Confirms the model works. Useful for preventing "catastrophic forgetting" during retraining.
* **False Positive (FP)**: The model detected spaghetti, but the print was **fine**.
  * *Value*: **Extremely High**. These are "annoyances" that pause your print. the model needs to learn these are safe.
* **True Negative (TN)**: The model thought it was safe, and it **was**.
  * *Value*: Low, unless it's a "tricky" part that looks like spaghetti but isn't.
* **False Negative (FN)**: The model thought it was safe, but the print **failed**.
  * *Value*: **Critical**. The model missed a failure. It needs to be taught to catch these.

---

## 2. Implementation Strategies

Here are many options, ranging from simple to complex.

### Option A: The "Snapshot" System (Low Complexity)

**Concept**: A simple file-system based approach. No UI changes needed.

1. **Automated Capture**:
    * Whenever the model triggers a **PAUSE** (Confidence > Threshold), it saves the image to `~/snapshots/suspected_failure/`.
    * Every 10 minutes of normal printing, it saves an image to `~/snapshots/normal/` (auto-delete old ones to save space).
2. **User Action**:
    * **If Paused Correctly (TP)**: User does nothing (or moves file to `confirmed_spaghetti`).
    * **If False Alarm (FP)**: User resumes print. User later logs into Pi (SSH/SFTP) and moves the image from `suspected_failure` to `dataset/false_positives`.
    * **If Missed Failure (FN)**: User notices spaghetti. User manually runs a script `save_failure.sh` (or a macro button in Mainsail) which continuously saves the next 10 frames to `dataset/missed_failures`.

**Pros**: Easy to implement.
**Cons**: Manual file management; high friction for the user.

### Option B: The "Review Gallery" Web App (Medium Complexity)

**Concept**: A lightweight web interface running on port 5001 on the Pi.

1. **Backend**: A small Python (Flask/FastAPI) app runs alongside the inference loop.
2. **Workflow**:
    * Inference loop saves "Events" to a local SQLite DB.
    * User visits `http://mainsail.local:5001`.
    * **Inbox View**: Shows the last 5 Pauses and random normal snapshots.
    * **Buttons**: "👍 Correct", "👎 Wrong", "⚠️ Missed Failure" (Upload button).
3. **Data Handling**:
    * Clicking "Wrong" on a Pause moves the image to `dataset/false_positive`.
    * Clicking "Missed Failure" allows uploading a photo from phone or grabbing the latest camera buffer.

**Pros**: User-friendly, visual, immediate feedback.
**Cons**: Requires maintaining another service/port.

### Option C: Moonraker/Mainsail Integration (High Complexity)

**Concept**: Integrate directly into the 3D Printer dashboard everyone already uses.

1. **Custom Macro**: Create Klipper macros `[gcode_macro REPORT_FALSE_POSITIVE]` and `[gcode_macro REPORT_MISSED_FAILURE]`.
2. **Workflow**:
    * When the print pauses, the user checks the webcam.
    * If it's a false alarm, they click the `REPORT_FALSE_POSITIVE` macro button in Mainsail *before* clicking Resume.
    * The macro passes a signal to our `inference_loop.py` (via file or socket) to tag the last image as FP.
3. **Notifications**: Use the `Moonraker` notification system to send a thumbnail to your phone (Telegram/Discord) with "Spaghetti Detected! [Confirm] [Deny]".

**Pros**: Seamless integration into existing workflow. No new UI to check.
**Cons**: Complex to set up Klipper macros to talk to external Python scripts.

### Option D: Cloud/Hybrid (Maximum Overkill)

**Concept**: Automatically sync "interesting" images to a cloud bucket.

1. **Sync**: `rclone` or similar tool runs nightly.
2. **Central Training**: Images are uploaded to a Google Drive / S3 bucket.
3. **Auto-Training**: A GitHub Action or Colab script pulls these images, fine-tunes the model, and compiles a new `.vmfb` file.
4. **Auto-Update**: The Pi pulls the new model automatically on boot.

**Pros**: Truly autonomous "Tesla Autopilot" style improvement.
**Cons**: Privacy concerns (uploading images of your room/house), data usage, high complexity.

---

## 3. Data Enhancement Strategies (The "Flywheel")

Once data is collected, how is it used?

1. **Hard Example Mining**:
    * Take the False Positives (FPs).
    * Add them to the training set with label `0` (Safe).
    * Retrain. This forces the model to learn the specific "weird" features of your printer (e.g., a shiny red cable that looks like spaghetti).
2. **Contextual Inputs (Future)**:
    * Pass the **Z-height** or **Print Progress %** to the model?
    * *Hypothesis*: Spaghetti usually happens mid-print, not continuously.
    * *Counter*: Spaghetti can happen anywhere. Visual data is King.
3. **Time-Series Analysis**:
    * Instead of 1 frame, pass 3 consecutive frames.
    * *Logic*: Spaghetti grows wildly. A static cable stays still. Motion flow could distinguish them.

## 4. Recommended Roadmap

1. **Phase 1 (Now)**: Implement **Option A (Snapshot System)** with a helper macro.
    * Modify `inference_loop.py` to save images on Pause.
    * Create a simple Klipper Macro `MARK_FALSE_ALARM` that moves the last image to a specific folder.
2. **Phase 2**: **Dataset Curator Tool**.
    * A simple script to zip up the "False Alarms" folder and "Confirmed Failures" folder for export.
3. **Phase 3**: **Retraining Pipeline (via ONNX)**.

    The `.tflite` and `saved_model.pb` files in `models/model_tflite/` are intermediate conversion artifacts produced by `onnx2tf` during compilation — they work for inference but aren't practical for training. The correct starting point is `models/model.onnx`.

    **Steps:**

    ```bash
    pip install onnx2torch torch torchvision
    ```

    ```python
    import torch
    from onnx2torch import convert

    model = convert("models/model.onnx")

    # Freeze everything except the final classifier
    for param in model.parameters():
        param.requires_grad = False
    # Unfreeze the last layer (name depends on architecture)
    for param in list(model.parameters())[-2:]:
        param.requires_grad = True

    optimizer = torch.optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()), lr=1e-4
    )
    ```

    The training data is structured as:

    ```text
    dataset/
    ├── safe/          # FPs + confirmed safe images
    └── spaghetti/     # TPs + missed failures (FNs)
    ```

    After fine-tuning, export back to ONNX and run the existing `/deploy` pipeline:

    ```python
    dummy = torch.randn(1, 224, 224, 3)
    torch.onnx.export(model, dummy, "models/model_finetuned.onnx")
    ```

    **For ONNX Models:**

    The build script `scripts/compile_model.sh` automatically handles model format conversion:
    Then compile via `scripts/compile_model.sh` as usual → new `.vmfb` on the Pi.

    ~50-200 labeled images from your printer should be enough to noticeably reduce false positives without degrading overall accuracy.

    This entire flow can run in a [Google Colab](https://colab.google.com/) notebook — free GPU, no local PyTorch setup required. Upload the zipped dataset, run the cells, download the new `.onnx` file, and compile locally.

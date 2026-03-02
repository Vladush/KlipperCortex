#!/usr/bin/env python3
import os
import requests
import sys
import argparse

# Model Definitions
MODELS = {
    "1": {
        "name": "Official Obico ONNX (Recommended)",
        "url": "https://tsd-pub-static.s3.amazonaws.com/ml-models/model-weights-5a6b1be1fa.onnx",
        "filename": "model.onnx",
        "type": "onnx"
    },
    "2": {
        "name": "Original Coral MobileNetV2 (Legacy)",
        "url": "https://github.com/google-coral/test_data/raw/master/ssd_mobilenet_v2_coco_quant_postprocess.tflite",
        "filename": "model.tflite",
        "type": "tflite"
    },
    "3": {
        "name": "Obico Legacy TFLite (spaghetti_v2.tflite)",
        "url": "https://github.com/TheSpaghettiDetective/obico-server/raw/master/obico/ml/spaghetti_v2.tflite",
        "filename": "model.tflite",
        "type": "tflite"
    }
}

MODEL_DIR = "models"

def download_file(url, dest_path):
    print(f"Downloading {url}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Downloaded to {dest_path}")
        return True
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Download AI models for KlipperCortex")
    parser.add_argument("--model", choices=["1", "2", "3"], help="Select model to download (1=Official ONNX, 2=Coral, 3=Obico Legacy)")
    args = parser.parse_args()

    # Ensure model directory exists
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)

    selection = args.model
    if not selection:
        print("Select a model to download:")
        for key, model in MODELS.items():
            print(f"[{key}] {model['name']}")
        
        selection = input("\nEnter choice [1-3] (Default: 1): ").strip()
        if not selection:
            selection = "1"

    if selection not in MODELS:
        print("Invalid selection.")
        sys.exit(1)

    model_info = MODELS[selection]
    dest_path = os.path.join(MODEL_DIR, model_info["filename"])
    
    # If detecting collision rename old file? 
    # For now, we just overwrite as we want one specific model to present to the compiler.
    
    print(f"\nSelected: {model_info['name']}")
    download_file(model_info["url"], dest_path)
    print(f"Model saved to {dest_path}")
    
    # Clean up conflicting files if they exist to avoid confusion
    if model_info["type"] == "onnx" and os.path.exists(os.path.join(MODEL_DIR, "model.tflite")):
        print("Note: You have both model.onnx and model.tflite. The compiler will prioritize ONNX if you pass it.")
    elif model_info["type"] == "tflite" and os.path.exists(os.path.join(MODEL_DIR, "model.onnx")):
         print("Note: You have both model.onnx and model.tflite. The compiler will prioritize TFLite if you pass it.")


if __name__ == "__main__":
    main()

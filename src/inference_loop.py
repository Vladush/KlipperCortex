import time
import requests
import numpy as np
try:
    import iree.runtime as ireert
except ImportError:
    ireert = None
from PIL import Image
import io
import os
import cv2  # For LocalCamera
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# configuration
PRINTER_HOST = os.getenv("PRINTER_HOST", "localhost")
MOONRAKER_PORT = os.getenv("MOONRAKER_PORT", "7125")
MODEL_PATH = os.getenv("MODEL_PATH", "models/spaghetti_v2.vmfb") # Default to local relative path
THRESHOLD = float(os.getenv("THRESHOLD", "0.85")) # Default minimum safe confidence for auto-pausing
CAMERA_TYPE = os.getenv("CAMERA_TYPE", "http") # 'http' or 'local'
CAMERA_URL = os.getenv("CAMERA_URL", f"http://{PRINTER_HOST}/webcam/?action=snapshot")
CAMERA_ID = int(os.getenv("CAMERA_ID", "0")) # For local USB camera
LIGHTING_ENABLED = os.getenv("LIGHTING_ENABLED", "false").lower() == "true"



# Dry run mode
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

CAMERA_WIDTH = int(os.getenv("CAMERA_WIDTH", "640"))
CAMERA_HEIGHT = int(os.getenv("CAMERA_HEIGHT", "480"))

class Camera:
    def capture(self):
        raise NotImplementedError

class HTTPCamera(Camera):
    def __init__(self, url):
        self.url = url
    
    def capture(self):
        if DRY_RUN:
            logging.info(f"[DRY_RUN] HTTP Capture from {self.url}")
            return Image.new('RGB', (CAMERA_WIDTH, CAMERA_HEIGHT), color='gray')
            
        try:
            # Optimize: Request specific resolution if supported by the server (e.g., mjpeg streamer)
            # For now, we fetch what's available and resize locally, but the structure allows for URL tweaking
            response = requests.get(self.url, timeout=2)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content)).convert('RGB')
            return img
        except Exception as e:
            logging.error(f"HTTP Camera capture failed: {e}")
            return None

class LocalCamera(Camera):
    def __init__(self, device_id=0):
        if not DRY_RUN:
            self.cap = cv2.VideoCapture(device_id)
            # Optimize: Set resolution at hardware level
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        else:
            logging.info(f"[DRY_RUN] Local Camera {device_id} initialized")
    
    def capture(self):
        if DRY_RUN:
            logging.info("[DRY_RUN] Local Capture")
            return Image.new('RGB', (CAMERA_WIDTH, CAMERA_HEIGHT), color='gray')

        ret, frame = self.cap.read()
        if ret:
            # OpenCV returns BGR, convert to RGB for consistency with PIL
            return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        logging.error("Local Camera capture failed")
        return None

    def release(self):
        if not DRY_RUN:
            self.cap.release()

class LightingController:
    def on(self):
        pass
    def off(self):
        pass



class MoonrakerLighting(LightingController):
    def __init__(self, host, port):
        self.url = f"http://{host}:{port}/printer/gcode/script"
    
    def _send_gcode(self, gcode):
        if DRY_RUN:
            logging.info(f"[DRY_RUN] G-code: {gcode}")
            return
            
        try:
            payload = {"script": gcode}
            requests.post(self.url, json=payload, timeout=2)
            logging.info(f"Sent G-Code: {gcode}")
        except Exception as e:
            logging.error(f"Lighting control failed: {e}")

    def on(self):
        gcode = os.getenv("LIGHTING_GCODE_ON", "SET_LED LED=case_light WHITE=1.0")
        self._send_gcode(gcode)

    def off(self):
        gcode = os.getenv("LIGHTING_GCODE_OFF", "SET_LED LED=case_light WHITE=0.0")
        self._send_gcode(gcode)

class SpaghettiDetector:
    def __init__(self):
        self._init_camera()
        self._init_lighting()
        self._init_model()

    def _init_camera(self):
        if CAMERA_TYPE == "local":
            logging.info(f"Initializing Local USB Camera (ID: {CAMERA_ID})...")
            self.camera = LocalCamera(CAMERA_ID)
        else:
            logging.info(f"Initializing HTTP Camera ({CAMERA_URL})...")
            self.camera = HTTPCamera(CAMERA_URL)

    def _init_lighting(self):
        if LIGHTING_ENABLED:
            logging.info("Initializing Moonraker Lighting Control...")
            self.lighting = MoonrakerLighting(PRINTER_HOST, MOONRAKER_PORT)
        else:
            logging.info("Lighting control disabled (using dummy).")
            self.lighting = LightingController()


    def _init_model(self):
        logging.info(f"Loading Model: {MODEL_PATH}")
        if DRY_RUN:
            logging.info("[DRY_RUN] Loading Mock Model")
            return

        if ireert is None:
            raise ImportError("iree.runtime module not found. Install 'iree-runtime' or run with DRY_RUN=true.")

        try:
            config = ireert.Config("local-sync")
            vmfb = ireert.VmModule.mmap(config.vm_instance, MODEL_PATH)
            self.ctx = ireert.SystemContext(config=config)
            self.ctx.add_vm_module(vmfb)
            self.predict_fn = self.ctx.modules.module["predict"]
            logging.info("Model loaded successfully.")
        except Exception as e:
            logging.critical(f"Failed to load model: {e}")
            raise e

    def preprocess(self, img):
        # Resize to model input size (224x224)
        img_resized = img.resize((224, 224))
        input_data = np.array(img_resized, dtype=np.float32) / 127.5 - 1.0
        return np.expand_dims(input_data, axis=0)

    def pause_printer(self):
        if DRY_RUN:
            logging.warning("[DRY_RUN] PAUSE COMMAND MOCKED!")
            return

        try:
            url = f"http://{PRINTER_HOST}:{MOONRAKER_PORT}/printer/print/pause"
            requests.post(url, timeout=2)
            logging.warning("PAUSE COMMAND SENT TO PRINTER!")
        except Exception as e:
            logging.error(f"Failed to pause printer: {e}")

    def _get_printer_state(self):
        if DRY_RUN:
            return "printing"
        
        try:
            url = f"http://{PRINTER_HOST}:{MOONRAKER_PORT}/printer/objects/query?print_stats"
            response = requests.get(url, timeout=2)
            response.raise_for_status()
            data = response.json()
            return data.get("result", {}).get("status", {}).get("print_stats", {}).get("state", "error")
        except Exception as e:
            logging.error(f"Failed to fetch printer state: {e}")
            return "error"

    def run(self):
        logging.info("Starting Detection Loop...")
        if DRY_RUN:
            logging.info("[DRY_RUN] Mode Active - No hardware calls will be made.")

        backoff = 5
        max_backoff = 300

        while True:
            state = self._get_printer_state()
            if state == "error":
                logging.warning(f"Connection error, backing off for {backoff} seconds...")
                time.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)
                continue
            
            backoff = 5 # Reset on successful connection
            
            if state != "printing":
                logging.debug(f"Printer is {state}, skipping inference...")
                time.sleep(10)
                continue

            self.lighting.on()
            time.sleep(0.5) # Wait for camera exposure to adjust
            
            img = self.camera.capture()
            self.lighting.off()
            
            if img:
                if DRY_RUN:
                    # Mock inference result
                    confidence = 0.95
                else:
                    input_tensor = self.preprocess(img)
                    results = self.predict_fn(input_tensor)
                    confidence = results.to_host()[1] # Assumes index 1 is 'spaghetti' label
                
                logging.info(f"Confidence: {confidence:.2f}")
                
                if confidence > THRESHOLD:
                    logging.warning(f"SPAGHETTI DETECTED! Confidence: {confidence:.2f}")
                    self.pause_printer()
                    time.sleep(60) # Cooldown
            
            time.sleep(5) # Check interval

if __name__ == "__main__":
    detector = SpaghettiDetector()
    detector.run()
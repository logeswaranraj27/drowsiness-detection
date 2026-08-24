"""
Drowsiness Detection - Live Camera System
==============================================
Runs your trained model on a live webcam feed:
  - Detects your face each frame (OpenCV Haar cascade)
  - Classifies it as ALERT / DROWSY using your trained CNN
  - Tracks consecutive drowsy frames -> triggers visual + audio alert
  - Logs every event with timestamp + confidence to a JSON file
  - On exit: prints a performance report (if you used ground-truth
    labelling with the spacebar) and saves a session graph

REQUIRES:
    drowsiness_model.h5  and  class_names.json
    (produced by running train_model.py first)

USAGE:
    python live_detection.py

CONTROLS:
    q       - quit
    SPACE   - toggle ground-truth label (ALERT <-> DROWSY) for accuracy testing
"""

import os
import json
import time
import platform
from collections import deque
from datetime import datetime

import cv2
import numpy as np
from tensorflow.keras.models import load_model
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ============================================================
# CONFIG
# ============================================================
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
REPORTS_DIR = os.path.join(ROOT_DIR, "others", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def _find_path(filename, search_dirs):
    for d in search_dirs:
        p = os.path.join(d, filename)
        if os.path.exists(p):
            return p
    return os.path.join(search_dirs[0], filename)

MODEL_PATH = _find_path("drowsiness_model.h5", [BACKEND_DIR, ROOT_DIR])
CLASS_NAMES_PATH = _find_path("class_names.json", [BACKEND_DIR, ROOT_DIR])
IMG_SIZE = 145
DROWSY_FRAME_THRESHOLD = 15     # consecutive drowsy frames before alert fires
HISTORY_LEN = 30                # rolling window for smoothing
EVENT_LOG_PATH = os.path.join(REPORTS_DIR, "event_log.json")
SESSION_REPORT_PATH = os.path.join(REPORTS_DIR, "session_report.png")
# ============================================================


def beep():
    """Cross-platform alert beep. Fails silently if unsupported."""
    try:
        if platform.system() == "Windows":
            import winsound
            winsound.Beep(1000, 400)
        else:
            # terminal bell as a fallback beep on macOS/Linux
            print("\a", end="", flush=True)
    except Exception:
        pass


def load_class_mapping(path):
    with open(path, "r") as f:
        mapping = json.load(f)  # e.g. {"Alert": 0, "Drowsy": 1}

    # figure out which index corresponds to "drowsy" using keyword match
    drowsy_keywords = ("drowsy", "closed", "sleep", "sleepy", "fatigue", "tired")
    drowsy_idx = None
    for name, idx in mapping.items():
        if any(k in name.lower() for k in drowsy_keywords):
            drowsy_idx = idx
            break
    if drowsy_idx is None:
        # fallback: assume index 1 is drowsy
        drowsy_idx = 1
        print(f"[WARN] Could not infer which class is 'drowsy' from {mapping}. "
              f"Assuming index 1. Edit load_class_mapping() if this is wrong.")

    idx_to_name = {v: k for k, v in mapping.items()}
    print(f"Class mapping: {mapping}  ->  treating index {drowsy_idx} "
          f"('{idx_to_name[drowsy_idx]}') as DROWSY")
    return drowsy_idx


def main():
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: '{MODEL_PATH}' not found. Run train_model.py first.")
        return
    if not os.path.exists(CLASS_NAMES_PATH):
        print(f"ERROR: '{CLASS_NAMES_PATH}' not found. Run train_model.py first.")
        return

    print("Loading model...")
    model = load_model(MODEL_PATH)
    drowsy_idx = load_class_mapping(CLASS_NAMES_PATH)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open webcam (index 0). Check your camera connection.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    prob_history = deque(maxlen=HISTORY_LEN)
    consecutive_drowsy = 0
    events = []
    ground_truth = None  # None until user toggles with spacebar
    y_true_log, y_pred_log = [], []

    prev_time = time.time()
    print("\nStarting live detection. Press 'q' to quit, SPACE to toggle ground-truth label.\n")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame from camera.")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))

            state = "NO FACE"
            confidence = 0.0
            box_color = (200, 200, 200)

            if len(faces) > 0:
                # use the largest detected face
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                face_roi = frame[y:y + h, x:x + w]

                face_resized = cv2.resize(face_roi, (IMG_SIZE, IMG_SIZE))
                face_norm = face_resized.astype("float32") / 255.0
                face_input = np.expand_dims(face_norm, axis=0)

                prob = float(model.predict(face_input, verbose=0)[0][0])
                drowsy_prob = prob if drowsy_idx == 1 else (1 - prob)
                prob_history.append(drowsy_prob)
                smoothed = float(np.mean(prob_history))

                is_drowsy_frame = smoothed >= 0.5
                consecutive_drowsy = consecutive_drowsy + 1 if is_drowsy_frame else 0

                alert_triggered = consecutive_drowsy >= DROWSY_FRAME_THRESHOLD
                state = "DROWSY" if alert_triggered else ("WATCHING" if is_drowsy_frame else "ALERT")
                confidence = smoothed
                box_color = (0, 0, 255) if alert_triggered else (0, 200, 0)

                if alert_triggered:
                    beep()

                cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)

                events.append({
                    "timestamp": datetime.now().isoformat(),
                    "state": state,
                    "confidence": round(confidence, 4),
                })

                if ground_truth is not None:
                    y_true_log.append(1 if ground_truth == "DROWSY" else 0)
                    y_pred_log.append(1 if state == "DROWSY" else 0)

            # ---- dashboard overlay ----
            now = time.time()
            fps = 1.0 / max(now - prev_time, 1e-6)
            prev_time = now

            cv2.putText(frame, f"State: {state}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, box_color, 2)
            cv2.putText(frame, f"Confidence: {confidence:.2%}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            if ground_truth is not None:
                cv2.putText(frame, f"Ground truth: {ground_truth}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)

            cv2.imshow("Drowsiness Detection", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord(" "):
                ground_truth = "DROWSY" if ground_truth != "DROWSY" else "ALERT"
                print(f"Ground truth set to: {ground_truth}")

    finally:
        cap.release()
        cv2.destroyAllWindows()

    # ---- save event log ----
    with open(EVENT_LOG_PATH, "w") as f:
        json.dump(events, f, indent=2)
    print(f"\nSaved {len(events)} events to {EVENT_LOG_PATH}")

    # ---- session summary ----
    if events:
        drowsy_count = sum(1 for e in events if e["state"] == "DROWSY")
        alert_count = sum(1 for e in events if e["state"] == "ALERT")
        avg_conf = np.mean([e["confidence"] for e in events])
        print("=" * 60)
        print("SESSION SUMMARY")
        print("=" * 60)
        print(f"Total frames logged: {len(events)}")
        print(f"ALERT frames:  {alert_count}")
        print(f"DROWSY frames: {drowsy_count}")
        print(f"Average confidence: {avg_conf:.2%}")

        # plot state-over-time
        confidences = [e["confidence"] for e in events]
        plt.figure(figsize=(10, 4))
        plt.plot(confidences)
        plt.axhline(0.5, color="red", linestyle="--", label="drowsy threshold")
        plt.title("Drowsiness Confidence Over Session")
        plt.xlabel("Frame")
        plt.ylabel("Drowsy Confidence")
        plt.legend()
        plt.tight_layout()
        plt.savefig(SESSION_REPORT_PATH)
        print(f"Saved session graph to {SESSION_REPORT_PATH}")

    # ---- accuracy metrics if ground truth was used ----
    if y_true_log:
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
        acc = accuracy_score(y_true_log, y_pred_log)
        prec = precision_score(y_true_log, y_pred_log, zero_division=0)
        rec = recall_score(y_true_log, y_pred_log, zero_division=0)
        f1 = f1_score(y_true_log, y_pred_log, zero_division=0)
        cm = confusion_matrix(y_true_log, y_pred_log)

        print("\n" + "=" * 60)
        print("PERFORMANCE (vs. ground-truth labels you toggled with SPACE)")
        print("=" * 60)
        print(f"Accuracy:  {acc:.2%}")
        print(f"Precision: {prec:.2%}")
        print(f"Recall:    {rec:.2%}")
        print(f"F1-Score:  {f1:.2%}")
        print("Confusion Matrix:")
        print(cm)


if __name__ == "__main__":
    main()

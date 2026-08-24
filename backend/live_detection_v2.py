"""
Drowsiness Detection - Live Camera System (v2)
==============================================
Fixes vs v1:
  - Uses MediaPipe FaceMesh landmarks to measure real Eye Aspect Ratio (EAR)
    and Mouth Aspect Ratio (MAR) -- detects closed eyes / yawning directly,
    instead of relying only on the CNN (which was biased toward "hand
    covering mouth" poses from the training data).
  - CNN prediction still runs as a secondary confidence signal, but EAR/MAR
    now drive the actual DROWSY alert.
  - Faster: MediaPipe is lighter than Haar+CNN every frame, and the CNN now
    only runs every few frames instead of every frame -- fixes FPS drop.
  - Continuous alarm (not a single beep) + on-screen "WAKE UP" warning while
    drowsy persists, running on a background thread so video doesn't freeze.

REQUIRES:
    pip install mediapipe
    drowsiness_model.h5 and class_names.json (from train_model.py) - optional,
    script still works with EAR/MAR alone if these are missing.

CONTROLS:
    q       - quit
    SPACE   - toggle ground-truth label (ALERT <-> DROWSY) for accuracy testing
"""

import os
import json
import time
import threading
import platform
from collections import deque
from datetime import datetime

import cv2
import numpy as np
import mediapipe as mp
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

EAR_THRESHOLD = 0.21          # below this = eyes considered closed
MAR_THRESHOLD = 0.6           # above this = yawning
EAR_CONSEC_FRAMES = 15        # consecutive closed-eye frames before DROWSY alert
MAR_CONSEC_FRAMES = 15        # consecutive yawn frames before YAWNING alert
CNN_EVERY_N_FRAMES = 5        # only run the (slow) CNN every N frames -- keeps FPS up

EVENT_LOG_PATH = os.path.join(REPORTS_DIR, "event_log.json")
SESSION_REPORT_PATH = os.path.join(REPORTS_DIR, "session_report.png")
# ============================================================

# MediaPipe FaceMesh eye/mouth landmark indices
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
MOUTH = [61, 291, 39, 181, 0, 17, 269, 405]

_alarm_stop = threading.Event()
_alarm_thread = None


def _dist(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))


def eye_aspect_ratio(landmarks, eye_idx, w, h):
    pts = [(landmarks[i].x * w, landmarks[i].y * h) for i in eye_idx]
    vertical1 = _dist(pts[1], pts[5])
    vertical2 = _dist(pts[2], pts[4])
    horizontal = _dist(pts[0], pts[3])
    if horizontal == 0:
        return 0.3
    return (vertical1 + vertical2) / (2.0 * horizontal)


def mouth_aspect_ratio(landmarks, mouth_idx, w, h):
    pts = [(landmarks[i].x * w, landmarks[i].y * h) for i in mouth_idx]
    vertical1 = _dist(pts[2], pts[3])
    vertical2 = _dist(pts[4], pts[5])
    vertical3 = _dist(pts[6], pts[7])
    horizontal = _dist(pts[0], pts[1])
    if horizontal == 0:
        return 0.0
    return (vertical1 + vertical2 + vertical3) / (2.0 * horizontal)


def _alarm_loop():
    """Repeats a beep every 0.6s until stopped. Runs on its own thread."""
    is_windows = platform.system() == "Windows"
    if is_windows:
        import winsound
    while not _alarm_stop.is_set():
        try:
            if is_windows:
                winsound.Beep(1400, 300)
            else:
                print("\a", end="", flush=True)
        except Exception:
            pass
        time.sleep(0.3)


def start_alarm():
    global _alarm_thread
    if _alarm_thread is None or not _alarm_thread.is_alive():
        _alarm_stop.clear()
        _alarm_thread = threading.Thread(target=_alarm_loop, daemon=True)
        _alarm_thread.start()


def stop_alarm():
    _alarm_stop.set()


def load_cnn():
    """Loads the CNN model if available. Returns (model, drowsy_idx) or (None, None)."""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(CLASS_NAMES_PATH):
        print("[INFO] CNN model not found - running with EAR/MAR detection only.")
        return None, None
    from tensorflow.keras.models import load_model
    print("Loading CNN model...")
    model = load_model(MODEL_PATH)
    with open(CLASS_NAMES_PATH, "r") as f:
        mapping = json.load(f)
    drowsy_keywords = ("drowsy", "closed", "sleep", "sleepy", "fatigue", "tired")
    drowsy_idx = next((idx for name, idx in mapping.items()
                        if any(k in name.lower() for k in drowsy_keywords)), 1)
    print(f"CNN class mapping: {mapping} -> drowsy index = {drowsy_idx}")
    return model, drowsy_idx


def main():
    model, drowsy_idx = load_cnn()

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open webcam (index 0). Check your camera connection.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    closed_eye_counter = 0
    yawn_counter = 0
    frame_count = 0
    cnn_confidence = 0.0
    events = []
    ground_truth = None
    y_true_log, y_pred_log = [], []

    prev_time = time.time()
    print("\nStarting live detection. Press 'q' to quit, SPACE to toggle ground-truth label.\n")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame from camera.")
                break

            frame_count += 1
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            state = "NO FACE"
            box_color = (200, 200, 200)
            ear, mar = 0.3, 0.0

            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0].landmark

                left_ear = eye_aspect_ratio(landmarks, LEFT_EYE, w, h)
                right_ear = eye_aspect_ratio(landmarks, RIGHT_EYE, w, h)
                ear = (left_ear + right_ear) / 2.0
                mar = mouth_aspect_ratio(landmarks, MOUTH, w, h)

                closed_eye_counter = closed_eye_counter + 1 if ear < EAR_THRESHOLD else 0
                yawn_counter = yawn_counter + 1 if mar > MAR_THRESHOLD else 0

                # Calculate bounding box from ALL landmarks (needed for drawing box)
                xs = [lm.x * w for lm in landmarks]
                ys = [lm.y * h for lm in landmarks]
                x1b, y1b = int(min(xs)), int(min(ys))
                x2b, y2b = int(max(xs)), int(max(ys))

                # Run the (slower) CNN only every N frames, reuse last score otherwise
                if model is not None and frame_count % CNN_EVERY_N_FRAMES == 0:
                    x1, x2 = max(int(min(xs)), 0), min(int(max(xs)), w)
                    y1, y2 = max(int(min(ys)), 0), min(int(max(ys)), h)
                    if x2 > x1 and y2 > y1:
                        face_roi = frame[y1:y2, x1:x2]
                        face_resized = cv2.resize(face_roi, (IMG_SIZE, IMG_SIZE))
                        face_norm = face_resized.astype("float32") / 255.0
                        face_input = np.expand_dims(face_norm, axis=0)
                        prob = float(model.predict(face_input, verbose=0)[0][0])
                        cnn_confidence = prob if drowsy_idx == 1 else (1 - prob)

                eyes_closed_alert = closed_eye_counter >= EAR_CONSEC_FRAMES
                yawning_alert = yawn_counter >= MAR_CONSEC_FRAMES

                if eyes_closed_alert or yawning_alert:
                    state = "DROWSY"
                    box_color = (0, 0, 255)
                    start_alarm()
                elif closed_eye_counter > 0 or yawn_counter > 0:
                    state = "WATCHING"
                    box_color = (0, 165, 255)
                    stop_alarm()
                else:
                    state = "ALERT"
                    box_color = (0, 200, 0)
                    stop_alarm()

                cv2.rectangle(frame, (x1b, y1b), (x2b, y2b), box_color, 2)

                events.append({
                    "timestamp": datetime.now().isoformat(),
                    "state": state,
                    "EAR": round(ear, 4),
                    "MAR": round(mar, 4),
                    "cnn_confidence": round(cnn_confidence, 4),
                })

                if ground_truth is not None:
                    y_true_log.append(1 if ground_truth == "DROWSY" else 0)
                    y_pred_log.append(1 if state == "DROWSY" else 0)
            else:
                stop_alarm()

            # ---- dashboard overlay ----
            now = time.time()
            fps = 1.0 / max(now - prev_time, 1e-6)
            prev_time = now

            cv2.putText(frame, f"State: {state}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, box_color, 2)
            cv2.putText(frame, f"EAR: {ear:.3f}  MAR: {mar:.3f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, f"CNN conf: {cnn_confidence:.2%}", (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            if ground_truth is not None:
                cv2.putText(frame, f"Ground truth: {ground_truth}", (10, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)

            if state == "DROWSY":
                cv2.putText(frame, "!! WAKE UP - DON'T SLEEP !!", (10, h - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)

            cv2.imshow("Drowsiness Detection", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord(" "):
                ground_truth = "DROWSY" if ground_truth != "DROWSY" else "ALERT"
                print(f"Ground truth set to: {ground_truth}")

    finally:
        stop_alarm()
        cap.release()
        cv2.destroyAllWindows()
        face_mesh.close()

    # ---- save event log ----
    with open(EVENT_LOG_PATH, "w") as f:
        json.dump(events, f, indent=2)
    print(f"\nSaved {len(events)} events to {EVENT_LOG_PATH}")

    if events:
        drowsy_count = sum(1 for e in events if e["state"] == "DROWSY")
        alert_count = sum(1 for e in events if e["state"] == "ALERT")
        avg_ear = np.mean([e["EAR"] for e in events])
        print("=" * 60)
        print("SESSION SUMMARY")
        print("=" * 60)
        print(f"Total frames logged: {len(events)}")
        print(f"ALERT frames:  {alert_count}")
        print(f"DROWSY frames: {drowsy_count}")
        print(f"Average EAR: {avg_ear:.3f}")

        ears = [e["EAR"] for e in events]
        plt.figure(figsize=(10, 4))
        plt.plot(ears, label="EAR")
        plt.axhline(EAR_THRESHOLD, color="red", linestyle="--", label="closed-eye threshold")
        plt.title("Eye Aspect Ratio Over Session")
        plt.xlabel("Frame")
        plt.ylabel("EAR")
        plt.legend()
        plt.tight_layout()
        plt.savefig(SESSION_REPORT_PATH)
        print(f"Saved session graph to {SESSION_REPORT_PATH}")

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
    
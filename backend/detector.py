"""
detector.py — wraps the TF model + MediaPipe FaceMesh as a reusable class
"""

import os
import json
import numpy as np
import cv2

IMG_SIZE = 145

LEFT_EYE  = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
MOUTH     = [61, 291, 39, 181, 0, 17, 269, 405]


def _dist(p1, p2):
    return float(np.linalg.norm(np.array(p1) - np.array(p2)))


def _ear(landmarks, idx, w, h):
    pts = [(landmarks[i].x * w, landmarks[i].y * h) for i in idx]
    v1 = _dist(pts[1], pts[5])
    v2 = _dist(pts[2], pts[4])
    hz = _dist(pts[0], pts[3])
    return (v1 + v2) / (2.0 * hz) if hz else 0.3


def _mar(landmarks, idx, w, h):
    pts = [(landmarks[i].x * w, landmarks[i].y * h) for i in idx]
    v1 = _dist(pts[2], pts[3])
    v2 = _dist(pts[4], pts[5])
    v3 = _dist(pts[6], pts[7])
    hz = _dist(pts[0], pts[1])
    return (v1 + v2 + v3) / (2.0 * hz) if hz else 0.0


class DrowsinessDetector:
    EAR_THRESHOLD   = 0.21
    MAR_THRESHOLD   = 0.60
    CONSEC_FRAMES   = 15
    CNN_EVERY_N     = 5

    def __init__(self, model_path=None, class_names_path=None):
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(backend_dir)

        # Resolve model_path
        candidates_model = [
            model_path,
            os.path.join(backend_dir, "drowsiness_model.h5"),
            os.path.join(root_dir, "drowsiness_model.h5"),
            os.path.join(root_dir, "backend", "drowsiness_model.h5"),
        ]
        resolved_model = next((p for p in candidates_model if p and os.path.exists(p)), None)

        # Resolve class_names_path
        candidates_classes = [
            class_names_path,
            os.path.join(backend_dir, "class_names.json"),
            os.path.join(root_dir, "class_names.json"),
            os.path.join(root_dir, "backend", "class_names.json"),
        ]
        resolved_classes = next((p for p in candidates_classes if p and os.path.exists(p)), None)

        # MediaPipe (always available)
        import mediapipe as mp
        self._mp_face = mp.solutions.face_mesh
        self._face_mesh = self._mp_face.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        # CNN (optional)
        self._model     = None
        self._drowsy_idx = 1
        if resolved_model and resolved_classes:
            try:
                from tensorflow.keras.models import load_model
                self._model = load_model(resolved_model)
                with open(resolved_classes) as f:
                    mapping = json.load(f)
                kw = ("drowsy", "closed", "sleep", "sleepy", "fatigue", "tired")
                self._drowsy_idx = next(
                    (idx for name, idx in mapping.items()
                     if any(k in name.lower() for k in kw)),
                    1,
                )
                print(f"[detector] CNN loaded from {resolved_model}. Drowsy index = {self._drowsy_idx}")
            except Exception as e:
                print(f"[detector] CNN load failed: {e}")

        # rolling state
        self._closed_ctr  = 0
        self._yawn_ctr    = 0
        self._frame_count = 0
        self._cnn_conf    = 0.0

    def reset(self):
        self._closed_ctr  = 0
        self._yawn_ctr    = 0
        self._frame_count = 0
        self._cnn_conf    = 0.0

    def process_frame_bytes(self, jpeg_bytes: bytes) -> dict:
        """
        Accept a JPEG bytes object (from the browser canvas),
        return a dict: {state, ear, mar, cnn_confidence, face_detected}
        """
        arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return {"state": "NO FACE", "ear": 0.3, "mar": 0.0,
                    "cnn_confidence": 0.0, "face_detected": False}

        return self._process(frame)

    def process_frame_b64(self, b64_str: str) -> dict:
        """Accept base64-encoded JPEG string from the browser."""
        import base64
        # strip data-URL prefix if present
        if "," in b64_str:
            b64_str = b64_str.split(",", 1)[1]
        jpeg_bytes = base64.b64decode(b64_str)
        return self.process_frame_bytes(jpeg_bytes)

    def _process(self, frame) -> dict:
        self._frame_count += 1
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            self._closed_ctr = 0
            self._yawn_ctr   = 0
            return {"state": "NO FACE", "ear": 0.3, "mar": 0.0,
                    "cnn_confidence": self._cnn_conf, "face_detected": False}

        landmarks = results.multi_face_landmarks[0].landmark

        l_ear = _ear(landmarks, LEFT_EYE,  w, h)
        r_ear = _ear(landmarks, RIGHT_EYE, w, h)
        ear   = (l_ear + r_ear) / 2.0
        mar   = _mar(landmarks, MOUTH, w, h)

        self._closed_ctr = self._closed_ctr + 1 if ear < self.EAR_THRESHOLD else 0
        self._yawn_ctr   = self._yawn_ctr   + 1 if mar > self.MAR_THRESHOLD else 0

        # CNN every N frames
        if self._model is not None and self._frame_count % self.CNN_EVERY_N == 0:
            xs = [lm.x * w for lm in landmarks]
            ys = [lm.y * h for lm in landmarks]
            x1, x2 = max(int(min(xs)), 0), min(int(max(xs)), w)
            y1, y2 = max(int(min(ys)), 0), min(int(max(ys)), h)
            if x2 > x1 and y2 > y1:
                roi = cv2.resize(frame[y1:y2, x1:x2], (IMG_SIZE, IMG_SIZE))
                inp = np.expand_dims(roi.astype("float32") / 255.0, 0)
                prob = float(self._model.predict(inp, verbose=0)[0][0])
                self._cnn_conf = prob if self._drowsy_idx == 1 else (1 - prob)

        eyes_alert = self._closed_ctr >= self.CONSEC_FRAMES
        yawn_alert = self._yawn_ctr   >= self.CONSEC_FRAMES

        if eyes_alert or yawn_alert:
            state = "DROWSY"
        elif self._closed_ctr > 0 or self._yawn_ctr > 0:
            state = "WATCHING"
        else:
            state = "ALERT"

        return {
            "state":          state,
            "ear":            round(ear, 4),
            "mar":            round(mar, 4),
            "cnn_confidence": round(self._cnn_conf, 4),
            "face_detected":  True,
        }

    def close(self):
        self._face_mesh.close()

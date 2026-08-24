"""
app.py — Flask backend for the Drowsiness Detection Web App
"""

import os
import sys
import json
from datetime import datetime
from functools import wraps

# Ensure project root is in sys.path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from flask import (Flask, request, jsonify, session,
                   render_template, redirect, url_for)
from werkzeug.security import generate_password_hash, check_password_hash

try:
    from database import database as db
except ImportError:
    import database as db

from detector import DrowsinessDetector

# Point Flask to the frontend/templates and frontend/static directories
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
TEMPLATE_DIR = os.path.join(FRONTEND_DIR, "templates")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR
)
app.secret_key = os.environ.get("SECRET_KEY", "drowsy-app-secret-key-2024")
app.config["SESSION_COOKIE_HTTPONLY"] = True

# ── Init DB + detector on startup ──────────────────────────────────────────────
db.init_db()
detector = DrowsinessDetector()

# In-memory buffer for the current active session's events (per server process)
_active_session: dict = {}   # {session_id, events[], vehicle_id}


# ── Auth helpers ───────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json:
                return jsonify({"error": "Unauthorized"}), 401
            return redirect(url_for("auth_page"))
        return f(*args, **kwargs)
    return wrapper


def current_user():
    return db.get_user_by_id(session["user_id"])


# ── Pages ──────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard_page"))
    return redirect(url_for("auth_page"))


@app.route("/auth")
def auth_page():
    if "user_id" in session:
        return redirect(url_for("dashboard_page"))
    return render_template("auth.html")


@app.route("/dashboard")
@login_required
def dashboard_page():
    return render_template("dashboard.html")


# ── Auth API ───────────────────────────────────────────────────────────────────

@app.route("/api/signup", methods=["POST"])
def api_signup():
    data = request.get_json(force=True)
    name     = (data.get("name") or "").strip()
    email    = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()
    language = (data.get("language") or "en").strip()

    if not name or not email or not password:
        return jsonify({"error": "All fields are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if db.get_user_by_email(email):
        return jsonify({"error": "Email already registered"}), 409

    uid = db.create_user(name, email, generate_password_hash(password), language)
    session["user_id"] = uid
    return jsonify({"ok": True, "name": name})


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(force=True)
    email    = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()

    user = db.get_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = user["id"]
    return jsonify({"ok": True, "name": user["name"], "language": user["language"]})


@app.route("/api/logout", methods=["POST"])
@login_required
def api_logout():
    session.clear()
    return jsonify({"ok": True})


# ── Profile API ────────────────────────────────────────────────────────────────

@app.route("/api/profile", methods=["GET"])
@login_required
def api_get_profile():
    u = current_user()
    return jsonify({
        "id":       u["id"],
        "name":     u["name"],
        "email":    u["email"],
        "language": u["language"],
    })


@app.route("/api/profile", methods=["PUT"])
@login_required
def api_update_profile():
    data     = request.get_json(force=True)
    name     = (data.get("name") or "").strip()
    language = (data.get("language") or "en").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    db.update_user(session["user_id"], name, language)
    return jsonify({"ok": True})


# ── Vehicles API ───────────────────────────────────────────────────────────────

@app.route("/api/vehicles", methods=["GET"])
@login_required
def api_get_vehicles():
    return jsonify(db.get_vehicles(session["user_id"]))


@app.route("/api/vehicles", methods=["POST"])
@login_required
def api_add_vehicle():
    data  = request.get_json(force=True)
    name  = (data.get("name") or "").strip()
    vtype = (data.get("type") or "Car").strip()
    plate = (data.get("plate") or "").strip()
    if not name:
        return jsonify({"error": "Vehicle name is required"}), 400
    vid = db.add_vehicle(session["user_id"], name, vtype, plate)
    return jsonify({"ok": True, "id": vid})


@app.route("/api/vehicles/<int:vid>", methods=["DELETE"])
@login_required
def api_delete_vehicle(vid):
    db.delete_vehicle(vid, session["user_id"])
    return jsonify({"ok": True})


# ── Detection API ──────────────────────────────────────────────────────────────

@app.route("/api/detect", methods=["POST"])
@login_required
def api_detect():
    """
    Expects JSON: { "frame": "<base64 JPEG data-URL>", "session_id": <int> }
    Returns:      { state, ear, mar, cnn_confidence, face_detected }
    """
    data = request.get_json(force=True)
    b64  = data.get("frame", "")
    if not b64:
        return jsonify({"error": "No frame provided"}), 400

    result = detector.process_frame_b64(b64)

    # buffer event for this session
    sid = data.get("session_id")
    if sid and sid == _active_session.get("session_id"):
        _active_session["events"].append({
            "timestamp":  datetime.now().isoformat(),
            "state":      result["state"],
            "ear":        result["ear"],
            "mar":        result["mar"],
            "confidence": result["cnn_confidence"],
        })

    return jsonify(result)


# ── Session API ────────────────────────────────────────────────────────────────

@app.route("/api/sessions/start", methods=["POST"])
@login_required
def api_start_session():
    global _active_session
    data       = request.get_json(force=True)
    vehicle_id = data.get("vehicle_id")  # may be None
    start_time = datetime.now().isoformat()
    sid = db.start_session(session["user_id"], vehicle_id, start_time)
    detector.reset()
    _active_session = {"session_id": sid, "events": [], "vehicle_id": vehicle_id}
    return jsonify({"ok": True, "session_id": sid})


@app.route("/api/sessions/end", methods=["POST"])
@login_required
def api_end_session():
    global _active_session
    if not _active_session:
        return jsonify({"error": "No active session"}), 400

    sid    = _active_session["session_id"]
    events = _active_session["events"]

    total   = len(events)
    drowsy  = sum(1 for e in events if e["state"] == "DROWSY")
    alert   = sum(1 for e in events if e["state"] == "ALERT")
    avg_conf = (sum(e["confidence"] for e in events) / total) if total else 0.0
    avg_ear  = (sum(e["ear"]        for e in events) / total) if total else 0.0

    db.end_session(sid, datetime.now().isoformat(),
                   total, drowsy, alert, avg_conf, avg_ear)
    db.save_session_events(sid, events)
    _active_session = {}

    return jsonify({
        "ok":           True,
        "session_id":   sid,
        "total_frames": total,
        "drowsy_frames": drowsy,
        "alert_frames": alert,
        "avg_confidence": round(avg_conf, 4),
    })


@app.route("/api/sessions", methods=["GET"])
@login_required
def api_get_sessions():
    return jsonify(db.get_sessions(session["user_id"]))


@app.route("/api/sessions/<int:sid>/events", methods=["GET"])
@login_required
def api_get_session_events(sid):
    return jsonify(db.get_session_events(sid, session["user_id"]))


@app.route("/api/stats", methods=["GET"])
@login_required
def api_stats():
    sessions = db.get_sessions(session["user_id"])
    total_sessions = len(sessions)
    total_drowsy   = sum(s["drowsy_frames"] for s in sessions)
    total_frames   = sum(s["total_frames"] for s in sessions)
    safe_score     = round((1 - total_drowsy / total_frames) * 100, 1) if total_frames else 100.0
    return jsonify({
        "total_sessions": total_sessions,
        "total_drowsy_frames": total_drowsy,
        "total_frames": total_frames,
        "safe_score": safe_score,
    })


# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  Drowsiness Detection Web App")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)

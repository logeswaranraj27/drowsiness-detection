"""
database.py — Firebase Realtime Database integration with local SQLite fallback.

Firebase Database Endpoint:
https://drwosiness-default-rtdb.asia-southeast1.firebasedatabase.app
"""

import os
import sys
import json
import time
import sqlite3
from datetime import datetime
import urllib.request
import urllib.error

# ── Paths & Configuration ──────────────────────────────────────────────────────
DB_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(DB_DIR)
LOCAL_SQLITE_PATH = os.path.join(DB_DIR, "drowsiness_app.db")

# User's Firebase Realtime Database URL
FIREBASE_DATABASE_URL = os.environ.get(
    "FIREBASE_DATABASE_URL",
    "https://drwosiness-default-rtdb.asia-southeast1.firebasedatabase.app"
).rstrip("/")

# Service account key file locations to check
CANDIDATE_KEY_PATHS = [
    os.environ.get("FIREBASE_CRED_PATH", ""),
    os.path.join(ROOT_DIR, "serviceAccountKey.json"),
    os.path.join(DB_DIR, "serviceAccountKey.json"),
    os.path.join(ROOT_DIR, "firebase-key.json"),
]

# Check for Firebase Admin SDK or REST with Service Account
_firebase_admin_initialized = False
_access_token = None
_token_expiry = 0


def _find_service_account_path():
    for p in CANDIDATE_KEY_PATHS:
        if p and os.path.isfile(p):
            return p
    return None


def _get_firebase_access_token():
    """Generates an OAuth2 access token from serviceAccountKey.json if present."""
    global _access_token, _token_expiry
    now = time.time()
    if _access_token and now < _token_expiry - 60:
        return _access_token

    key_path = _find_service_account_path()
    if not key_path:
        return None

    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request

        scopes = [
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/firebase.database"
        ]
        creds = service_account.Credentials.from_service_account_file(key_path, scopes=scopes)
        creds.refresh(Request())
        _access_token = creds.token
        _token_expiry = creds.expiry.timestamp() if creds.expiry else (now + 3600)
        return _access_token
    except Exception as e:
        print(f"[Firebase DB] Warning: Could not generate OAuth token: {e}")
        return None


def _fb_request(method, path, data=None):
    """
    Sends an authenticated REST request to Firebase Realtime Database.
    Returns parsed JSON result, or raises on fatal errors.
    """
    clean_path = path.strip("/")
    url = f"{FIREBASE_DATABASE_URL}/{clean_path}.json"

    token = _get_firebase_access_token()
    if token:
        url += f"?access_token={token}"
    elif os.environ.get("FIREBASE_AUTH_SECRET"):
        url += f"?auth={os.environ.get('FIREBASE_AUTH_SECRET')}"

    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data is not None else None

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content and content != "null" else None
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Firebase HTTP {e.code} on {method} /{clean_path}: {err_body}")


def _is_firebase_configured():
    return bool(_find_service_account_path() or os.environ.get("FIREBASE_AUTH_SECRET"))


# ── SQLite Fallback Helpers (Used if serviceAccountKey.json is not yet present) ─

def get_sqlite_conn():
    conn = sqlite3.connect(LOCAL_SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    key_path = _find_service_account_path()
    if key_path:
        print("=" * 60)
        print(f"  [Firebase DB] Connected to Realtime Database:")
        print(f"  Endpoint: {FIREBASE_DATABASE_URL}")
        print(f"  Credentials: {os.path.basename(key_path)}")
        print("=" * 60)
    else:
        print("=" * 60)
        print("  [Notice] serviceAccountKey.json not found in project directory.")
        print("  Using local SQLite (drowsiness_app.db) as active storage.")
        print(f"  To connect to your Firebase database ({FIREBASE_DATABASE_URL}),")
        print("  download serviceAccountKey.json from Firebase Console into this folder.")
        print("=" * 60)

    # Initialize local SQLite tables as fallback
    with get_sqlite_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL,
                email         TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                language      TEXT    NOT NULL DEFAULT 'en',
                created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS vehicles (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name      TEXT    NOT NULL,
                type      TEXT    NOT NULL DEFAULT 'Car',
                plate     TEXT    NOT NULL DEFAULT '',
                created_at TEXT   NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                vehicle_id     INTEGER REFERENCES vehicles(id) ON DELETE SET NULL,
                start_time     TEXT    NOT NULL,
                end_time       TEXT,
                total_frames   INTEGER NOT NULL DEFAULT 0,
                drowsy_frames  INTEGER NOT NULL DEFAULT 0,
                alert_frames   INTEGER NOT NULL DEFAULT 0,
                avg_confidence REAL    NOT NULL DEFAULT 0.0,
                avg_ear        REAL    NOT NULL DEFAULT 0.0
            );

            CREATE TABLE IF NOT EXISTS session_events (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                timestamp  TEXT    NOT NULL,
                state      TEXT    NOT NULL,
                ear        REAL    NOT NULL DEFAULT 0.0,
                mar        REAL    NOT NULL DEFAULT 0.0,
                confidence REAL    NOT NULL DEFAULT 0.0
            );
        """)


# ── Users ──────────────────────────────────────────────────────────────────────

def create_user(name, email, password_hash, language="en"):
    if _is_firebase_configured():
        user_id = int(time.time() * 1000)
        created_at = datetime.now().isoformat()
        user_data = {
            "id": user_id,
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "language": language,
            "created_at": created_at
        }
        _fb_request("PUT", f"users/{user_id}", user_data)
        return user_id

    # Fallback to SQLite
    with get_sqlite_conn() as conn:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, language) VALUES (?,?,?,?)",
            (name, email, password_hash, language),
        )
        return cur.lastrowid


def get_user_by_email(email):
    if _is_firebase_configured():
        users = _fb_request("GET", "users") or {}
        if isinstance(users, dict):
            for uid, u in users.items():
                if isinstance(u, dict) and u.get("email", "").lower() == email.lower():
                    return u
        return None

    # Fallback to SQLite
    with get_sqlite_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id):
    if _is_firebase_configured():
        u = _fb_request("GET", f"users/{user_id}")
        return u if isinstance(u, dict) else None

    # Fallback to SQLite
    with get_sqlite_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None


def update_user(user_id, name, language):
    if _is_firebase_configured():
        _fb_request("PATCH", f"users/{user_id}", {"name": name, "language": language})
        return

    # Fallback to SQLite
    with get_sqlite_conn() as conn:
        conn.execute(
            "UPDATE users SET name=?, language=? WHERE id=?",
            (name, language, user_id),
        )


# ── Vehicles ───────────────────────────────────────────────────────────────────

def get_vehicles(user_id):
    if _is_firebase_configured():
        vehicles_dict = _fb_request("GET", "vehicles") or {}
        result = []
        if isinstance(vehicles_dict, dict):
            for vid, v in vehicles_dict.items():
                if isinstance(v, dict) and str(v.get("user_id")) == str(user_id):
                    result.append(v)
        result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return result

    # Fallback to SQLite
    with get_sqlite_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM vehicles WHERE user_id=? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def add_vehicle(user_id, name, v_type, plate):
    if _is_firebase_configured():
        vid = int(time.time() * 1000)
        v_data = {
            "id": vid,
            "user_id": user_id,
            "name": name,
            "type": v_type,
            "plate": plate,
            "created_at": datetime.now().isoformat()
        }
        _fb_request("PUT", f"vehicles/{vid}", v_data)
        return vid

    # Fallback to SQLite
    with get_sqlite_conn() as conn:
        cur = conn.execute(
            "INSERT INTO vehicles (user_id, name, type, plate) VALUES (?,?,?,?)",
            (user_id, name, v_type, plate),
        )
        return cur.lastrowid


def delete_vehicle(vehicle_id, user_id):
    if _is_firebase_configured():
        v = _fb_request("GET", f"vehicles/{vehicle_id}")
        if isinstance(v, dict) and str(v.get("user_id")) == str(user_id):
            _fb_request("DELETE", f"vehicles/{vehicle_id}")
        return

    # Fallback to SQLite
    with get_sqlite_conn() as conn:
        conn.execute(
            "DELETE FROM vehicles WHERE id=? AND user_id=?",
            (vehicle_id, user_id),
        )


# ── Sessions ───────────────────────────────────────────────────────────────────

def start_session(user_id, vehicle_id, start_time):
    if _is_firebase_configured():
        session_id = int(time.time() * 1000)
        session_data = {
            "id": session_id,
            "user_id": user_id,
            "vehicle_id": vehicle_id,
            "start_time": start_time,
            "end_time": None,
            "total_frames": 0,
            "drowsy_frames": 0,
            "alert_frames": 0,
            "avg_confidence": 0.0,
            "avg_ear": 0.0
        }
        _fb_request("PUT", f"sessions/{session_id}", session_data)
        return session_id

    # Fallback to SQLite
    with get_sqlite_conn() as conn:
        cur = conn.execute(
            "INSERT INTO sessions (user_id, vehicle_id, start_time) VALUES (?,?,?)",
            (user_id, vehicle_id, start_time),
        )
        return cur.lastrowid


def end_session(session_id, end_time, total_frames, drowsy_frames,
                alert_frames, avg_confidence, avg_ear):
    if _is_firebase_configured():
        _fb_request("PATCH", f"sessions/{session_id}", {
            "end_time": end_time,
            "total_frames": total_frames,
            "drowsy_frames": drowsy_frames,
            "alert_frames": alert_frames,
            "avg_confidence": avg_confidence,
            "avg_ear": avg_ear
        })
        return

    # Fallback to SQLite
    with get_sqlite_conn() as conn:
        conn.execute(
            """UPDATE sessions
               SET end_time=?, total_frames=?, drowsy_frames=?,
                   alert_frames=?, avg_confidence=?, avg_ear=?
               WHERE id=?""",
            (end_time, total_frames, drowsy_frames,
             alert_frames, avg_confidence, avg_ear, session_id),
        )


def save_session_events(session_id, events):
    """events: list of dicts with keys timestamp, state, ear, mar, confidence"""
    if _is_firebase_configured():
        _fb_request("PUT", f"session_events/{session_id}", events)
        return

    # Fallback to SQLite
    with get_sqlite_conn() as conn:
        conn.executemany(
            """INSERT INTO session_events
               (session_id, timestamp, state, ear, mar, confidence)
               VALUES (?,?,?,?,?,?)""",
            [(session_id, e["timestamp"], e["state"],
              e.get("ear", 0.0), e.get("mar", 0.0), e.get("confidence", 0.0))
             for e in events],
        )


def get_sessions(user_id):
    if _is_firebase_configured():
        sessions_dict = _fb_request("GET", "sessions") or {}
        vehicles_dict = _fb_request("GET", "vehicles") or {}
        result = []
        if isinstance(sessions_dict, dict):
            for sid, s in sessions_dict.items():
                if isinstance(s, dict) and str(s.get("user_id")) == str(user_id):
                    # Join vehicle details
                    vid = s.get("vehicle_id")
                    veh = vehicles_dict.get(str(vid), {}) if vid and isinstance(vehicles_dict, dict) else {}
                    s_copy = dict(s)
                    s_copy["vehicle_name"] = veh.get("name") if isinstance(veh, dict) else None
                    s_copy["vehicle_type"] = veh.get("type") if isinstance(veh, dict) else None
                    result.append(s_copy)
        result.sort(key=lambda x: x.get("start_time", ""), reverse=True)
        return result

    # Fallback to SQLite
    with get_sqlite_conn() as conn:
        rows = conn.execute(
            """SELECT s.*, v.name as vehicle_name, v.type as vehicle_type
               FROM sessions s
               LEFT JOIN vehicles v ON s.vehicle_id = v.id
               WHERE s.user_id=?
               ORDER BY s.start_time DESC""",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_session_events(session_id, user_id):
    if _is_firebase_configured():
        s = _fb_request("GET", f"sessions/{session_id}")
        if not s or str(s.get("user_id")) != str(user_id):
            return []
        events = _fb_request("GET", f"session_events/{session_id}") or []
        if isinstance(events, list):
            return events
        elif isinstance(events, dict):
            return list(events.values())
        return []

    # Fallback to SQLite
    with get_sqlite_conn() as conn:
        rows = conn.execute(
            """SELECT se.* FROM session_events se
               JOIN sessions s ON se.session_id = s.id
               WHERE se.session_id=? AND s.user_id=?
               ORDER BY se.id ASC""",
            (session_id, user_id),
        ).fetchall()
        return [dict(r) for r in rows]

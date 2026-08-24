"""
run.py — Alternative root launcher for the Drowsiness Detection Web App
"""

import sys
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from backend.app import app

if __name__ == "__main__":
    print("=" * 60)
    print("  DrowsyGuard — AI Drowsiness Detection Web App")
    print("  Server running on http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)

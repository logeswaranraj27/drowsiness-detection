"""
app.py — Root entrypoint for Drowsiness Detection Web App

Allows running directly from root with:
    python app.py
"""

import sys
import os

# Add workspace root and backend to path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from backend.app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 60)
    print("  DrowsyGuard — AI Drowsiness Detection Web App")
    print(f"  Server running on http://localhost:{port}")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=port)

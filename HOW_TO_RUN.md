# 🛡️ DrowsyGuard — AI Drowsiness Detection System

## 📁 Project Architecture & Organization

The repository is organized into distinct, modular directories:

```
CAPSTONE/
├── frontend/                       # UI assets & views
│   ├── templates/
│   │   ├── auth.html               # Login & Registration Page
│   │   └── dashboard.html          # Main Dashboard & Live Monitoring UI
│   └── static/
│       ├── css/
│       │   └── style.css           # Modern Dark-mode Glassmorphism styling
│       └── js/
│           ├── auth.js             # Authentication client logic & i18n
│           └── dashboard.js        # Webcam capture, canvas streaming & telemetry
│
├── backend/                        # Application logic & models
│   ├── __init__.py
│   ├── app.py                      # Flask REST API & Web Server
│   ├── detector.py                 # MediaPipe FaceMesh + CNN Detector engine
│   ├── live_detection.py           # Standalone OpenCV Haar+CNN live camera system
│   ├── live_detection_v2.py        # Standalone MediaPipe EAR+MAR live camera system
│   ├── train_model.py              # CNN classifier training script (MobileNetV2)
│   ├── drowsiness_model.h5         # Trained model weights
│   └── class_names.json            # Class label mapping
│
├── database/                       # Data persistence layer
│   ├── __init__.py
│   ├── database.py                 # SQLite helper functions & schema
│   └── drowsiness_app.db           # SQLite database
│
├── others/                         # Training data & generated artifacts
│   ├── reports/
│   │   ├── evaluation_report.txt   # CNN model classification report & confusion matrix
│   │   ├── session_report.png      # Session EAR / confidence chart
│   │   ├── training_history.png    # Training loss & accuracy curves
│   │   └── event_log.json          # Timestamped detection event logs
│   ├── requirements_backup.txt
│   └── Drowsy_datset/              # Training & testing image dataset
│
├── app.py                          # Root launcher (runs backend server)
├── run.py                          # Alternative root runner
├── requirements.txt                # Python package dependencies
└── HOW_TO_RUN.md                   # This instruction guide
```

---

## 🚀 How to Run the Web Application

### Step 1: Activate Virtual Environment
Open PowerShell / Command Prompt in this folder and activate the environment:

```powershell
drowsiness_env\Scripts\activate
```

### Step 2: Start the Web App
Run either of the following commands from the root directory:

```bash
python app.py
```
*(or `python run.py` or `python backend/app.py`)*

### Step 3: Open in Browser
Open your browser and navigate to:
👉 **`http://localhost:5000`**

---

## ⚙️ Running Standalone Python Scripts

### 1. Standalone Live Detection (MediaPipe EAR + MAR)
To run the lightweight live camera detection window with visual + audio alarm:
```bash
python backend/live_detection_v2.py
```

### 2. Standalone Live Detection (Haar Cascade + CNN)
```bash
python backend/live_detection.py
```

### 3. Retrain the CNN Model
If you add new images to `others/Drowsy_datset/` and want to retrain:
```bash
python backend/train_model.py
```
This updates `backend/drowsiness_model.h5` and `backend/class_names.json`, and outputs new training curves in `others/reports/`.

---

## 🌟 Key Features
- 🌐 **9 Languages**: English, Tamil, Hindi, Malayalam, Telugu, Kannada, French, German, Spanish.
- 🔐 **Secure SQLite Authentication**: Password hashing using `werkzeug.security`.
- 📊 **Driver Analytics**: Track ride history, safe scores, drowsy frame frequency, and vehicle-specific stats.
- 🎥 **Browser Webcam Streaming**: Real-time EAR, MAR, and CNN confidence scoring directly from the browser.

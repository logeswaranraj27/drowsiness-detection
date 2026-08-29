"""
Drowsiness Detection - Model Training Script
==============================================
Trains a MobileNetV2-based CNN classifier on your Kaggle drowsiness dataset.

USAGE:
    1. Extract your Kaggle dataset zip somewhere on disk.
    2. Set DATASET_DIR below to the folder that CONTAINS the class subfolders
       (e.g. if you have  MyDataset/Drowsy/*.jpg  and  MyDataset/Alert/*.jpg,
       set DATASET_DIR = "MyDataset").
    3. Run:  python train_model.py
    4. Output: drowsiness_model.h5, class_names.json, training_history.png,
               evaluation_report.txt

The script auto-detects class folders and does NOT need you to know the
exact label names in advance - it just needs one folder per class, each
folder full of images for that class.
"""

import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ============================================================
# CONFIG - EDIT THESE
# ============================================================
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
REPORTS_DIR = os.path.join(ROOT_DIR, "others", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def _find_dataset():
    candidates = [
        os.path.join(ROOT_DIR, "others", "Drowsy_datset", "train"),
        os.path.join(ROOT_DIR, "others", "Drowsy_datset"),
        os.path.join(ROOT_DIR, "Drowsy_datset", "train"),
        os.path.join(ROOT_DIR, "Drowsy_datset"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

DATASET_DIR = os.path.join(ROOT_DIR, "Driver Drowsiness Dataset (DDD)")
IMG_SIZE = 145                   # input image size (square)
BATCH_SIZE = 32
EPOCHS = 20
VALIDATION_SPLIT = 0.2
MODEL_OUT = os.path.join(BACKEND_DIR, "drowsiness_model.h5")
CLASS_NAMES_OUT = os.path.join(BACKEND_DIR, "class_names.json")
REPORT_OUT = os.path.join(REPORTS_DIR, "evaluation_report.txt")
HISTORY_PLOT_OUT = os.path.join(REPORTS_DIR, "training_history.png")
# ============================================================

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp")


def find_class_root(base_dir):
    """
    Walks the directory tree to find the folder whose immediate
    subfolders each contain images directly - i.e. the true
    'root' that Keras's flow_from_directory needs.
    Handles cases where the zip extracted with an extra nested
    folder layer, or a train/ subfolder, etc.
    """
    if not os.path.isdir(base_dir):
        raise FileNotFoundError(
            f"DATASET_DIR '{base_dir}' does not exist. "
            f"Edit DATASET_DIR at the top of this script."
        )

    def has_images_directly(folder):
        try:
            return any(f.lower().endswith(IMAGE_EXTS) for f in os.listdir(folder))
        except (FileNotFoundError, NotADirectoryError):
            return False

    def subdirs(folder):
        return [
            os.path.join(folder, d)
            for d in os.listdir(folder)
            if os.path.isdir(os.path.join(folder, d))
        ]

    # BFS for the first folder whose subfolders all contain images directly
    queue = [base_dir]
    seen = set()
    while queue:
        current = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)

        children = subdirs(current)
        if len(children) >= 2 and all(has_images_directly(c) for c in children):
            return current, [os.path.basename(c) for c in children]

        queue.extend(children)

    raise RuntimeError(
        f"Could not auto-detect class folders under '{base_dir}'. "
        f"Please check the folder structure manually and set DATASET_DIR "
        f"to the folder that directly contains one subfolder per class."
    )


def build_model():
    base = MobileNetV2(input_shape=(IMG_SIZE, IMG_SIZE, 3), include_top=False, weights="imagenet")
    base.trainable = False  # transfer learning - freeze base initially

    x = base.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(128, activation="relu")(x)
    x = Dropout(0.3)(x)
    output = Dense(1, activation="sigmoid")(x)

    model = Model(inputs=base.input, outputs=output)
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    return model


def main():
    print("=" * 70)
    print("DROWSINESS DETECTION - MODEL TRAINING")
    print("=" * 70)

    class_root, class_folders = find_class_root(DATASET_DIR)
    print(f"\nFound dataset root: {class_root}")
    print(f"Detected classes: {class_folders}")

    datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        validation_split=VALIDATION_SPLIT,
        horizontal_flip=True,
        brightness_range=(0.8, 1.2),
        zoom_range=0.1,
    )

    train_gen = datagen.flow_from_directory(
        class_root,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode="binary",
        subset="training",
        shuffle=True,
    )
    val_gen = datagen.flow_from_directory(
        class_root,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode="binary",
        subset="validation",
        shuffle=False,
    )

    # class_indices maps folder_name -> 0/1 ; save it so live_detection.py
    # knows which index means "drowsy"
    class_indices = train_gen.class_indices  # e.g. {'Alert': 0, 'Drowsy': 1}
    print(f"\nClass index mapping: {class_indices}")
    with open(CLASS_NAMES_OUT, "w") as f:
        json.dump(class_indices, f, indent=2)

    model = build_model()
    model.summary()

    callbacks = [
        EarlyStopping(monitor="val_loss", patience=4, restore_best_weights=True),
        ModelCheckpoint(MODEL_OUT, monitor="val_accuracy", save_best_only=True, verbose=1),
    ]

    print("\nStarting training...\n")
    history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS,
        callbacks=callbacks,
    )

    # ---- Plots ----
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(history.history["accuracy"], label="train")
    axes[0].plot(history.history["val_accuracy"], label="val")
    axes[0].set_title("Accuracy")
    axes[0].legend()
    axes[1].plot(history.history["loss"], label="train")
    axes[1].plot(history.history["val_loss"], label="val")
    axes[1].set_title("Loss")
    axes[1].legend()
    plt.tight_layout()
    plt.savefig(HISTORY_PLOT_OUT)
    print(f"\nSaved training curves to {HISTORY_PLOT_OUT}")

    # ---- Evaluation report ----
    val_gen.reset()
    y_true = val_gen.classes
    y_prob = model.predict(val_gen).ravel()
    y_pred = (y_prob >= 0.5).astype(int)

    report = classification_report(y_true, y_pred, target_names=list(class_indices.keys()))
    cm = confusion_matrix(y_true, y_pred)

    print("\n" + "=" * 70)
    print("EVALUATION REPORT")
    print("=" * 70)
    print(report)
    print("Confusion Matrix:")
    print(cm)

    with open(REPORT_OUT, "w") as f:
        f.write(report)
        f.write("\n\nConfusion Matrix:\n")
        f.write(str(cm))
    print(f"Saved evaluation report to {REPORT_OUT}")

    print(f"\nModel saved to: {MODEL_OUT}")
    print(f"Class mapping saved to: {CLASS_NAMES_OUT}")
    print("Done!")


if __name__ == "__main__":
    main()

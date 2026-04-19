"""Proje genelinde kullanilacak sabitler."""

import sys
from pathlib import Path


def _resolve_project_root() -> Path:
    if getattr(sys, "frozen", False):
        bundle_root = getattr(sys, "_MEIPASS", None)
        if bundle_root:
            return Path(bundle_root)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = _resolve_project_root()
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

FER2013_DIR = RAW_DATA_DIR / "fer2013"
TRAIN_DIR = FER2013_DIR / "train"
TEST_DIR = FER2013_DIR / "test"

IMAGE_SIZE = (96, 96)
BATCH_SIZE = 32
COLOR_MODE = "rgb"
SEED = 42
INPUT_SHAPE = (96, 96, 3)
NUM_CLASSES = 7
VALIDATION_SPLIT = 0.1
EPOCHS = 15
LEARNING_RATE = 3e-4
TRAINING_OVERSAMPLE_FACTOR = 2
FINE_TUNE_AT = 100
FINE_TUNE_LEARNING_RATE = 1e-5

MODEL_PATH = ARTIFACTS_DIR / "emotion_cnn.keras"
HISTORY_PATH = ARTIFACTS_DIR / "training_history.csv"
CONFUSION_MATRIX_IMAGE_PATH = ARTIFACTS_DIR / "confusion_matrix.png"
CONFUSION_MATRIX_CSV_PATH = ARTIFACTS_DIR / "confusion_matrix.csv"
CLASSIFICATION_REPORT_PATH = ARTIFACTS_DIR / "classification_report.txt"

EMOTION_LABELS = [
    "angry",
    "disgust",
    "fear",
    "happy",
    "sad",
    "surprise",
    "neutral",
]

HOME_MODE_MAP = {
    "angry": "rahatlatici mod",
    "disgust": "standart mod",
    "fear": "rahatlatici mod",
    "happy": "enerjik mod",
    "sad": "rahatlatici mod",
    "surprise": "standart mod",
    "neutral": "odak modu",
}

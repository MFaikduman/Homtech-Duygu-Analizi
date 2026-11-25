"""Shared paths and class order for HOMTECH EmotionAI."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DOWNLOADS_DIR = DATA_DIR / "downloads"
RAW_DATA_DIR = DATA_DIR / "raw"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
CAPTURE_MODEL_DIR = ARTIFACTS_DIR / "runs" / "camera-rbf-001"
ALIGNED_MODEL_DIR = ARTIFACTS_DIR / "runs" / "seven-class-rbf-001"

# Model checkpoints and reports must use this exact order.
EMOTION_LABELS = [
    "angry", "disgust", "fear", "happy", "sad", "surprise", "neutral",
]

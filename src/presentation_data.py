"""Sunum modülü için proje özeti ve metrikleri derler."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from src.config import EMOTION_LABELS, HISTORY_PATH, IMAGE_SIZE, PROJECT_ROOT, TEST_DIR, TRAIN_DIR


IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")
CLASSIFICATION_REPORT_PATH = PROJECT_ROOT / "artifacts" / "classification_report.txt"
CONFUSION_MATRIX_CSV_PATH = PROJECT_ROOT / "artifacts" / "confusion_matrix.csv"
CONFUSION_MATRIX_IMAGE_PATH = PROJECT_ROOT / "artifacts" / "confusion_matrix.png"
README_PATH = PROJECT_ROOT / "README.md"
FER2013_TRAIN_FALLBACK = {
    "angry": 3995,
    "disgust": 436,
    "fear": 4097,
    "happy": 7215,
    "sad": 4830,
    "surprise": 3171,
    "neutral": 4965,
}
FER2013_TEST_FALLBACK = {
    "angry": 958,
    "disgust": 111,
    "fear": 1024,
    "happy": 1774,
    "sad": 1247,
    "surprise": 831,
    "neutral": 1233,
}


def _count_split(directory: Path) -> dict:
    counts = {}

    for label in EMOTION_LABELS:
        class_dir = directory / label
        count = 0

        if class_dir.exists():
            for extension in IMAGE_EXTENSIONS:
                count += len(list(class_dir.glob(f"*{extension}")))

        counts[label] = count

    return counts


def _parse_classification_report() -> dict:
    if not CLASSIFICATION_REPORT_PATH.exists():
        return {
            "overall": {},
            "per_class": [],
        }

    text = CLASSIFICATION_REPORT_PATH.read_text(encoding="utf-8")
    per_class = []
    accuracy = None
    macro_avg = None
    weighted_avg = None
    total_support = None

    class_pattern = re.compile(
        r"^\s*(angry|disgust|fear|happy|sad|surprise|neutral)\s+"
        r"([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+(\d+)\s*$",
        re.MULTILINE,
    )

    for match in class_pattern.finditer(text):
        label, precision, recall, f1_score, support = match.groups()
        per_class.append(
            {
                "label": label,
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1_score),
                "support": int(support),
            }
        )

    accuracy_match = re.search(r"^\s*accuracy\s+([0-9.]+)\s+(\d+)\s*$", text, re.MULTILINE)
    if accuracy_match:
        accuracy = float(accuracy_match.group(1))
        total_support = int(accuracy_match.group(2))

    macro_match = re.search(
        r"^\s*macro avg\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+(\d+)\s*$",
        text,
        re.MULTILINE,
    )
    if macro_match:
        macro_avg = {
            "precision": float(macro_match.group(1)),
            "recall": float(macro_match.group(2)),
            "f1_score": float(macro_match.group(3)),
            "support": int(macro_match.group(4)),
        }

    weighted_match = re.search(
        r"^\s*weighted avg\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+(\d+)\s*$",
        text,
        re.MULTILINE,
    )
    if weighted_match:
        weighted_avg = {
            "precision": float(weighted_match.group(1)),
            "recall": float(weighted_match.group(2)),
            "f1_score": float(weighted_match.group(3)),
            "support": int(weighted_match.group(4)),
        }

    strongest_class = max(per_class, key=lambda item: item["f1_score"], default=None)
    weakest_class = min(per_class, key=lambda item: item["f1_score"], default=None)

    return {
        "overall": {
            "accuracy": accuracy,
            "macro_avg": macro_avg,
            "weighted_avg": weighted_avg,
            "support": total_support,
        },
        "per_class": per_class,
        "strongest_class": strongest_class,
        "weakest_class": weakest_class,
    }


def _parse_training_history() -> dict:
    if not HISTORY_PATH.exists():
        return {}

    with open(HISTORY_PATH, "r", encoding="utf-8", newline="") as history_file:
        rows = list(csv.DictReader(history_file))

    if not rows:
        return {}

    normalized_rows = []
    for index, row in enumerate(rows, start=1):
        normalized_rows.append(
            {
                "epoch": index,
                "accuracy": float(row["accuracy"]),
                "loss": float(row["loss"]),
                "val_accuracy": float(row["val_accuracy"]),
                "val_loss": float(row["val_loss"]),
                "learning_rate": float(row["learning_rate"]),
            }
        )

    best_val_epoch = max(normalized_rows, key=lambda item: item["val_accuracy"])
    final_epoch = normalized_rows[-1]

    return {
        "epochs": len(normalized_rows),
        "best_epoch": best_val_epoch["epoch"],
        "best_val_accuracy": best_val_epoch["val_accuracy"],
        "final_accuracy": final_epoch["accuracy"],
        "final_val_accuracy": final_epoch["val_accuracy"],
        "history": normalized_rows,
    }


def _parse_reported_best_metrics() -> dict:
    if not README_PATH.exists():
        return {}

    readme_text = README_PATH.read_text(encoding="utf-8")

    metrics = {}
    patterns = {
        "accuracy": r"- `accuracy`: `([0-9.]+)`",
        "precision": r"- `precision`: `([0-9.]+)`",
        "recall": r"- `recall`: `([0-9.]+)`",
        "weighted_f1_score": r"- `weighted f1-score`: `([0-9.]+)`",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, readme_text)
        if match:
            metrics[key] = float(match.group(1))

    return metrics


def _parse_confusion_matrix() -> dict:
    if not CONFUSION_MATRIX_CSV_PATH.exists():
        return {
            "labels": EMOTION_LABELS,
            "rows": [],
            "image_path": None,
        }

    with open(CONFUSION_MATRIX_CSV_PATH, "r", encoding="utf-8", newline="") as matrix_file:
        rows = list(csv.reader(matrix_file))

    labels = rows[0][1:] if rows else EMOTION_LABELS
    matrix_rows = []
    for row in rows[1:]:
        matrix_rows.append(
            {
                "label": row[0],
                "values": [int(value) for value in row[1:]],
            }
        )

    image_path = "/artifacts/confusion_matrix.png" if CONFUSION_MATRIX_IMAGE_PATH.exists() else None
    return {
        "labels": labels,
        "rows": matrix_rows,
        "image_path": image_path,
    }


def _load_dataset_counts() -> tuple[dict, dict]:
    train_counts = _count_split(TRAIN_DIR)
    test_counts = _count_split(TEST_DIR)

    if sum(train_counts.values()) == 0 and sum(test_counts.values()) == 0:
        return FER2013_TRAIN_FALLBACK.copy(), FER2013_TEST_FALLBACK.copy()

    return train_counts, test_counts


def build_presentation_payload() -> dict:
    train_counts, test_counts = _load_dataset_counts()
    report = _parse_classification_report()
    training = _parse_training_history()
    reported_best_metrics = _parse_reported_best_metrics()

    total_train = sum(train_counts.values())
    total_test = sum(test_counts.values())
    class_totals = {
        label: train_counts[label] + test_counts[label]
        for label in EMOTION_LABELS
    }
    dominant_class = max(class_totals, key=class_totals.get, default=None)
    rarest_class = min(class_totals, key=class_totals.get, default=None)

    return {
        "project": {
            "title": "HOMTECH Duygu Analizi ve Akıllı Ev Senaryo Sistemi",
            "subtitle": "Duygu tanımayı akıllı ev otomasyonuna bağlayan sunum modülü",
            "goal": (
                "Yüz ifadesinden duyguyu tahmin edip bunu ışık, sıcaklık, müzik, perde "
                "ve bildirim gibi ev aksiyonlarına çevirmek."
            ),
            "image_size": {"width": IMAGE_SIZE[0], "height": IMAGE_SIZE[1]},
            "emotion_labels": EMOTION_LABELS,
        },
        "dataset": {
            "name": "FER-2013",
            "source": "Kaggle / msambare/fer2013",
            "train_total": total_train,
            "test_total": total_test,
            "total_images": total_train + total_test,
            "train_counts": train_counts,
            "test_counts": test_counts,
            "class_totals": class_totals,
            "dominant_class": dominant_class,
            "rarest_class": rarest_class,
        },
        "evaluation": {
            "current_report": report,
            "reported_best_metrics": reported_best_metrics,
            "training": training,
            "confusion_matrix": _parse_confusion_matrix(),
        },
        "story": {
            "pipeline": [
                "FER-2013 veri setinden 7 sınıflı duygu verisi okunur.",
                "Görseller FER stiline yaklaştırılıp 96x96 RGB formata çekilir.",
                "MobileNetV2 tabanlı model transfer learning ile eğitilir.",
                "Tek görsel tahmininden sonra TTA ile skorlar dengelenir.",
                "Sonuç, HOMTECH akıllı ev planına çevrilerek sahne önerisi üretir.",
            ],
            "tech_stack": [
                "Python",
                "TensorFlow / Keras",
                "OpenCV",
                "NumPy",
                "Pandas",
                "scikit-learn",
                "Matplotlib / Seaborn",
                "HTML / CSS / JavaScript",
            ],
        },
    }

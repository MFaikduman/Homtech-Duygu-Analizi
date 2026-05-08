"""Sunum modulu icin proje ozeti ve metrikleri derler."""

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
LITERATURE_BENCHMARKS = [
    {
        "label": "Bu proje",
        "short_label": "Bizim model",
        "accuracy": 53.48,
        "year": 2026,
        "note": "HOMTECH sunumu icin temel CNN/MobileNetV2 prototipi",
    },
    {
        "label": "Pramerdorfer ve Kampel",
        "short_label": "P&K 2016",
        "accuracy": 75.20,
        "year": 2016,
        "note": "FER2013 uzerinde ensemble CNN yaklasimi",
    },
    {
        "label": "Georgescu ve ark.",
        "short_label": "Geo 2018",
        "accuracy": 75.42,
        "year": 2018,
        "note": "Local learning tabanli FER2013 sonucu",
    },
    {
        "label": "Khaireddin ve Chen",
        "short_label": "K&C 2021",
        "accuracy": 73.28,
        "year": 2021,
        "note": "DERL cikarimlariyla bildirilen FER2013 performansi",
    },
    {
        "label": "Improved MobileNetV2",
        "short_label": "IMV2 2024",
        "accuracy": 68.62,
        "year": 2024,
        "note": "Hafif mimariyi iyilestiren guncel calisma",
    },
]


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


def _build_literature_payload(report: dict) -> dict:
    current_accuracy = report.get("overall", {}).get("accuracy")
    current_accuracy_percent = round((current_accuracy or 0) * 100, 2)

    benchmarks = []
    for item in LITERATURE_BENCHMARKS:
        benchmarks.append(
            {
                **item,
                "delta_vs_current": round(item["accuracy"] - current_accuracy_percent, 2),
            }
        )

    external_benchmarks = [item for item in benchmarks if item["label"] != "Bu proje"]
    best_reference = max(external_benchmarks, key=lambda item: item["accuracy"], default=None)
    average_reference = round(
        sum(item["accuracy"] for item in external_benchmarks) / len(external_benchmarks),
        2,
    ) if external_benchmarks else None

    summary = (
        f"Bu prototip {current_accuracy_percent:.2f}% dogruluk uretirken, secili literatur ornekleri "
        f"ortalama {average_reference:.2f}% seviyesine cikiyor. En yuksek referans "
        f"{best_reference['label']} ile {best_reference['accuracy']:.2f}% olarak goruluyor."
        if best_reference and average_reference is not None
        else "Literatur karsilastirmasi icin referans sonuclar hazirlanamadi."
    )

    return {
        "current_accuracy": current_accuracy_percent,
        "summary": summary,
        "benchmarks": benchmarks,
        "best_reference": best_reference,
        "average_reference": average_reference,
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
            "title": "HOMTECH Duygu Analizi ve Akilli Ev Senaryo Sistemi",
            "subtitle": "Duygu tanimayi akilli ev otomasyonuna baglayan sunum modul",
            "goal": (
                "Yuz ifadesinden duyguyu tahmin edip bunu isik, sicaklik, muzik, perde "
                "ve bildirim gibi ev aksiyonlarina cevirmek."
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
        "literature": _build_literature_payload(report),
        "story": {
            "pipeline": [
                "FER-2013 veri setinden 7 sinifli duygu verisi okunur.",
                "Gorseller FER stiline yaklastirilip 96x96 RGB formata cekilir.",
                "MobileNetV2 tabanli model transfer learning ile egitilir.",
                "Tek gorsel tahmininden sonra TTA ile skorlar dengelenir.",
                "Sonuc, HOMTECH akilli ev planina cevrilerek sahne onerisi uretir.",
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

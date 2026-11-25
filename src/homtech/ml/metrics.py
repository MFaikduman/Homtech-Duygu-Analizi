"""Metrics with explicit class order shared by validation and final evaluation."""

import csv
import json
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from homtech.ml.rafdb import CLASSES


def classification_metrics(y_true, y_pred, *, classes=CLASSES) -> dict:
    indices = [CLASSES.index(label) for label in classes]
    if len(y_true) == 0 or len(y_true) != len(y_pred):
        raise ValueError("Gerçek/tahmin etiketleri boş olmamalı ve aynı uzunlukta olmalı.")
    return {"samples": len(y_true),
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "macro_f1": float(f1_score(y_true, y_pred, labels=indices,
                                       average="macro", zero_division=0)),
            "classes": list(classes),
            "classification_report": classification_report(
                y_true, y_pred, labels=indices, target_names=list(classes),
                output_dict=True, zero_division=0),
            "confusion_matrix": confusion_matrix(y_true, y_pred, labels=indices).tolist()}


def save_reports(metrics: dict, output_dir: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_dir.mkdir(parents=True, exist_ok=True)
    classes = metrics["classes"]
    indices = range(len(classes))
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    with (output_dir / "confusion_matrix.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["actual/predicted", *classes])
        writer.writerows([label, *row] for label, row in zip(classes, metrics["confusion_matrix"]))
    figure, axis = plt.subplots(figsize=(9, 7))
    axis.imshow(metrics["confusion_matrix"], cmap="Blues")
    axis.set(xticks=indices, yticks=indices, xticklabels=classes, yticklabels=classes,
             xlabel="Predicted expression", ylabel="Actual expression",
             title=f"RAF-DB — {len(classes)}-class evaluation")
    for row in indices:
        for column in indices:
            axis.text(column, row, metrics["confusion_matrix"][row][column], ha="center", va="center")
    figure.tight_layout()
    figure.savefig(output_dir / "confusion_matrix.png", dpi=160)
    plt.close(figure)

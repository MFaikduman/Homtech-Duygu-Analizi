"""Model degerlendirme icin giris noktasi."""

import csv

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support
from tensorflow import keras

from src.config import (
    ARTIFACTS_DIR,
    CLASSIFICATION_REPORT_PATH,
    CONFUSION_MATRIX_CSV_PATH,
    CONFUSION_MATRIX_IMAGE_PATH,
    EMOTION_LABELS,
    MODEL_PATH,
)
from src.data.data_loader import load_datasets


def collect_predictions(model, dataset):
    y_true = []
    y_pred = []

    for images, labels in dataset:
        predictions = model.predict(images, verbose=0)
        y_true.extend(np.argmax(labels.numpy(), axis=1))
        y_pred.extend(np.argmax(predictions, axis=1))

    return np.array(y_true), np.array(y_pred)


def save_confusion_matrix(matrix):
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(CONFUSION_MATRIX_CSV_PATH, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([""] + EMOTION_LABELS)
        for label, row in zip(EMOTION_LABELS, matrix):
            writer.writerow([label] + list(row))

    plt.figure(figsize=(8, 6))
    sns.heatmap(
        matrix,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=EMOTION_LABELS,
        yticklabels=EMOTION_LABELS,
    )
    plt.xlabel("Tahmin")
    plt.ylabel("Gercek")
    plt.title("Confusion Matrix")
    plt.tight_layout()
    plt.savefig(CONFUSION_MATRIX_IMAGE_PATH, dpi=300)
    plt.close()


def save_classification_report(report_text):
    with open(CLASSIFICATION_REPORT_PATH, "w", encoding="utf-8") as report_file:
        report_file.write(report_text)


def main() -> None:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Egitilmis model bulunamadi: {MODEL_PATH}. Once python -m src.train calistir."
        )

    print("Model degerlendirme basladi.")

    _, _, test_dataset, _ = load_datasets()
    model = keras.models.load_model(MODEL_PATH)

    y_true, y_pred = collect_predictions(model, test_dataset)

    accuracy = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0,
    )
    matrix = confusion_matrix(y_true, y_pred)
    report_text = classification_report(
        y_true,
        y_pred,
        target_names=EMOTION_LABELS,
        zero_division=0,
    )

    save_confusion_matrix(matrix)
    save_classification_report(report_text)

    print(f"Accuracy: {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1-score: {f1:.4f}")
    print("\nClassification Report:")
    print(report_text)
    print(f"Confusion matrix gorseli kaydedildi: {CONFUSION_MATRIX_IMAGE_PATH}")
    print(f"Confusion matrix CSV kaydedildi: {CONFUSION_MATRIX_CSV_PATH}")
    print(f"Classification report kaydedildi: {CLASSIFICATION_REPORT_PATH}")


if __name__ == "__main__":
    main()

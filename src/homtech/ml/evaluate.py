"""Evaluate a selected HOG/SVM model on its classes in the official test split."""

import argparse
import hashlib
from pathlib import Path

import numpy as np

from homtech.console import configure_utf8_console
from homtech.ml.capture_data import DEFAULT_ORIGINAL_ARCHIVE, extract_capture_features
from homtech.ml.features import extract_features
from homtech.ml.metrics import classification_metrics, save_reports
from homtech.ml.model import load_model, predict_with_margin
from homtech.ml.rafdb import CLASSES, DEFAULT_ROOT, describe_samples, read_samples
from homtech.ml.train import DEFAULT_OUTPUT


def evaluate(model_path: Path, data_dir: Path, output_dir: Path, *, original_archive: Path | None = None):
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Rapor klasörü boş olmalı; yeni --output-dir seçin.")
    payload = load_model(model_path)
    classes = payload["classes"]
    labels = {CLASSES.index(label) for label in classes}
    official_test = [item for item in read_samples(data_dir) if item.split == "test"]
    samples = [item for item in official_test if item.label in labels]
    if {item.label for item in samples} != labels:
        raise ValueError("Test kümesi modelin tüm sınıflarını içermeli.")
    description = describe_samples(samples, content_hash=True)
    if description != payload["dataset"]["test"]:
        raise ValueError("Test verisi eğitim manifestiyle eşleşmiyor.")
    input_metrics = {}
    if capture_data := payload.get("capture_data"):
        archive = original_archive or Path(payload["configuration"].get("original_archive", DEFAULT_ORIGINAL_ARCHIVE))
        with archive.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != capture_data["archive_sha256"]:
            raise ValueError("Orijinal fotoğraf arşivi eğitim manifestiyle eşleşmiyor.")
        matrix, samples = extract_capture_features(samples, archive, payload["feature_config"], progress=True)
        predictions, margins = predict_with_margin(payload["estimator"], matrix)
        actual = np.array([item.label for item in samples])
        accepted = margins >= payload["suggestion_policy"]["minimum_margin"]
        correct = predictions == actual
        suggested = accepted & (predictions != CLASSES.index("disgust"))
        input_metrics.update(
            input_kind="original_rafdb_after_face_detection",
            rejected_by_face_detector=description["total"] - len(samples),
            uncertain=int((~accepted).sum()),
            accepted_predictions=int(accepted.sum()),
            correct_accepted_predictions=int((accepted & correct).sum()),
            accepted_accuracy=float(correct[accepted].mean()) if accepted.any() else None,
            suggestions=int(suggested.sum()),
            correct_suggestions=int((suggested & correct).sum()),
        )
    else:
        matrix = extract_features(samples, progress=True, config=payload["feature_config"])
        predictions = payload["estimator"].predict(matrix)
    metrics = classification_metrics([item.label for item in samples], predictions, classes=classes)
    with model_path.open("rb") as stream:
        model_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    excluded = [label for label in CLASSES if label not in classes]
    metrics.update(dataset="RAF-DB BasicEmo",
                   split="official_test_subset" if excluded else "official_test",
                   official_test_samples=len(official_test), excluded_classes=excluded,
                   algorithm=payload["algorithm"], best_c=payload["best_c"],
                   model_sha256=model_hash, test_fingerprint=description)
    metrics.update(input_metrics)
    save_reports(metrics, output_dir)
    return metrics


def main(argv=None):
    configure_utf8_console()
    parser = argparse.ArgumentParser(description="HOG + SVM için RAF-DB test raporu.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--model", type=Path, default=DEFAULT_OUTPUT / "best.joblib")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--original-archive", type=Path, help="Camera-rbf için RAF-DB original.zip yolu")
    args = parser.parse_args(argv)
    try:
        output = args.output_dir or args.model.parent / "evaluation"
        metrics = evaluate(args.model, args.data_dir, output, original_archive=args.original_archive)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Hata: {exc}\n")
    print(f"Test: {metrics['samples']} görsel; accuracy={metrics['accuracy']:.4f}; macro F1={metrics['macro_f1']:.4f}")
    if "accepted_predictions" in metrics:
        print(f"Eşiği geçen tahminler: {metrics['correct_accepted_predictions']}/{metrics['accepted_predictions']} doğru; "
              f"yüz bulma aşamasında elenen: {metrics['rejected_by_face_detector']}")
    print(f"Raporlar: {output}")


if __name__ == "__main__":
    main()

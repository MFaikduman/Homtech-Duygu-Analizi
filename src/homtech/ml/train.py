"""Train classical HOG + SVM models and select C using validation macro F1."""

import argparse
import csv
import hashlib
import json
import math
import platform
import subprocess
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sklearn
from sklearn.exceptions import ConvergenceWarning

from homtech.console import configure_utf8_console
from homtech.ml.capture_data import DEFAULT_ORIGINAL_ARCHIVE, extract_capture_features
from homtech.ml.features import FEATURE_CONFIG, extract_features
from homtech.ml.metrics import classification_metrics
from homtech.ml.model import (
    LINEAR_ALGORITHM, LINEAR_SCHEMA_VERSION, RBF_ALGORITHM, RBF_FEATURE_CONFIG,
    RBF_SCHEMA_VERSION, build_estimator, predict_with_margin, save_model,
)
from homtech.ml.rafdb import CLASSES, DEFAULT_ROOT, SIX_CLASSES, describe_samples, read_samples, split_samples
from homtech.settings import ALIGNED_MODEL_DIR, ARTIFACTS_DIR, CAPTURE_MODEL_DIR, PROJECT_ROOT


DEFAULT_OUTPUT = ARTIFACTS_DIR / "runs" / "six-class-rbf-001"
LINEAR_OUTPUT = ARTIFACTS_DIR / "runs" / "hog-svm-001"


def write_json(path, payload):
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def build_parser():
    parser = argparse.ArgumentParser(description="RAF-DB için klasik makine öğrenmesi: HOG + SVM.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--profile", choices=("six-rbf", "seven-rbf", "camera-rbf", "seven-linear"),
                        default="six-rbf", help="Masaüstü fotoğraf ve kamera modeli için camera-rbf")
    parser.add_argument("--original-archive", type=Path, default=DEFAULT_ORIGINAL_ARCHIVE,
                        help="camera-rbf için RAF-DB original.zip yolu")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--c-values", type=float, nargs="+",
                        help="Doğrulama kümesinde karşılaştırılacak SVM C değerleri")
    parser.add_argument("--pca-components", type=int, default=128,
                        help="RBF SVM öncesindeki PCA bileşen sayısı")
    parser.add_argument("--validation-split", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-iter", type=int, default=10000)
    return parser


def suggestion_policy(estimator, validation_x, validation_y, *, input_kind):
    predictions, margins = predict_with_margin(estimator, validation_x)
    disgust = CLASSES.index("disgust")
    supported = validation_y != disgust
    candidate = predictions != disgust
    target_coverage = 0.70
    target_count = math.ceil(int(supported.sum()) * target_coverage)
    scores = np.sort(margins[supported & candidate])
    minimum = scores[max(0, len(scores) - target_count)] if len(scores) else margins.max() + 1
    return {"minimum_margin": float(minimum), "target_validation_coverage": target_coverage,
            "calibration_input": input_kind}


def train(args):
    linear = args.profile == "seven-linear"
    camera = args.profile == "camera-rbf"
    capture = camera or args.profile == "seven-rbf"
    if linear:
        model, algorithm, schema_version = "linear", LINEAR_ALGORITHM, LINEAR_SCHEMA_VERSION
        classes, feature_config = CLASSES, FEATURE_CONFIG
        default_output, default_c_values = LINEAR_OUTPUT, [0.01, 0.1, 1.0]
    else:
        model, algorithm, schema_version = "rbf", RBF_ALGORITHM, RBF_SCHEMA_VERSION
        classes = CLASSES if capture else SIX_CLASSES
        feature_config = RBF_FEATURE_CONFIG
        default_output, default_c_values = (ALIGNED_MODEL_DIR if capture else DEFAULT_OUTPUT), [1.0]
        if camera:
            default_output = CAPTURE_MODEL_DIR
    output_dir = args.output_dir or default_output
    c_values = default_c_values if args.c_values is None else args.c_values
    if not c_values or any(not math.isfinite(c) or c <= 0 for c in c_values):
        raise ValueError("C değerleri sonlu ve pozitif olmalı.")
    if args.max_iter < 1 or not 0 <= args.seed < 2**32:
        raise ValueError("max-iter pozitif, seed 0 ile 2**32-1 arasında olmalı.")
    if not linear and args.pca_components < 2:
        raise ValueError("PCA bileşen sayısı en az 2 olmalı.")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Çıktı klasörü boş olmalı; yeni --output-dir seçin.")
    samples = read_samples(args.data_dir)
    splits = split_samples(samples, args.validation_split, args.seed)
    labels = {CLASSES.index(label) for label in classes}
    splits = {name: [item for item in items if item.label in labels] for name, items in splits.items()}
    print("Veri içerik fingerprint'leri hesaplanıyor...", flush=True)
    descriptions = {name: describe_samples(items, content_hash=True) for name, items in splits.items()}
    config = {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()}
    config.update(output_dir=str(output_dir), c_values=c_values)
    capture_data = {}
    if camera:
        with args.original_archive.open("rb") as stream:
            capture_data["archive_sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT,
                                         text=True, stderr=subprocess.DEVNULL).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=PROJECT_ROOT,
                                             text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        commit, dirty = None, None
    manifest = {"schema_version": schema_version, "algorithm": algorithm,
                "created_at_utc": datetime.now(timezone.utc).isoformat(), "status": "running",
                "git": {"commit": commit, "dirty": dirty},
                "runtime": {"python": sys.version.split()[0], "platform": platform.platform(),
                            "scikit_learn": sklearn.__version__, "numpy": np.__version__},
                "configuration": config, "feature_config": feature_config, "classes": list(classes),
                "dataset": descriptions,
                "split_membership": {name: [item.name for item in items] for name, items in splits.items()},
                "selection_metric": "validation_macro_f1", "trials": []}
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "run_manifest.json"
    write_json(manifest_path, manifest)
    try:
        train_samples, validation_samples = splits["train"], splits["validation"]
        print("Eğitim kümesinden HOG özellikleri çıkarılıyor...", flush=True)
        if camera:
            train_x, train_samples = extract_capture_features(
                train_samples, args.original_archive, feature_config, progress=True)
            print("Doğrulama kümesinden HOG özellikleri çıkarılıyor...", flush=True)
            validation_x, validation_samples = extract_capture_features(
                validation_samples, args.original_archive, feature_config, progress=True)
            capture_data.update(train=describe_samples(train_samples), validation=describe_samples(validation_samples))
            manifest["capture_data"] = capture_data
        else:
            train_x = extract_features(train_samples, progress=True, config=feature_config)
            print("Doğrulama kümesinden HOG özellikleri çıkarılıyor...", flush=True)
            validation_x = extract_features(validation_samples, progress=True, config=feature_config)
        train_y = np.array([item.label for item in train_samples])
        validation_y = np.array([item.label for item in validation_samples])
        if set(train_y) != labels:
            raise ValueError("Eğitim görüntülerinde modelin tüm yüz ifadesi sınıfları bulunmalı.")
        best_score, best_c = -1.0, None
        for c in dict.fromkeys(c_values):
            print(f"SVM eğitiliyor: C={c:g}", flush=True)
            started = time.monotonic()
            estimator = build_estimator(model, c, args.pca_components, args.seed, args.max_iter)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ConvergenceWarning)
                # Fit every pipeline step on the training split.
                estimator.fit(train_x, train_y)
            converged = not any(issubclass(item.category, ConvergenceWarning) for item in caught)
            metrics = classification_metrics(validation_y, estimator.predict(validation_x), classes=classes)
            trial = {"c": c, "validation_accuracy": metrics["accuracy"],
                     "validation_macro_f1": metrics["macro_f1"], "converged": converged,
                     "elapsed_seconds": time.monotonic() - started}
            manifest["trials"].append(trial)
            if metrics["macro_f1"] > best_score:
                best_score, best_c = metrics["macro_f1"], c
                manifest["best_validation_metrics"] = metrics
                payload = {
                    "schema_version": schema_version, "algorithm": algorithm,
                    "classes": list(classes), "feature_config": feature_config,
                    "estimator": estimator, "best_c": c, "validation_macro_f1": best_score,
                    "configuration": config, "dataset": descriptions,
                    "scikit_learn_version": sklearn.__version__,
                }
                if capture:
                    policy = suggestion_policy(
                        estimator, validation_x, validation_y,
                        input_kind="original_rafdb_validation_after_detection" if camera else "aligned_rafdb_validation")
                    payload["suggestion_policy"] = policy
                    manifest["suggestion_policy"] = policy
                if camera:
                    payload["capture_data"] = capture_data
                save_model(output_dir / "best.joblib", payload)
            manifest.update(best_c=best_c, best_validation_macro_f1=best_score)
            write_json(manifest_path, manifest)
            with (output_dir / "validation_results.csv").open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(trial))
                writer.writeheader()
                writer.writerows(manifest["trials"])
            print(f"C={c:g}: val_acc={metrics['accuracy']:.4f}, "
                  f"val_macro_f1={metrics['macro_f1']:.4f}, converged={converged}", flush=True)
            if not converged:
                print("Uyarı: SVM yakınsamadı; max-iter değerini artırarak yeni bir koşu deneyin.", flush=True)
        manifest["status"] = "completed"
        write_json(manifest_path, manifest)
        return manifest
    except BaseException as exc:
        manifest.update(status="interrupted" if isinstance(exc, KeyboardInterrupt) else "failed", error=str(exc))
        write_json(manifest_path, manifest)
        raise


def main(argv=None):
    configure_utf8_console()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        manifest = train(args)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Hata: {exc}\n")
    model_path = Path(manifest["configuration"]["output_dir"]) / "best.joblib"
    print(f"En iyi C: {manifest['best_c']}; model: {model_path}")
    print("Test kümesi değerlendirilmedi. Sonuç için homtech-evaluate çalıştırın.")


if __name__ == "__main__":
    main()

"""Validation-only model selection for the next classical-ML improvement step."""

import argparse
import csv
import json
import math
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.exceptions import ConvergenceWarning

from homtech.console import configure_utf8_console
from homtech.ml.features import HOG_PRESETS, extract_features, feature_config_for_preset
from homtech.ml.metrics import classification_metrics
from homtech.ml.model import build_estimator
from homtech.ml.rafdb import DEFAULT_ROOT, describe_samples, read_samples, split_samples
from homtech.settings import ARTIFACTS_DIR


DEFAULT_OUTPUT = ARTIFACTS_DIR / "runs" / "classical-search-001"


def write_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Classical HOG + SVM search. The official test split is excluded.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--presets", nargs="+", choices=tuple(HOG_PRESETS),
                        default=["baseline", "orient12", "finegrid"])
    parser.add_argument("--models", nargs="+", choices=("linear", "rbf"), default=["linear"])
    parser.add_argument("--c-values", nargs="+", type=float, default=[0.003, 0.01, 0.03])
    parser.add_argument("--pca-components", type=int, default=256,
                        help="PCA dimension before an RBF SVM; unused for linear SVM.")
    parser.add_argument("--train-augmentation", choices=("none", "flip"), default="none",
                        help="Training-only augmentation. Validation and official test are never augmented.")
    parser.add_argument("--validation-split", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-iter", type=int, default=20000)
    return parser


def run(args):
    if (not args.c_values or any(not math.isfinite(value) or value <= 0 for value in args.c_values)
            or args.pca_components < 2 or args.max_iter < 1):
        raise ValueError("C values must be positive; PCA components must be at least 2; max-iter must be positive.")
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise ValueError("Output directory must be empty; choose a new --output-dir.")
    samples = read_samples(args.data_dir)
    splits = split_samples(samples, args.validation_split, args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1, "status": "running", "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "validation-only classical ML search; official test split is excluded",
        "configuration": {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
        "dataset": {name: describe_samples(items, content_hash=True) for name, items in splits.items()},
        "selection_metric": "validation_macro_f1", "trials": [],
    }
    manifest_path = args.output_dir / "run_manifest.json"
    write_json(manifest_path, manifest)
    train_y = np.array([item.label for item in splits["train"]])
    if args.train_augmentation == "flip":
        train_y = np.concatenate((train_y, train_y))
    validation_y = np.array([item.label for item in splits["validation"]])
    best = None
    try:
        for preset in dict.fromkeys(args.presets):
            config = feature_config_for_preset(preset)
            print(f"HOG={preset}: training features...", flush=True)
            train_x = extract_features(
                splits["train"], progress=True, config=config,
                augment_horizontal_flip=args.train_augmentation == "flip")
            print(f"HOG={preset}: validation features...", flush=True)
            validation_x = extract_features(splits["validation"], progress=True, config=config)
            for model in dict.fromkeys(args.models):
                for c in dict.fromkeys(args.c_values):
                    print(f"Trying HOG={preset}, SVM={model}, C={c:g}", flush=True)
                    started = time.monotonic()
                    estimator = build_estimator(model, c, args.pca_components, args.seed, args.max_iter)
                    with warnings.catch_warnings(record=True) as caught:
                        warnings.simplefilter("always", ConvergenceWarning)
                        estimator.fit(train_x, train_y)
                    metrics = classification_metrics(validation_y, estimator.predict(validation_x))
                    trial = {"preset": preset, "feature_config": config, "model": model, "c": c,
                             "train_augmentation": args.train_augmentation,
                             "validation_accuracy": metrics["accuracy"],
                             "validation_macro_f1": metrics["macro_f1"],
                             "converged": not any(issubclass(item.category, ConvergenceWarning) for item in caught),
                             "elapsed_seconds": time.monotonic() - started}
                    manifest["trials"].append(trial)
                    if best is None or trial["validation_macro_f1"] > best["validation_macro_f1"]:
                        best = trial
                    manifest["best_trial"] = best
                    write_json(manifest_path, manifest)
                    print(f"  val_acc={trial['validation_accuracy']:.4f}, val_macro_f1={trial['validation_macro_f1']:.4f}", flush=True)
        manifest["status"] = "completed"
        write_json(manifest_path, manifest)
        fields = ["preset", "model", "c", "train_augmentation", "validation_accuracy",
                  "validation_macro_f1", "converged", "elapsed_seconds"]
        with (args.output_dir / "validation_results.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows({field: trial[field] for field in fields} for trial in manifest["trials"])
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
        manifest = run(args)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    best = manifest["best_trial"]
    print(f"Best validation candidate: {best['preset']} + {best['model']} (C={best['c']:g}), "
          f"macro F1={best['validation_macro_f1']:.4f}")
    print("The official test split was not used.")


if __name__ == "__main__":
    main()

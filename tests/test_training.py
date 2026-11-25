import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import joblib
import numpy as np
from PIL import Image, ImageDraw

from homtech.ml import evaluate as evaluation
from homtech.ml import train as training
from homtech.ml.evaluate import evaluate
from homtech.ml.features import extract_features, extract_image_features, make_descriptor
from homtech.ml.model import load_model
from homtech.ml.rafdb import CLASSES, read_samples
from test_rafdb import create_rafdb


def create_patterned_dataset(root):
    create_rafdb(root, train_per_class=4)
    for path in (root / "Image/aligned").glob("*.jpg"):
        raw_label = int(path.name.split("_")[1][:2])
        index = int(path.name.split("_")[1][2:])
        image = Image.new("RGB", (100, 100), "black")
        draw = ImageDraw.Draw(image)
        left = 5 + raw_label * 10
        draw.rectangle((left, 10 + index, left + 5, 85), fill="white")
        image.save(path)


class ClassicalTrainingTests(unittest.TestCase):
    def test_training_selection_persistence_and_final_evaluation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data, output = root / "data", root / "run"
            create_patterned_dataset(data)
            args = training.build_parser().parse_args([
                "--data-dir", str(data), "--output-dir", str(output), "--profile", "seven-linear",
                "--c-values", "0.01", "0.1",
            ])
            with patch.object(training, "extract_features", wraps=training.extract_features) as extractor:
                manifest = training.train(args)
            self.assertEqual(manifest["status"], "completed")
            self.assertEqual(manifest["algorithm"], "hog_linear_svm")
            self.assertEqual(extractor.call_count, 2)
            for call in extractor.call_args_list:
                self.assertTrue(all(item.split == "train" for item in call.args[0]))
            best_trial = max(manifest["trials"], key=lambda row: row["validation_macro_f1"])
            self.assertEqual(manifest["best_c"], best_trial["c"])
            self.assertTrue((output / "validation_results.csv").is_file())
            payload = load_model(output / "best.joblib")
            estimator = payload["estimator"]
            # Scaling must learn statistics from training only, excluding validation/test.
            self.assertEqual(int(estimator.named_steps["scaler"].n_samples_seen_),
                             manifest["dataset"]["train"]["total"])
            self.assertEqual(estimator.n_features_in_, 4356)
            self.assertEqual(payload["classes"], list(CLASSES))
            metrics = evaluate(output / "best.joblib", data, output / "evaluation")
            self.assertEqual(metrics["samples"], 7)
            self.assertGreaterEqual(metrics["accuracy"], 0.8)
            self.assertEqual(sum(map(sum, metrics["confusion_matrix"])), 7)
            for name in ("metrics.json", "confusion_matrix.csv", "confusion_matrix.png"):
                self.assertTrue((output / "evaluation" / name).is_file())
            self.assertFalse((output / "best.pt").exists())
            with self.assertRaisesRegex(ValueError, "boş olmalı"):
                training.train(args)
            Image.new("RGB", (100, 100), "red").save(data / "Image/aligned/test_01000_aligned.jpg")
            with self.assertRaisesRegex(ValueError, "eşleşmiyor"):
                evaluate(output / "best.joblib", data, output / "changed-data")
            payload["classes"] = list(reversed(CLASSES))
            joblib.dump(payload, output / "invalid.joblib")
            with self.assertRaisesRegex(ValueError, "uyumsuz"):
                load_model(output / "invalid.joblib")

    def test_default_rbf_profile_scores_only_the_six_supported_classes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data, output = root / "data", root / "run"
            create_patterned_dataset(data)
            args = training.build_parser().parse_args([
                "--data-dir", str(data), "--output-dir", str(output), "--pca-components", "4",
            ])
            manifest = training.train(args)
            classes = ["angry", "fear", "happy", "sad", "surprise", "neutral"]
            self.assertEqual(manifest["algorithm"], "hog_pca_rbf_svm")
            self.assertEqual(manifest["classes"], classes)
            for split in manifest["dataset"].values():
                self.assertEqual(split["counts"]["disgust"], 0)
            payload = load_model(output / "best.joblib")
            self.assertEqual(payload["estimator"].classes_.tolist(), [0, 2, 3, 4, 5, 6])
            metrics = evaluate(output / "best.joblib", data, output / "evaluation")
            self.assertEqual(metrics["classes"], classes)
            self.assertEqual(metrics["excluded_classes"], ["disgust"])
            self.assertEqual(metrics["split"], "official_test_subset")
            self.assertEqual(metrics["samples"], 6)
            self.assertEqual(metrics["official_test_samples"], 7)
            self.assertEqual(np.shape(metrics["confusion_matrix"]), (6, 6))
            self.assertEqual(sum(map(sum, metrics["confusion_matrix"])), 6)
            header = (output / "evaluation/confusion_matrix.csv").read_text(encoding="utf-8").splitlines()[0]
            self.assertEqual(header.split(",")[1:], classes)

    def test_camera_rbf_uses_an_independent_test_split_and_checks_the_original_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data, output, archive = root / "data", root / "run", root / "original.zip"
            create_patterned_dataset(data)
            archive.write_bytes(b"controlled original archive")
            args = training.build_parser().parse_args([
                "--data-dir", str(data), "--output-dir", str(output), "--profile", "camera-rbf",
                "--original-archive", str(archive), "--pca-components", "4",
            ])

            def features(samples, path, config, *, progress=False):
                self.assertEqual(path, archive)
                return extract_features(samples, config=config), samples

            with patch.object(training, "extract_capture_features", side_effect=features) as extractor:
                manifest = training.train(args)
            self.assertEqual(len(extractor.call_args_list), 2)
            self.assertTrue(all(sample.split == "train"
                                for call in extractor.call_args_list for sample in call.args[0]))
            payload = load_model(output / "best.joblib")
            self.assertEqual(payload["classes"], list(CLASSES))
            self.assertEqual(payload["suggestion_policy"], manifest["suggestion_policy"])
            with patch.object(evaluation, "extract_capture_features", side_effect=features) as extractor:
                metrics = evaluate(output / "best.joblib", data, output / "evaluation")
            self.assertTrue(all(sample.split == "test" for sample in extractor.call_args.args[0]))
            self.assertEqual(metrics["input_kind"], "original_rafdb_after_face_detection")
            self.assertEqual(metrics["accepted_predictions"] + metrics["uncertain"], 7)
            archive.write_bytes(b"changed original archive")
            with self.assertRaisesRegex(ValueError, "arşivi eğitim manifestiyle eşleşmiyor"):
                evaluate(output / "best.joblib", data, output / "different-archive")

    def test_failed_training_is_recorded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_rafdb(root / "data", train_per_class=2)
            args = training.build_parser().parse_args([
                "--data-dir", str(root / "data"), "--output-dir", str(root / "run"),
            ])
            with patch.object(training, "extract_features", side_effect=ValueError("broken image")):
                with self.assertRaisesRegex(ValueError, "broken image"):
                    training.train(args)
            manifest = json.loads((root / "run/run_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "failed")
            self.assertFalse((root / "run/best.joblib").exists())

    def test_rejects_invalid_svm_parameters_before_creating_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            for value in ("-1", "nan", "inf"):
                args = training.build_parser().parse_args([
                    "--c-values", value, "--output-dir", str(Path(directory) / "run"),
                ])
                with self.assertRaises(ValueError):
                    training.train(args)
            self.assertFalse((Path(directory) / "run").exists())

    def test_hog_is_deterministic_and_sensitive_to_shape(self):
        vertical = Image.new("L", (100, 100))
        ImageDraw.Draw(vertical).rectangle((20, 10, 30, 90), fill=255)
        horizontal = Image.new("L", (100, 100))
        ImageDraw.Draw(horizontal).rectangle((10, 20, 90, 30), fill=255)
        first = extract_image_features(vertical)
        np.testing.assert_array_equal(first, extract_image_features(vertical))
        self.assertEqual(first.shape, (make_descriptor().getDescriptorSize(),))
        self.assertTrue(np.isfinite(first).all())
        self.assertFalse(np.array_equal(first, extract_image_features(horizontal)))

    def test_rejects_corrupt_images_during_feature_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_rafdb(root)
            samples = read_samples(root)
            samples[0].path.write_bytes(b"broken")
            with self.assertRaisesRegex(ValueError, "çıkarılamadı"):
                extract_features(samples)

    def test_macro_f1_includes_all_seven_classes(self):
        from homtech.ml.metrics import classification_metrics
        perfect = classification_metrics(list(range(7)), list(range(7)))
        self.assertEqual(perfect["macro_f1"], 1.0)
        constant = classification_metrics(list(range(7)), [0] * 7)
        self.assertAlmostEqual(constant["accuracy"], 1 / 7)
        self.assertAlmostEqual(constant["macro_f1"], 0.25 / 7)


if __name__ == "__main__":
    unittest.main()

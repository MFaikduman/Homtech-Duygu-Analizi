import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from homtech.ml import experiment
from test_rafdb import create_rafdb


class ClassicalExperimentTests(unittest.TestCase):
    def test_search_uses_training_and_validation_features_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data, output = root / "data", root / "run"
            create_rafdb(data, train_per_class=3)
            args = experiment.build_parser().parse_args([
                "--data-dir", str(data), "--output-dir", str(output),
                "--presets", "baseline", "orient12", "--models", "linear", "--c-values", "0.01",
            ])
            with patch.object(experiment, "extract_features", wraps=experiment.extract_features) as extractor:
                manifest = experiment.run(args)
            self.assertEqual(manifest["status"], "completed")
            self.assertEqual(len(manifest["trials"]), 2)
            self.assertTrue(all(item.split == "train" for call in extractor.call_args_list for item in call.args[0]))
            self.assertTrue((output / "validation_results.csv").is_file())
            self.assertNotIn("test", [item.split for call in extractor.call_args_list for item in call.args[0]])

    def test_horizontal_flip_augmentation_doubles_training_rows_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data, output = root / "data", root / "run"
            create_rafdb(data, train_per_class=3)
            args = experiment.build_parser().parse_args([
                "--data-dir", str(data), "--output-dir", str(output), "--presets", "baseline",
                "--models", "linear", "--c-values", "0.01", "--train-augmentation", "flip",
            ])
            manifest = experiment.run(args)
            self.assertEqual(manifest["trials"][0]["train_augmentation"], "flip")
            self.assertEqual(manifest["status"], "completed")


if __name__ == "__main__":
    unittest.main()

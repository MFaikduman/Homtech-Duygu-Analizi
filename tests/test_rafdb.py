import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from homtech.ml.rafdb import (
    CLASSES, IMAGE_DIR, LABEL_FILE, RAF_LABELS, describe_samples, main, read_samples, split_samples,
)


def create_rafdb(root: Path, train_per_class: int = 4) -> None:
    (root / LABEL_FILE).parent.mkdir(parents=True)
    (root / IMAGE_DIR).mkdir(parents=True)
    rows = []
    for raw_label in range(1, 8):
        for split, count in (("train", train_per_class), ("test", 1)):
            for index in range(count):
                name = f"{split}_{raw_label:02d}{index:03d}.jpg"
                rows.append(f"{name} {raw_label}")
                # Unique, synthetic RGB images. No real faces or restricted data.
                image = Image.new("RGB", (100, 100), (raw_label * 30, index * 35,
                                                      50 if split == "train" else 180))
                image.save(root / IMAGE_DIR / f"{Path(name).stem}_aligned.jpg")
    (root / LABEL_FILE).write_text("\n".join(rows), encoding="utf-8")


class RAFDBTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        create_rafdb(self.root)

    def test_converts_official_labels_to_application_indices(self):
        samples = read_samples(self.root, verify_images=True)
        for raw_label, emotion in RAF_LABELS.items():
            sample = next(item for item in samples if item.name == f"train_{raw_label:02d}000.jpg")
            self.assertEqual(CLASSES[sample.label], emotion)
        self.assertEqual(len(samples), 35)

    def test_split_is_stratified_disjoint_and_independent_of_input_order(self):
        samples = read_samples(self.root)
        splits = split_samples(samples, 0.25, seed=42)
        repeated = split_samples(list(reversed(samples)), 0.25, seed=42)
        self.assertEqual(splits, repeated)
        sets = {name: {sample.name for sample in items} for name, items in splits.items()}
        self.assertFalse(sets["train"] & sets["validation"])
        self.assertFalse((sets["train"] | sets["validation"]) & sets["test"])
        self.assertEqual(sets["test"], {sample.name for sample in samples if sample.split == "test"})
        self.assertEqual(set.union(*sets.values()), {sample.name for sample in samples})
        self.assertTrue(all(len({sample.label for sample in items}) == 7 for items in splits.values()))
        self.assertNotEqual(splits["validation"], split_samples(samples, 0.25, seed=7)["validation"])

    def test_rejects_invalid_labels_names_and_duplicate_ids(self):
        path = self.root / LABEL_FILE
        original = path.read_text(encoding="utf-8")
        for extra in ("train_99999.jpg 8", "../train_99999.jpg 1", "train_01000.jpg 1"):
            with self.subTest(extra=extra):
                path.write_text(original + "\n" + extra, encoding="utf-8")
                with self.assertRaises(ValueError):
                    read_samples(self.root)

    def test_rejects_missing_and_corrupt_images(self):
        sample = read_samples(self.root)[0]
        sample.path.write_bytes(b"not an image")
        with self.assertRaisesRegex(ValueError, "Görsel okunamadı"):
            read_samples(self.root, verify_images=True)
        sample.path.unlink()
        with self.assertRaises(FileNotFoundError):
            read_samples(self.root)

    def test_requires_sufficient_training_and_all_test_classes(self):
        samples = read_samples(self.root)
        for bad in ([item for item in samples if item.label != 0 or item.split == "test"],
                    [item for item in samples if item.label != 0 or item.split == "train"]):
            with self.assertRaises(ValueError):
                split_samples(bad)
        for fraction in (0, 1, float("nan")):
            with self.assertRaises(ValueError):
                split_samples(samples, fraction)

    def test_fingerprint_detects_image_and_label_changes(self):
        samples = read_samples(self.root)
        before = describe_samples(samples, content_hash=True)
        self.assertEqual(before, describe_samples(list(reversed(samples)), content_hash=True))
        Image.new("RGB", (100, 100), "red").save(samples[0].path)
        self.assertNotEqual(before["sha256"], describe_samples(samples, content_hash=True)["sha256"])
        path = self.root / LABEL_FILE
        path.write_text(path.read_text(encoding="utf-8").replace("test_01000.jpg 1", "test_01000.jpg 2"),
                        encoding="utf-8")
        self.assertNotEqual(describe_samples(samples)["sha256"], describe_samples(read_samples(self.root))["sha256"])

    def test_missing_dataset_cli_exits_with_actionable_error(self):
        error = io.StringIO()
        with contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as raised:
            main(["--data-dir", str(self.root / "missing")])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("docs/emotionai.md", error.getvalue())


if __name__ == "__main__":
    unittest.main()

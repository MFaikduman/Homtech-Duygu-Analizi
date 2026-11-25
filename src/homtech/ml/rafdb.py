"""Read RAF-DB BasicEmo's official labels without importing a training framework."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from homtech.console import configure_utf8_console
from homtech.settings import RAW_DATA_DIR, EMOTION_LABELS


DEFAULT_ROOT = RAW_DATA_DIR / "rafdb" / "BasicEmo"
# RAF-DB's one-based IDs are NOT the application's class indices.
RAF_LABELS = {1: "surprise", 2: "fear", 3: "disgust", 4: "happy",
              5: "sad", 6: "angry", 7: "neutral"}
CLASSES = tuple(EMOTION_LABELS)
SIX_CLASSES = tuple(label for label in CLASSES if label != "disgust")
LABEL_FILE = Path("EmoLabel/list_patition_label.txt")  # Official spelling.
IMAGE_DIR = Path("Image/aligned")
NAME_PATTERN = re.compile(r"(train|test)_[0-9]+\.jpg", re.ASCII)


@dataclass(frozen=True)
class Sample:
    name: str
    path: Path
    label: int
    split: str


def read_samples(root: Path, *, verify_images: bool = False) -> list[Sample]:
    """Reject missing files, duplicate IDs and invalid labels before training."""
    root = Path(root)
    label_path = root / LABEL_FILE
    if not label_path.is_file():
        raise FileNotFoundError(
            f"RAF-DB etiket dosyası bulunamadı: {label_path}. "
            "BasicEmo klasörünü --data-dir ile belirtin; bkz. docs/emotionai.md."
        )
    samples = []
    seen = set()
    for line_number, line in enumerate(label_path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2 or not NAME_PATTERN.fullmatch(parts[0]):
            raise ValueError(f"Geçersiz RAF-DB kaydı, satır {line_number}: {line!r}")
        name, raw_label = parts
        try:
            emotion = RAF_LABELS[int(raw_label)]
        except (ValueError, KeyError) as exc:
            raise ValueError(f"Etiket 1–7 olmalı, satır {line_number}: {raw_label}") from exc
        if name in seen:
            raise ValueError(f"Tekrarlanan görsel kimliği: {name}")
        seen.add(name)
        path = root / IMAGE_DIR / f"{Path(name).stem}_aligned.jpg"
        if not path.is_file():
            raise FileNotFoundError(f"Hizalanmış yüz görseli bulunamadı: {path}")
        if verify_images:
            try:
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    image.convert("RGB").load()
            except (OSError, ValueError) as exc:
                raise ValueError(f"Görsel okunamadı: {path}") from exc
        samples.append(Sample(name, path, CLASSES.index(emotion), name.split("_")[0]))
    if not samples:
        raise ValueError("RAF-DB etiket dosyası boş.")
    return sorted(samples, key=lambda sample: sample.name)


def split_samples(samples: list[Sample], validation_fraction: float = 0.15,
                  seed: int = 42) -> dict[str, list[Sample]]:
    """Stratify official TRAIN only; preserve the official test set untouched."""
    if not 0 < validation_fraction < 1:
        raise ValueError("Doğrulama oranı 0 ile 1 arasında olmalı.")
    splits = {"train": [], "validation": [], "test": []}
    splits["test"] = sorted((sample for sample in samples if sample.split == "test"),
                            key=lambda sample: sample.name)
    for index, emotion in enumerate(CLASSES):
        group = sorted((sample for sample in samples
                        if sample.split == "train" and sample.label == index),
                       key=lambda sample: sample.name)
        if len(group) < 2:
            raise ValueError(f"{emotion}: eğitim/doğrulama ayrımı için en az 2 görsel gerekli.")
        random.Random(seed + index).shuffle(group)
        count = min(len(group) - 1, max(1, int(len(group) * validation_fraction)))
        splits["validation"].extend(group[:count])
        splits["train"].extend(group[count:])
    for index, emotion in enumerate(CLASSES):
        if not any(sample.label == index for sample in splits["test"]):
            raise ValueError(f"Test kümesinde sınıf eksik: {emotion}")
    return splits


def describe_samples(samples: list[Sample], *, content_hash: bool = False) -> dict:
    digest = hashlib.sha256()
    for sample in sorted(samples, key=lambda item: item.name):
        digest.update(f"{sample.name}\t{sample.label}\n".encode("utf-8"))
        if content_hash:
            with sample.path.open("rb") as stream:
                file_digest = hashlib.file_digest(stream, "sha256").hexdigest()
            digest.update(file_digest.encode("ascii"))
    counts = Counter(sample.label for sample in samples)
    return {"total": len(samples),
            "counts": {label: counts[index] for index, label in enumerate(CLASSES)},
            "sha256": digest.hexdigest(),
            "hash_includes_image_content": content_hash}


def main(argv=None) -> None:
    configure_utf8_console()
    parser = argparse.ArgumentParser(description="RAF-DB etiket, görsel ve sınıf dağılımını doğrula.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--validation-split", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--verify-images", action="store_true")
    parser.add_argument("--output", type=Path, help="İsteğe bağlı JSON raporu")
    args = parser.parse_args(argv)
    try:
        samples = read_samples(args.data_dir, verify_images=args.verify_images)
        splits = split_samples(samples, args.validation_split, args.seed)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Hata: {exc}\n")
    report = {"dataset": "RAF-DB BasicEmo", "classes": CLASSES,
              "official_label_mapping": RAF_LABELS,
              "seed": args.seed, "validation_fraction": args.validation_split,
              "images_verified": args.verify_images,
              "splits": {name: describe_samples(items) for name, items in splits.items()},
              "official_counts_match": (
                  sum(sample.split == "train" for sample in samples) == 12271
                  and len(splits["test"]) == 3068)}
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    print(payload)
    if not report["official_counts_match"]:
        print("Uyarı: Sayılar beklenen 12.271 eğitim / 3.068 test ile eşleşmiyor.")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()

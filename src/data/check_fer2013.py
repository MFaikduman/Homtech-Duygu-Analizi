"""FER-2013 klasor yapisini kontrol eder."""

from pathlib import Path

from src.config import EMOTION_LABELS, TEST_DIR, TRAIN_DIR


def count_images(folder: Path) -> int:
    patterns = ("*.png", "*.jpg", "*.jpeg", "*.bmp")
    return sum(len(list(folder.glob(pattern))) for pattern in patterns)


def check_split(split_name: str, split_dir: Path) -> None:
    print(f"\n[{split_name.upper()}]")

    if not split_dir.exists():
        print(f"Klasor bulunamadi: {split_dir}")
        return

    total = 0
    for label in EMOTION_LABELS:
        class_dir = split_dir / label
        if not class_dir.exists():
            print(f"- {label}: klasor eksik")
            continue

        image_count = count_images(class_dir)
        total += image_count
        print(f"- {label}: {image_count} gorsel")

    print(f"Toplam: {total} gorsel")


def main() -> None:
    print("FER-2013 veri seti kontrolu basladi.")
    check_split("train", TRAIN_DIR)
    check_split("test", TEST_DIR)


if __name__ == "__main__":
    main()

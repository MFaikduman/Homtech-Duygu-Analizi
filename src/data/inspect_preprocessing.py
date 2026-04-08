"""Veri yukleme ve on isleme adimini kontrol eder."""

from src.data.data_loader import get_dataset_info, load_datasets


def print_info(split_name, dataset):
    info = get_dataset_info(dataset)
    print(f"\n[{split_name}]")
    print(f"Goruntu batch sekli: {info['image_batch_shape']}")
    print(f"Etiket batch sekli: {info['label_batch_shape']}")
    print(f"Goruntu veri tipi: {info['image_dtype']}")
    print(f"Etiket veri tipi: {info['label_dtype']}")
    print(f"Piksel min: {info['pixel_min']}")
    print(f"Piksel max: {info['pixel_max']}")


def main():
    print("Veri yukleme ve on isleme kontrolu basladi.")
    train_dataset, validation_dataset, test_dataset, steps_per_epoch = load_datasets()

    print_info("TRAIN", train_dataset)
    print_info("VALIDATION", validation_dataset)
    print_info("TEST", test_dataset)
    print(f"\nStep sayisi: {steps_per_epoch}")


if __name__ == "__main__":
    main()

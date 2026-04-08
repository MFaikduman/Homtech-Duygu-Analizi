"""FER-2013 veri yukleme ve on isleme yardimcilari."""

from pathlib import Path

import numpy as np
import tensorflow as tf

from src.config import (
    BATCH_SIZE,
    EMOTION_LABELS,
    IMAGE_SIZE,
    SEED,
    TEST_DIR,
    TRAINING_OVERSAMPLE_FACTOR,
    TRAIN_DIR,
    VALIDATION_SPLIT,
)
from src.image_preprocessing import adapt_to_fer_style_rgb


AUTOTUNE = tf.data.AUTOTUNE
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")


def _collect_samples(directory: Path):
    image_paths = []
    labels = []

    for class_index, class_name in enumerate(EMOTION_LABELS):
        class_dir = directory / class_name
        if not class_dir.exists():
            raise FileNotFoundError(f"Sinif klasoru bulunamadi: {class_dir}")

        for extension in IMAGE_EXTENSIONS:
            for image_path in sorted(class_dir.glob(f"*{extension}")):
                image_paths.append(str(image_path))
                labels.append(class_index)

    if not image_paths:
        raise ValueError(f"Gorsel bulunamadi: {directory}")

    return image_paths, labels


def _apply_fer_style_preprocessing(image: np.ndarray) -> np.ndarray:
    return adapt_to_fer_style_rgb(image)


def _load_and_preprocess_image(image_path, label):
    image_bytes = tf.io.read_file(image_path)
    image = tf.io.decode_image(
        image_bytes,
        channels=3,
        expand_animations=False,
    )
    image.set_shape([None, None, 3])
    image = tf.image.resize(image, IMAGE_SIZE)
    image = tf.cast(image, tf.uint8)
    image = tf.numpy_function(_apply_fer_style_preprocessing, [image], tf.uint8)
    image.set_shape([IMAGE_SIZE[0], IMAGE_SIZE[1], 3])
    image = tf.cast(image, tf.float32)
    label = tf.one_hot(label, depth=len(EMOTION_LABELS))
    return image, label


def _build_class_dataset(image_paths, labels, class_index):
    class_image_paths = [
        image_path
        for image_path, label in zip(image_paths, labels)
        if label == class_index
    ]
    class_labels = [class_index] * len(class_image_paths)
    return tf.data.Dataset.from_tensor_slices((class_image_paths, class_labels))


def _build_dataset(image_paths, labels, shuffle: bool):
    dataset = tf.data.Dataset.from_tensor_slices((image_paths, labels))
    if shuffle:
        dataset = dataset.shuffle(buffer_size=len(image_paths), seed=SEED)

    dataset = dataset.map(_load_and_preprocess_image, num_parallel_calls=AUTOTUNE)
    dataset = dataset.cache().batch(BATCH_SIZE).prefetch(AUTOTUNE)
    return dataset


def _split_train_validation(image_paths, labels):
    train_paths = []
    train_labels = []
    validation_paths = []
    validation_labels = []

    for class_index in range(len(EMOTION_LABELS)):
        class_samples = [
            (path, label)
            for path, label in zip(image_paths, labels)
            if label == class_index
        ]
        rng = np.random.default_rng(SEED + class_index)
        rng.shuffle(class_samples)

        validation_count = max(1, int(len(class_samples) * VALIDATION_SPLIT))
        validation_samples = class_samples[:validation_count]
        train_samples = class_samples[validation_count:]

        if not train_samples:
            raise ValueError(
                f"Egitim icin yeterli veri kalmadi: {EMOTION_LABELS[class_index]}"
            )

        for image_path, label in train_samples:
            train_paths.append(image_path)
            train_labels.append(label)

        for image_path, label in validation_samples:
            validation_paths.append(image_path)
            validation_labels.append(label)

    return train_paths, train_labels, validation_paths, validation_labels


def _build_balanced_train_dataset(image_paths, labels):
    label_counts = {index: 0 for index in range(len(EMOTION_LABELS))}
    class_datasets = []

    for label in labels:
        label_counts[label] += 1

    max_count = max(label_counts.values())

    for class_index in range(len(EMOTION_LABELS)):
        class_dataset = _build_class_dataset(image_paths, labels, class_index)
        class_dataset = class_dataset.shuffle(
            buffer_size=max(label_counts[class_index], 1),
            seed=SEED,
            reshuffle_each_iteration=True,
        ).repeat()
        class_datasets.append(class_dataset)

    target_samples = max_count * len(EMOTION_LABELS) * TRAINING_OVERSAMPLE_FACTOR
    dataset = tf.data.Dataset.sample_from_datasets(
        class_datasets,
        weights=[1.0 / len(EMOTION_LABELS)] * len(EMOTION_LABELS),
        seed=SEED,
        stop_on_empty_dataset=False,
    )
    dataset = dataset.take(target_samples)
    dataset = dataset.map(_load_and_preprocess_image, num_parallel_calls=AUTOTUNE)
    dataset = dataset.batch(BATCH_SIZE).prefetch(AUTOTUNE)

    steps_per_epoch = max(1, target_samples // BATCH_SIZE)
    return dataset, steps_per_epoch


def load_datasets():
    train_image_paths, train_labels = _collect_samples(TRAIN_DIR)
    test_image_paths, test_labels = _collect_samples(TEST_DIR)

    (
        train_image_paths,
        train_labels,
        validation_image_paths,
        validation_labels,
    ) = _split_train_validation(train_image_paths, train_labels)

    train_dataset, steps_per_epoch = _build_balanced_train_dataset(
        train_image_paths,
        train_labels,
    )
    validation_dataset = _build_dataset(
        validation_image_paths,
        validation_labels,
        shuffle=False,
    )
    test_dataset = _build_dataset(test_image_paths, test_labels, shuffle=False)
    return train_dataset, validation_dataset, test_dataset, steps_per_epoch


def get_class_weights():
    train_image_paths, train_labels = _collect_samples(TRAIN_DIR)

    train_image_paths, train_labels, _, _ = _split_train_validation(
        train_image_paths,
        train_labels,
    )

    total_samples = len(train_labels)
    num_classes = len(EMOTION_LABELS)
    label_counts = {index: 0 for index in range(num_classes)}
    for label in train_labels:
        label_counts[label] += 1

    return {
        label: total_samples / (num_classes * count)
        for label, count in label_counts.items()
        if count > 0
    }


def get_label_counts(directory: Path):
    _, labels = _collect_samples(directory)
    counts = {index: 0 for index in range(len(EMOTION_LABELS))}
    for label in labels:
        counts[label] += 1
    return counts


def get_dataset_info(dataset):
    images, labels = next(iter(dataset.take(1)))
    return {
        "image_batch_shape": tuple(images.shape),
        "label_batch_shape": tuple(labels.shape),
        "image_dtype": images.dtype.name,
        "label_dtype": labels.dtype.name,
        "pixel_min": float(tf.reduce_min(images).numpy()),
        "pixel_max": float(tf.reduce_max(images).numpy()),
    }

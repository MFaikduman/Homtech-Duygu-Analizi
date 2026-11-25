"""Deterministic, hand-crafted HOG features. No neural network or learned encoder."""

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps


FEATURE_CONFIG = {
    "method": "HOG", "image_size": [96, 96], "grayscale": True,
    "equalize_histogram": True, "orientations": 9,
    "pixels_per_cell": [8, 8], "block_size": [16, 16], "block_stride": [8, 8],
}

# Small, explainable feature-engineering variants for classical ML experiments.
HOG_PRESETS = {
    "baseline": FEATURE_CONFIG,
    "orient12": {**FEATURE_CONFIG, "orientations": 12},
    "finegrid": {**FEATURE_CONFIG, "pixels_per_cell": [6, 6],
                 "block_size": [12, 12], "block_stride": [6, 6]},
    "highres": {**FEATURE_CONFIG, "image_size": [128, 128]},
}


def feature_config_for_preset(name: str) -> dict:
    try:
        return dict(HOG_PRESETS[name])
    except KeyError as exc:
        raise ValueError(f"Unknown HOG preset: {name}. Available: {', '.join(HOG_PRESETS)}.") from exc


def make_descriptor(config: dict | None = None):
    config = FEATURE_CONFIG if config is None else config
    width, height = config["image_size"]
    cell_width, cell_height = config["pixels_per_cell"]
    block_width, block_height = config["block_size"]
    stride_width, stride_height = config["block_stride"]
    if (width % cell_width or height % cell_height
            or block_width % cell_width or block_height % cell_height
            or stride_width % cell_width or stride_height % cell_height
            or (width - block_width) % stride_width or (height - block_height) % stride_height):
        raise ValueError("Incompatible HOG window, cell, block, or stride sizes.")
    return cv2.HOGDescriptor((width, height), (block_width, block_height),
                             (stride_width, stride_height), (cell_width, cell_height),
                             int(config["orientations"]))


def extract_image_features(image: Image.Image, descriptor=None, *, config: dict | None = None) -> np.ndarray:
    config = FEATURE_CONFIG if config is None else config
    gray = ImageOps.exif_transpose(image).convert("L").resize(tuple(config["image_size"]), Image.Resampling.BILINEAR)
    pixels = np.asarray(gray)
    if config.get("equalize_histogram", False):
        pixels = cv2.equalizeHist(pixels)
    descriptor = descriptor if descriptor is not None else make_descriptor(config)
    result = descriptor.compute(pixels).reshape(-1).astype(np.float32)
    if not np.isfinite(result).all():
        raise ValueError("HOG özellikleri sonlu olmalı.")
    return result


def extract_features(samples, *, progress: bool = False, config: dict | None = None,
                     augment_horizontal_flip: bool = False) -> np.ndarray:
    if not samples:
        raise ValueError("Özellik çıkarılacak görsel listesi boş.")
    config = FEATURE_CONFIG if config is None else config
    descriptor = make_descriptor(config)
    rows = len(samples) * (2 if augment_horizontal_flip else 1)
    matrix = np.empty((rows, descriptor.getDescriptorSize()), dtype=np.float32)
    for index, sample in enumerate(samples):
        try:
            with Image.open(Path(sample.path)) as image:
                matrix[index] = extract_image_features(image, descriptor, config=config)
                if augment_horizontal_flip:
                    matrix[len(samples) + index] = extract_image_features(
                        ImageOps.mirror(image), descriptor, config=config)
        except (OSError, ValueError) as exc:
            raise ValueError(f"Görsel özellikleri çıkarılamadı: {sample.path}") from exc
        if progress and ((index + 1) % 1000 == 0 or index + 1 == len(samples)):
            print(f"HOG: {index + 1}/{len(samples)} görsel", flush=True)
    return matrix

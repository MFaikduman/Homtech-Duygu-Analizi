"""Egitim ve tahminde ortak goruntu on isleme yardimcilari."""

from __future__ import annotations

import cv2
import numpy as np


def adapt_to_fer_style_rgb(image_rgb: np.ndarray) -> np.ndarray:
    """Gorseli FER benzeri gri tonlu ve kontrast dengeli formata yaklastir."""
    if image_rgb.ndim != 3 or image_rgb.shape[-1] != 3:
        raise ValueError("Beklenen RGB goruntu gelmedi")

    image_rgb = np.asarray(image_rgb, dtype=np.uint8)
    gray_image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    equalized = cv2.equalizeHist(gray_image)
    return cv2.cvtColor(equalized, cv2.COLOR_GRAY2RGB)


def build_tta_variants(image_rgb: np.ndarray) -> np.ndarray:
    """Tahmin icin hafif test-time augmentation varyantlari olustur."""
    base = np.asarray(image_rgb, dtype=np.float32)
    horizontal_flip = np.flip(base, axis=1)
    center_crop = base[4:-4, 4:-4]
    center_crop = cv2.resize(center_crop, (base.shape[1], base.shape[0]))
    return np.stack([base, horizontal_flip, center_crop], axis=0)

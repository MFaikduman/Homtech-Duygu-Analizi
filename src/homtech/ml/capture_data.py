"""Build camera-model features from the original RAF-DB image archive."""

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import os
from pathlib import Path
from threading import local
from zipfile import ZipFile

import cv2
import numpy as np
from PIL import Image

from homtech.ml.features import extract_image_features, make_descriptor
from homtech.ml.predict import FaceDetector, ImageInputError, prepare_photo
from homtech.settings import DOWNLOADS_DIR


DEFAULT_ORIGINAL_ARCHIVE = DOWNLOADS_DIR / "rafdb" / "basic" / "Image" / "original.zip"


def extract_capture_features(samples, archive: Path, config: dict, *, progress=False):
    """Match desktop preprocessing and keep rejections outside model fitting."""
    worker = local()
    previous_threads = cv2.getNumThreads()
    cv2.setNumThreads(1)
    try:
        with ZipFile(archive) as images, ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 1)) as pool:
            def extract(sample):
                if not hasattr(worker, "detector"):
                    worker.detector = FaceDetector()
                    worker.descriptor = make_descriptor(config)
                try:
                    raw = images.read(f"original/{sample.name}")
                except KeyError:
                    raise ValueError(f"Orijinal arşivde görüntü eksik: {sample.name}") from None
                with Image.open(BytesIO(raw)) as opened:
                    try:
                        image = prepare_photo(opened)
                        face, _ = worker.detector.extract(image)
                    except ImageInputError:
                        return None
                return extract_image_features(face, worker.descriptor, config=config)

            retained = []
            features = []
            for index, (sample, row) in enumerate(zip(samples, pool.map(extract, samples)), 1):
                if row is not None:
                    retained.append(sample)
                    features.append(row)
                if progress and (index % 1000 == 0 or index == len(samples)):
                    print(f"Kamera önişleme: {index}/{len(samples)}, tek yüz: {len(retained)}", flush=True)
    finally:
        cv2.setNumThreads(previous_threads)
    if not features:
        raise ValueError("Orijinal görüntülerde kullanılabilir yüz bulunamadı.")
    return np.stack(features), retained

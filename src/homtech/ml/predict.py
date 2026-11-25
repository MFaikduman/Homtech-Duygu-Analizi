"""Local face detection, alignment and expression prediction for captured images."""

from dataclasses import dataclass
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

from homtech.ml.features import extract_image_features, make_descriptor
from homtech.ml.model import RBF_ALGORITHM, load_model
from homtech.ml.rafdb import CLASSES
from homtech.settings import ALIGNED_MODEL_DIR, CAPTURE_MODEL_DIR


MAX_IMAGE_EDGE = 720
DEFAULT_CAPTURE_MODEL = CAPTURE_MODEL_DIR / "best.joblib"
DEFAULT_ALIGNED_MODEL = ALIGNED_MODEL_DIR / "best.joblib"
MULTIPLE_FACES = "Birden fazla yüz bulundu. Lütfen tek kişinin olduğu bir görüntü kullanın."


class ImageInputError(ValueError):
    """An expected image or face detection problem that can be shown to the user."""


class FaceNotFound(ImageInputError):
    """The normal face detector could not locate a face."""


@dataclass(frozen=True)
class Expression:
    label: str
    uncertain: bool
    face: tuple[float, float, float, float]
    close_portrait: bool = False
    second_label: str | None = None


def rank_expressions(estimator, features):
    scores = estimator.decision_function(features.reshape(1, -1))[0]
    first, second = np.argsort(-scores, kind="stable")[:2]
    first_label = CLASSES[int(estimator.classes_[first])]
    second_label = CLASSES[int(estimator.classes_[second])]
    return first_label, second_label, float(scores[first] - scores[second])


def read_photo(path: Path) -> Image.Image:
    try:
        with path.open("rb") as stream, Image.open(stream, formats=("JPEG", "PNG", "WEBP", "BMP", "TIFF")) as image:
            return prepare_photo(image)
    except (OSError, Image.DecompressionBombError):
        raise ImageInputError("Fotoğraf açılamadı. Geçerli bir fotoğraf dosyası seçin.") from None


def prepare_photo(image: Image.Image) -> Image.Image:
    if image.width * image.height > 32_000_000:
        raise ImageInputError("Bu fotoğraf çok büyük. Daha küçük bir fotoğraf seçin.")
    image = ImageOps.exif_transpose(image)
    image.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE), Image.Resampling.LANCZOS)
    return image.convert("RGB")


def normalized_bounds(x, y, w, h, width, height):
    left, top = max(0, x), max(0, y)
    right, bottom = min(width, x + w), min(height, y + h)
    return left / width, top / height, (right - left) / width, (bottom - top) / height


class FaceDetector:
    def __init__(self):
        self.faces = self._cascade("frontalface_default")
        self.eyes = self._cascade("eye_tree_eyeglasses")
        self._close_faces = None
        self._portrait_faces = None

    def _cascade(self, name):
        path = Path(cv2.data.haarcascades) / f"haarcascade_{name}.xml"
        cascade = cv2.CascadeClassifier(str(path))
        if cascade.empty():
            raise RuntimeError("OpenCV yüz algılama dosyaları yüklenemedi.")
        return cascade

    def extract(self, image: Image.Image) -> tuple[Image.Image, tuple[float, float, float, float]]:
        gray = np.asarray(image.convert("L"))
        height, width = gray.shape
        if min(width, height) < 48:
            raise ImageInputError("Fotoğraf çok küçük. Yüzün daha net göründüğü bir fotoğraf seçin.")
        enhanced = cv2.equalizeHist(gray)
        # Allow a tight portrait whose facial landmarks sit near an image edge.
        padding = round(0.09 * min(width, height))
        padded = cv2.copyMakeBorder(enhanced, padding, padding, padding, padding, cv2.BORDER_REPLICATE)
        faces = self.faces.detectMultiScale(padded, scaleFactor=1.10, minNeighbors=5, minSize=(46, 46))
        if len(faces) == 0:
            raise FaceNotFound("Yüz bulunamadı. Yüzünüzün tamamının göründüğü bir fotoğraf deneyin.")
        if len(faces) > 1:
            raise ImageInputError(MULTIPLE_FACES)
        x, y, w, h = map(int, faces[0])
        x, y = x - padding, y - padding
        bounds = normalized_bounds(x, y, w, h, width, height)
        eyes = self._find_eyes(enhanced, x, y, w, h)
        if eyes is None:
            scale = 100 / (1.10 * max(w, h))
            matrix = np.array([[scale, 0, 50 - scale * (x + w / 2)],
                               [0, scale, 51 - scale * (y + h / 2)]])
        else:
            first, second = eyes
            dx, dy = second[0] - first[0], second[1] - first[1]
            midpoint = ((first[0] + second[0]) / 2, (first[1] + second[1]) / 2)
            matrix = cv2.getRotationMatrix2D(midpoint, math.degrees(math.atan2(dy, dx)),
                                            44 / math.hypot(dx, dy))
            matrix[:, 2] += np.array((50.5, 34.5)) - midpoint
        aligned = cv2.warpAffine(gray, matrix, (100, 100),
                                 flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        return Image.fromarray(aligned), bounds

    def find_close_portrait(self, image: Image.Image) -> tuple[float, float, float, float] | None:
        """Try extra context around a tightly framed, nearly square portrait."""
        gray = np.asarray(image.convert("L"))
        height, width = gray.shape
        if not 0.8 <= width / height <= 1.25:
            return None
        if self._close_faces is None:
            self._close_faces = self._cascade("frontalface_alt2")
        enhanced = cv2.equalizeHist(gray)
        edge = min(width, height)
        minimum_face = max(46, math.ceil(0.65 * edge))
        bounds = None
        for cascade, pixels, padding in (
            (self._close_faces, gray, round(0.17 * edge)),
            (self._close_faces, enhanced, round(0.17 * edge)),
            (self.faces, enhanced, round(0.21 * edge)),
        ):
            padded = cv2.copyMakeBorder(pixels, padding, padding, padding, padding, cv2.BORDER_REPLICATE)
            # Keep all detected faces in the decision, including a smaller second face.
            faces = cascade.detectMultiScale(padded, scaleFactor=1.10, minNeighbors=4, minSize=(46, 46))
            if len(faces) > 1:
                raise ImageInputError(MULTIPLE_FACES)
            if len(faces) == 1 and bounds is None:
                x, y, w, h = map(int, faces[0])
                if min(w, h) >= minimum_face:
                    bounds = normalized_bounds(x - padding, y - padding, w, h, width, height)
        if bounds is not None:
            return bounds

        if self._portrait_faces is None:
            self._portrait_faces = self._cascade("frontalface_alt")
        padding = round(0.23 * edge)
        for cascade, pixels in ((self._close_faces, enhanced), (self._close_faces, gray),
                                (self._portrait_faces, gray)):
            padded = cv2.copyMakeBorder(pixels, padding, padding, padding, padding, cv2.BORDER_REPLICATE)
            faces = cascade.detectMultiScale(padded, scaleFactor=1.10, minNeighbors=3, minSize=(46, 46))
            if len(faces) > 1:
                raise ImageInputError(MULTIPLE_FACES)
            if len(faces) == 1:
                x, y, w, h = map(int, faces[0])
                candidate = normalized_bounds(x - padding, y - padding, w, h, width, height)
                if min(candidate[2:]) >= 0.60:
                    return candidate
        return None

    def _find_eyes(self, gray, x, y, w, h):
        left, top = max(x, 0), max(y, 0)
        upper_face = gray[top:y + round(h * 0.63), left:x + w]
        if min(upper_face.shape) < 18:
            return None
        min_eye = max(9, round(w * 0.10))
        matches = self.eyes.detectMultiScale(upper_face, scaleFactor=1.10, minNeighbors=3,
                                            minSize=(min_eye, min_eye))
        points = [(left + a + c / 2, top + b + d / 2) for a, b, c, d in matches]
        pairs = [(a, b) for a in points for b in points
                 if a[0] < x + w / 2 < b[0] and 0.28 * w < b[0] - a[0] < 0.66 * w
                 and abs(a[1] - b[1]) < 0.24 * h
                 and min(a[1], b[1]) > y + 0.13 * h]
        return min(pairs, key=lambda pair: abs(pair[0][0] - (x + 0.28 * w))
                   + abs(pair[1][0] - (x + 0.72 * w))
                   + abs((pair[0][1] + pair[1][1]) / 2 - (y + 0.34 * h)), default=None)


class ExpressionAnalyzer:
    def __init__(self, model_path: Path = DEFAULT_CAPTURE_MODEL, aligned_model_path: Path = DEFAULT_ALIGNED_MODEL):
        payload = load_model(model_path)
        policy = payload.get("suggestion_policy")
        margin = policy.get("minimum_margin") if isinstance(policy, dict) else None
        if (payload["classes"] != list(CLASSES) or payload["algorithm"] != RBF_ALGORITHM
                or not isinstance(margin, (int, float)) or not math.isfinite(margin)):
            raise ValueError("Fotoğraf ve kamera için eşik içeren yedi sınıflı RBF modeli gerekli.")
        self.detector = FaceDetector()
        self.estimator = payload["estimator"]
        self.config = payload["feature_config"]
        self.descriptor = make_descriptor(self.config)
        self.minimum_margin = margin
        self.aligned_model_path = aligned_model_path

    def predict(self, image: Image.Image, *, prefer_aligned: bool = False, on_face=None) -> Expression:
        face, bounds = self.detector.extract(image)
        if on_face is not None:
            on_face(bounds)
        # Small square uploads already filled by a face match the aligned
        # model's input. Cropping them again can remove useful expression detail.
        if (prefer_aligned and max(image.size) <= 128 and 0.8 <= image.width / image.height <= 1.25
                and min(bounds[2:]) >= 0.80 and self.aligned_model_path.is_file()):
            return self._predict_portrait(image, bounds)
        features = extract_image_features(face, self.descriptor, config=self.config)
        first, second, margin = rank_expressions(self.estimator, features)
        return Expression(first, margin < self.minimum_margin, bounds, second_label=second)

    def predict_photo(self, image: Image.Image, *, prefer_aligned: bool = True, on_face=None) -> Expression:
        try:
            return self.predict(image, prefer_aligned=prefer_aligned, on_face=on_face)
        except FaceNotFound:
            bounds = self.detector.find_close_portrait(image)
            if bounds is None:
                raise

        if on_face is not None:
            on_face(bounds)
        return self._predict_portrait(image, bounds)

    def predict_region(self, image: Image.Image, bounds: tuple[float, float, float, float], *, on_face=None) -> Expression:
        x, y, w, h = bounds
        width, height = image.size
        if not (0 <= x < x + w <= 1.000001 and 0 <= y < y + h <= 1.000001):
            raise ImageInputError("Yüz alanı fotoğrafın içinde olmalı.")
        box = (round(x * width), round(y * height), round((x + w) * width), round((y + h) * height))
        if min(box[2] - box[0], box[3] - box[1]) < 48:
            raise ImageInputError("Yüzün tamamını kapsayan daha büyük bir alan seçin.")
        if on_face is not None:
            on_face(bounds)
        return self._predict_portrait(image.crop(box), bounds)

    def _predict_portrait(self, image, bounds):
        try:
            payload = load_model(self.aligned_model_path)
        except FileNotFoundError:
            estimator, config = self.estimator, self.config
        else:
            estimator, config = payload["estimator"], payload["feature_config"]
        features = extract_image_features(image, config=config)
        first, second, _ = rank_expressions(estimator, features)
        return Expression(first, True, bounds, close_portrait=True, second_label=second)

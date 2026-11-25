"""Background desktop camera and image analysis jobs."""

from pathlib import Path
from pickle import UnpicklingError
from queue import Empty, Full, Queue
import sys
from time import monotonic

import cv2
from PIL import Image
from PySide6.QtCore import QThread, Signal

from homtech.demo_examples import DemoExample
from homtech.ml.predict import ExpressionAnalyzer, FaceNotFound, ImageInputError, prepare_photo, read_photo


MODEL_MISSING = "Model dosyası bulunamadı. Camera-rbf eğitim çıktısını kontrol edin."
ANALYSIS_ERRORS = (OSError, ValueError, EOFError, RuntimeError, UnpicklingError, cv2.error)


def camera_photo(frame):
    return prepare_photo(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))


class CameraStream(QThread):
    frame_ready = Signal(object, float)
    failed = Signal(str)

    def run(self):
        camera = None
        try:
            backends = (cv2.CAP_DSHOW, cv2.CAP_MSMF) if sys.platform == "win32" else (cv2.CAP_ANY,)
            for backend in backends:
                if self.isInterruptionRequested():
                    return
                camera = cv2.VideoCapture(0, backend)
                if camera.isOpened():
                    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    if self._stream(camera):
                        return
                camera.release()
                camera = None
            if not self.isInterruptionRequested():
                self.failed.emit("Kamera açılamadı. Windows kamera izinlerini ve bağlantıyı kontrol edin.")
        except cv2.error:
            if not self.isInterruptionRequested():
                self.failed.emit("Kamera bağlantısında hata oluştu.")
        finally:
            if camera is not None:
                camera.release()

    def _stream(self, camera):
        delivered = False
        missed = 0
        while not self.isInterruptionRequested():
            ok, frame = camera.read()
            if self.isInterruptionRequested():
                return True
            if ok and frame is not None and frame.size:
                self.frame_ready.emit(frame, monotonic())
                delivered = True
                missed = 0
            else:
                missed += 1
                if missed == 10:
                    if delivered:
                        self.failed.emit("Kamera görüntüsü kesildi. Kamerayı yeniden açabilirsiniz.")
                    return delivered
            self.msleep(60)
        return True


class AnalyzeImage(QThread):
    image_ready = Signal(object)
    face_ready = Signal(object)
    prediction_ready = Signal(object)
    failed = Signal(str)
    face_not_found = Signal(str)

    def __init__(self, source, model_path: Path, parent=None, *, region=None):
        super().__init__(parent)
        self.source = source
        self.model_path = model_path
        self.region = region

    def run(self):
        try:
            if isinstance(self.source, Image.Image):
                image = self.source
            elif isinstance(self.source, DemoExample):
                image = self.source.read()
            elif isinstance(self.source, Path):
                image = read_photo(self.source)
            else:
                image = camera_photo(self.source)
            self.image_ready.emit(image)
            analyzer = ExpressionAnalyzer(self.model_path)
            if self.region is None:
                result = analyzer.predict_photo(
                    image, prefer_aligned=isinstance(self.source, Path), on_face=self.face_ready.emit)
            else:
                result = analyzer.predict_region(image, self.region, on_face=self.face_ready.emit)
            self.prediction_ready.emit(result)
        except FaceNotFound as exc:
            self.face_not_found.emit(str(exc))
        except ImageInputError as exc:
            self.failed.emit(str(exc))
        except FileNotFoundError:
            self.failed.emit(MODEL_MISSING)
        except ANALYSIS_ERRORS:
            self.failed.emit("İfade modeli yüklenemedi veya fotoğraf analiz edilemedi.")


class LiveAnalysis(QThread):
    prediction_ready = Signal(object, float)
    face_unavailable = Signal(str, float)
    failed = Signal(str)
    maximum_frame_age = 1.5

    def __init__(self, model_path: Path, parent=None):
        super().__init__(parent)
        self.model_path = model_path
        self._frames = Queue(maxsize=1)

    def submit(self, frame, captured_at: float):
        try:
            self._frames.put_nowait((frame, captured_at))
        except Full:
            try:
                self._frames.get_nowait()
            except Empty:
                pass
            self._frames.put_nowait((frame, captured_at))

    def run(self):
        try:
            analyzer = ExpressionAnalyzer(self.model_path)
            while not self.isInterruptionRequested():
                try:
                    frame, captured_at = self._frames.get(timeout=0.1)
                except Empty:
                    continue
                if self.isInterruptionRequested():
                    return
                if monotonic() - captured_at > self.maximum_frame_age:
                    continue
                try:
                    result = analyzer.predict(camera_photo(frame))
                except ImageInputError as exc:
                    self.face_unavailable.emit(str(exc), captured_at)
                else:
                    self.prediction_ready.emit(result, captured_at)
        except FileNotFoundError:
            self.failed.emit(MODEL_MISSING)
        except ANALYSIS_ERRORS:
            self.failed.emit("Canlı ifade analizi durdu. Kamera karesini çekerek tekrar deneyebilirsiniz.")

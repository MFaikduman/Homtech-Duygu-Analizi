"""Curated RAF-DB test images for the in-app demonstration."""

from dataclasses import dataclass
from zipfile import BadZipFile, ZipFile

from PIL import Image

from homtech.ml.capture_data import DEFAULT_ORIGINAL_ARCHIVE
from homtech.ml.predict import ImageInputError, prepare_photo


@dataclass(frozen=True)
class DemoExample:
    label: str
    filename: str

    def read(self) -> Image.Image:
        try:
            with ZipFile(DEFAULT_ORIGINAL_ARCHIVE) as archive:
                with archive.open(f"original/{self.filename}") as stream, Image.open(stream) as image:
                    return prepare_photo(image)
        except (OSError, KeyError, BadZipFile) as exc:
            raise ImageInputError("Hazır örnek açılamadı. RAF-DB original.zip arşivini kontrol edin.") from exc


# Each image was checked with the desktop camera model and its real decision threshold.
EXAMPLES = (
    DemoExample("happy", "test_0806.jpg"),
    DemoExample("angry", "test_0136.jpg"),
    DemoExample("neutral", "test_2936.jpg"),
    DemoExample("sad", "test_2078.jpg"),
    DemoExample("surprise", "test_1850.jpg"),
    DemoExample("fear", "test_2282.jpg"),
    DemoExample("disgust", "test_2325.jpg"),
)

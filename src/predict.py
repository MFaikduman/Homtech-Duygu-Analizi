"""Tahmin ve akıllı ev modu önerisi için giriş noktası."""

import argparse
import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from src.config import EMOTION_LABELS, IMAGE_SIZE, MODEL_PATH
from src.image_preprocessing import adapt_to_fer_style_rgb, build_tta_variants
from src.smart_home import SmartHomeContext, build_smart_home_plan
from tensorflow import keras


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tek bir görselden duygu tahmini yapar."
    )
    parser.add_argument(
        "--image",
        required=True,
        help="Tahmin yapılacak görselin dosya yolu",
    )
    parser.add_argument(
        "--use-full-image",
        action="store_true",
        help="Yüz algılama yerine tüm görseli kullan",
    )
    parser.add_argument(
        "--time-of-day",
        choices=["morning", "day", "evening", "night"],
        default="evening",
        help="Akıllı ev karar motoru için zaman bağlamı",
    )
    parser.add_argument(
        "--occupancy",
        choices=["alone", "family", "guests"],
        default="alone",
        help="Evdeki kişi durumu",
    )
    parser.add_argument(
        "--quiet-hours",
        action="store_true",
        help="Sessiz saatler aktifse ortam önerilerini yumuşat",
    )
    return parser.parse_args()


def load_image_array(image_array: np.ndarray) -> np.ndarray:
    image_array = cv2.resize(image_array, IMAGE_SIZE)
    image_array = adapt_to_fer_style_rgb(image_array)
    image_array = image_array.astype(np.float32)
    image_array = np.expand_dims(image_array, axis=0)
    return image_array


def detect_largest_face(gray_image: np.ndarray) -> tuple[int, int, int, int] | None:
    cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(str(cascade_path))

    faces = face_cascade.detectMultiScale(
        gray_image,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
    )

    if len(faces) == 0:
        return None

    x, y, w, h = max(faces, key=lambda face: face[2] * face[3])
    return int(x), int(y), int(w), int(h)


def prepare_rgb_image(rgb_image: np.ndarray, use_full_image: bool) -> tuple[np.ndarray, str]:
    gray_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)

    if use_full_image:
        return load_image_array(rgb_image), "tüm görsel kullanıldı"

    face_box = detect_largest_face(gray_image)
    if face_box is None:
        return load_image_array(rgb_image), "yüz bulunamadı, tüm görsel kullanıldı"

    x, y, w, h = face_box
    rgb_face_region = rgb_image[y : y + h, x : x + w]

    return load_image_array(rgb_face_region), "en büyük yüz bölgesi kullanıldı"


def prepare_image(image_path: Path, use_full_image: bool) -> tuple[np.ndarray, str]:
    try:
        rgb_image = np.array(Image.open(image_path).convert("RGB"))
    except Exception as exc:
        raise ValueError(f"Görsel okunamadı: {image_path}") from exc
    return prepare_rgb_image(rgb_image, use_full_image)


def prepare_image_bytes(image_bytes: bytes, use_full_image: bool) -> tuple[np.ndarray, str]:
    try:
        rgb_image = np.array(Image.open(io.BytesIO(image_bytes)).convert("RGB"))
    except Exception as exc:
        raise ValueError("Görsel verisi okunamadı") from exc
    return prepare_rgb_image(rgb_image, use_full_image)


def load_prediction_model(model_path: Path = MODEL_PATH) -> keras.Model:
    if not model_path.exists():
        raise FileNotFoundError(
            f"Eğitilmiş model bulunamadı: {model_path}. Önce python -m src.train çalıştır."
        )
    return keras.models.load_model(model_path)


def run_prediction(
    model,
    image_array,
    preprocessing_note: str,
    context: SmartHomeContext,
):
    tta_batch = build_tta_variants(image_array[0])
    probabilities = model.predict(tta_batch, verbose=0).mean(axis=0)
    predicted_index = int(np.argmax(probabilities))
    predicted_emotion = EMOTION_LABELS[predicted_index]
    confidence = float(probabilities[predicted_index])
    smart_home_plan = build_smart_home_plan(
        predicted_emotion,
        confidence,
        context,
    )
    probability_map = {
        label: float(probability)
        for label, probability in zip(EMOTION_LABELS, probabilities)
    }
    return {
        "predicted_emotion": predicted_emotion,
        "confidence": confidence,
        "preprocessing_note": preprocessing_note,
        "probabilities": probability_map,
        "smart_home_plan": smart_home_plan,
    }


def predict_image_path(
    image_path: Path,
    context: SmartHomeContext,
    use_full_image: bool = False,
    model=None,
):
    active_model = model or load_prediction_model()
    image_array, preprocessing_note = prepare_image(image_path, use_full_image)
    return run_prediction(active_model, image_array, preprocessing_note, context)


def predict_image_bytes(
    image_bytes: bytes,
    context: SmartHomeContext,
    use_full_image: bool = False,
    model=None,
):
    active_model = model or load_prediction_model()
    image_array, preprocessing_note = prepare_image_bytes(image_bytes, use_full_image)
    return run_prediction(active_model, image_array, preprocessing_note, context)


def print_smart_home_plan(plan) -> None:
    print("\nAkıllı ev aksiyon planı:")
    print(f"- Otomasyon durumu: {plan.automation_state}")
    print(f"- Önerilen HOMTECH modu: {plan.suggested_mode}")
    print(f"- Aydınlatma sahnesi: {plan.lighting_scene}")
    print(f"- Parlaklık: %{plan.brightness_percent}")
    print(f"- Sıcaklık: {plan.temperature_celsius}C")
    print(f"- Müzik: {plan.music_scene}")
    print(f"- Perde konumu: {plan.blinds_position}")
    print(f"- Bildirim politikası: {plan.notification_policy}")
    print(f"- Özet: {plan.summary}")


def main() -> None:
    args = parse_args()
    image_path = Path(args.image)

    if not image_path.exists():
        raise FileNotFoundError(f"Görsel bulunamadı: {image_path}")

    context = SmartHomeContext(
        time_of_day=args.time_of_day,
        occupancy=args.occupancy,
        quiet_hours=args.quiet_hours,
    )
    result = predict_image_path(
        image_path,
        context,
        use_full_image=args.use_full_image,
    )
    smart_home_plan = result["smart_home_plan"]

    print(f"Görsel: {image_path}")
    print(f"Ön işleme notu: {result['preprocessing_note']}")
    print(f"Tahmin edilen duygu: {result['predicted_emotion']}")
    print(f"Güven skoru: {result['confidence']:.4f}")
    print(f"Bağlam: zaman={args.time_of_day}, doluluk={args.occupancy}, sessiz_saat={args.quiet_hours}")
    print_smart_home_plan(smart_home_plan)
    print("\nSınıf olasılıkları:")

    for label, probability in result["probabilities"].items():
        print(f"- {label}: {probability:.4f}")


if __name__ == "__main__":
    main()

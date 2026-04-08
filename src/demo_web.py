"""HOMTECH akilli ev sistemi icin yerel web demosu."""

import argparse
import base64
import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from src.config import EMOTION_LABELS, MODEL_PATH
from src.predict import load_prediction_model, predict_image_bytes
from src.smart_home import SmartHomeContext, build_smart_home_plan


ASSETS_DIR = Path(__file__).resolve().parent / "web_demo"


def parse_args():
    parser = argparse.ArgumentParser(
        description="HOMTECH akilli ev sistemi icin demo arayuzunu baslatir."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Sunucu adresi")
    parser.add_argument("--port", type=int, default=8000, help="Sunucu portu")
    return parser.parse_args()


def build_context(payload: dict) -> SmartHomeContext:
    return SmartHomeContext(
        time_of_day=payload.get("time_of_day", "evening"),
        occupancy=payload.get("occupancy", "alone"),
        quiet_hours=bool(payload.get("quiet_hours", False)),
    )


def plan_to_dict(plan) -> dict:
    return {
        "emotion": plan.emotion,
        "confidence": round(plan.confidence, 4),
        "suggested_mode": plan.suggested_mode,
        "automation_state": plan.automation_state,
        "lighting_scene": plan.lighting_scene,
        "brightness_percent": plan.brightness_percent,
        "temperature_celsius": plan.temperature_celsius,
        "music_scene": plan.music_scene,
        "blinds_position": plan.blinds_position,
        "notification_policy": plan.notification_policy,
        "summary": plan.summary,
    }


def decode_image_payload(image_data: str) -> bytes:
    if not image_data:
        raise ValueError("Gorsel verisi eksik")

    encoded_part = image_data.split(",", 1)[1] if "," in image_data else image_data
    try:
        return base64.b64decode(encoded_part)
    except Exception as exc:
        raise ValueError("Gorsel verisi cozulurken hata olustu") from exc


class DemoRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, model=None, **kwargs):
        self.model = model
        super().__init__(*args, directory=str(ASSETS_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/api/health":
            payload = {
                "model_ready": self.model is not None,
                "model_path": str(MODEL_PATH),
                "supported_emotions": EMOTION_LABELS,
            }
            return self.send_json(payload)
        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/scenario":
            return self.handle_scenario()
        if self.path == "/api/predict":
            return self.handle_predict()
        self.send_error(HTTPStatus.NOT_FOUND, "Istek bulunamadi")

    def handle_scenario(self):
        try:
            payload = self.read_json()
            emotion = payload["emotion"]
            confidence = float(payload.get("confidence", 0.75))
            context = build_context(payload)
            plan = build_smart_home_plan(emotion, confidence, context)
        except KeyError as exc:
            return self.send_json({"error": f"Eksik alan: {exc.args[0]}"}, status=400)
        except Exception as exc:
            return self.send_json({"error": str(exc)}, status=400)

        return self.send_json(
            {
                "source": "scenario",
                "plan": plan_to_dict(plan),
                "probabilities": {},
                "preprocessing_note": "Senaryo modu: el ile secilen duygu kullanildi.",
            }
        )

    def handle_predict(self):
        try:
            payload = self.read_json()
            image_bytes = decode_image_payload(payload.get("image_data", ""))
            context = build_context(payload)
            result = predict_image_bytes(
                image_bytes,
                context,
                use_full_image=bool(payload.get("use_full_image", False)),
                model=self.model,
            )
        except Exception as exc:
            return self.send_json({"error": str(exc)}, status=400)

        return self.send_json(
            {
                "source": "prediction",
                "plan": plan_to_dict(result["smart_home_plan"]),
                "probabilities": result["probabilities"],
                "preprocessing_note": result["preprocessing_note"],
            }
        )

    def read_json(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        return json.loads(raw_body.decode("utf-8"))

    def send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def create_handler(model):
    def handler(*args, **kwargs):
        return DemoRequestHandler(*args, model=model, **kwargs)

    return handler


def main() -> None:
    args = parse_args()
    model = load_prediction_model()
    server = ThreadingHTTPServer((args.host, args.port), create_handler(model))
    url = f"http://{args.host}:{args.port}"
    print("HOMTECH demo arayuzu hazir.")
    print(f"Tarayicida ac: {url}")
    print("Durdurmak icin Ctrl+C kullan.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSunucu kapatiliyor...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

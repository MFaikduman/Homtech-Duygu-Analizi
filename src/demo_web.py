"""HOMTECH akilli ev sistemi icin yerel web demosu."""

import argparse
import base64
import json
import logging
import mimetypes
import os
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from src.config import ARTIFACTS_DIR, EMOTION_LABELS, MODEL_PATH, PROJECT_ROOT
from src.presentation_data import build_presentation_payload
from src.smart_home import SmartHomeContext, build_smart_home_plan


os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

ASSETS_DIR = PROJECT_ROOT / "src" / "web_demo"
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
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
        return base64.b64decode(encoded_part, validate=True)
    except Exception as exc:
        raise ValueError("Gorsel verisi cozulurken hata olustu") from exc


class PredictionRuntime:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._load_started = False
        self._predict_image_bytes = None
        self.model = None
        self.model_error = None
        self.model_loading = False

    def start_background_load(self) -> None:
        with self._lock:
            if self._load_started or self.model_loading or self.model is not None:
                return
            self._load_started = True
            self.model_loading = True
            self.model_error = None

        worker = threading.Thread(
            target=self._load_prediction_model,
            name="prediction-model-loader",
            daemon=True,
        )
        worker.start()

    def _load_prediction_model(self) -> None:
        loaded_model = None
        loaded_predict_image_bytes = None
        error_message = None

        try:
            from src.predict import load_prediction_model, predict_image_bytes

            loaded_model = load_prediction_model()
            loaded_predict_image_bytes = predict_image_bytes
        except Exception as exc:
            error_message = str(exc)
            LOGGER.warning("Tahmin modeli yuklenemedi: %s", error_message)

        with self._lock:
            self.model = loaded_model
            self.model_error = error_message
            self.model_loading = False
            self._load_started = loaded_model is not None
            if loaded_predict_image_bytes is not None:
                self._predict_image_bytes = loaded_predict_image_bytes

    def get_status(self) -> dict:
        with self._lock:
            return {
                "model_ready": self.model is not None,
                "model_loading": self.model_loading,
                "model_error": self.model_error,
            }

    def predict_image_bytes(
        self,
        image_bytes: bytes,
        context: SmartHomeContext,
        use_full_image: bool = False,
    ):
        with self._lock:
            model = self.model
            model_loading = self.model_loading
            model_error = self.model_error
            predict_image_bytes = self._predict_image_bytes

        if model is None:
            if not model_loading:
                self.start_background_load()
                raise RuntimeError("Tahmin modeli baslatildi. Birkac saniye sonra tekrar dene.")
            raise RuntimeError("Tahmin modeli halen yukleniyor. Birkac saniye sonra tekrar dene.")

        if predict_image_bytes is None:
            raise RuntimeError("Tahmin modulu hazir degil.")

        return predict_image_bytes(
            image_bytes,
            context,
            use_full_image=use_full_image,
            model=model,
        )


class DemoRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, prediction_runtime=None, **kwargs):
        self.prediction_runtime = prediction_runtime
        super().__init__(*args, directory=str(ASSETS_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/presentation":
            self.path = "/presentation.html"
            return super().do_GET()
        if self.path.startswith("/artifacts/"):
            return self.serve_artifact()
        if self.path == "/api/health":
            runtime_status = self.prediction_runtime.get_status()
            payload = {
                "scenario_ready": True,
                "model_path": str(MODEL_PATH),
                "supported_emotions": EMOTION_LABELS,
                **runtime_status,
            }
            return self.send_json(payload)
        if self.path == "/api/presentation-data":
            return self.send_json(build_presentation_payload())
        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/scenario":
            return self.handle_scenario()
        if self.path == "/api/predict":
            return self.handle_predict()
        if self.path == "/api/warmup-model":
            return self.handle_warmup_model()
        self.send_error(HTTPStatus.NOT_FOUND, "Istek bulunamadi")

    def guess_type(self, path):
        content_type = super().guess_type(path)
        utf8_types = {
            "text/html",
            "text/css",
            "application/javascript",
            "text/javascript",
        }
        if content_type in utf8_types:
            return f"{content_type}; charset=utf-8"
        return content_type

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
            result = self.prediction_runtime.predict_image_bytes(
                image_bytes,
                context,
                use_full_image=bool(payload.get("use_full_image", False)),
            )
        except RuntimeError as exc:
            return self.send_json({"error": str(exc)}, status=503)
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

    def handle_warmup_model(self):
        self.prediction_runtime.start_background_load()
        return self.send_json(self.prediction_runtime.get_status())

    def read_json(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        return json.loads(raw_body.decode("utf-8")) if raw_body else {}

    def serve_artifact(self):
        artifact_name = self.path.removeprefix("/artifacts/")
        target_path = (ARTIFACTS_DIR / artifact_name).resolve()
        artifacts_root = ARTIFACTS_DIR.resolve()

        if artifacts_root not in target_path.parents and target_path != artifacts_root:
            self.send_error(HTTPStatus.FORBIDDEN, "Erisim engellendi")
            return

        if not target_path.exists() or not target_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Dosya bulunamadi")
            return

        content_type, _ = mimetypes.guess_type(target_path.name)
        body = target_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def create_handler(prediction_runtime: PredictionRuntime):
    def handler(*args, **kwargs):
        return DemoRequestHandler(
            *args,
            prediction_runtime=prediction_runtime,
            **kwargs,
        )

    return handler


def create_demo_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    prediction_runtime = PredictionRuntime()
    return ThreadingHTTPServer(
        (host, port),
        create_handler(prediction_runtime),
    )


def start_demo_server(host: str = "127.0.0.1", port: int = 0) -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    server = create_demo_server(host, port)
    thread = threading.Thread(
        target=server.serve_forever,
        name="homtech-demo-server",
        daemon=True,
    )
    thread.start()
    server_host, server_port = server.server_address[:2]
    return server, thread, f"http://{server_host}:{server_port}"


def stop_demo_server(server: ThreadingHTTPServer | None, thread: threading.Thread | None = None) -> None:
    if server is None:
        return
    server.shutdown()
    server.server_close()
    if thread is not None and thread.is_alive():
        thread.join(timeout=5)


def main() -> None:
    args = parse_args()
    server = create_demo_server(args.host, args.port)
    url = f"http://{args.host}:{args.port}"
    print("HOMTECH demo arayuzu hazir.")
    print("Web arayuzu hemen acilabilir.")
    print("Analiz modeli sadece istendiginde yuklenir.")
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

import json
import unittest
from urllib.request import urlopen

from src.config import EMOTION_LABELS
from src.demo_web import start_demo_server, stop_demo_server
from src.smart_home import SmartHomeContext, build_smart_home_plan


class SmartHomeSmokeTests(unittest.TestCase):
    def test_build_smart_home_plan(self):
        plan = build_smart_home_plan(
            "happy",
            0.91,
            SmartHomeContext(time_of_day="evening", occupancy="alone"),
        )

        self.assertEqual(plan.emotion, "happy")
        self.assertEqual(plan.suggested_mode, "enerjik mod")
        self.assertEqual(plan.automation_state, "otomatik uygulanabilir")


class DemoServerSmokeTests(unittest.TestCase):
    def test_health_endpoint(self):
        server = None
        thread = None

        try:
            server, thread, url = start_demo_server(host="127.0.0.1", port=0)
            with urlopen(f"{url}/api/health", timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))

            self.assertTrue(payload["scenario_ready"])
            self.assertEqual(payload["supported_emotions"], EMOTION_LABELS)
            self.assertIn("model_ready", payload)
        finally:
            stop_demo_server(server, thread)


if __name__ == "__main__":
    unittest.main()

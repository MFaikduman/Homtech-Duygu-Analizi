"""Duygu bilgisinden akilli ev plani ureten demo araci."""

import argparse

from src.config import EMOTION_LABELS
from src.smart_home import SmartHomeContext, build_smart_home_plan


def parse_args():
    parser = argparse.ArgumentParser(
        description="Duyguya gore akilli ev aksiyon plani uretir."
    )
    parser.add_argument(
        "--emotion",
        required=True,
        choices=EMOTION_LABELS,
        help="Senaryo uretilecek duygu etiketi",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.75,
        help="Tahmin guven skoru",
    )
    parser.add_argument(
        "--time-of-day",
        choices=["morning", "day", "evening", "night"],
        default="evening",
        help="Zaman baglami",
    )
    parser.add_argument(
        "--occupancy",
        choices=["alone", "family", "guests"],
        default="alone",
        help="Ev doluluk durumu",
    )
    parser.add_argument(
        "--quiet-hours",
        action="store_true",
        help="Sessiz saat ayarini ac",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    context = SmartHomeContext(
        time_of_day=args.time_of_day,
        occupancy=args.occupancy,
        quiet_hours=args.quiet_hours,
    )
    plan = build_smart_home_plan(args.emotion, args.confidence, context)

    print(f"Duygu: {plan.emotion}")
    print(f"Guven skoru: {plan.confidence:.2f}")
    print(f"Otomasyon durumu: {plan.automation_state}")
    print(f"HOMTECH modu: {plan.suggested_mode}")
    print(f"Aydinlatma: {plan.lighting_scene}")
    print(f"Parlaklik: %{plan.brightness_percent}")
    print(f"Sicaklik: {plan.temperature_celsius}C")
    print(f"Muzik: {plan.music_scene}")
    print(f"Perde: {plan.blinds_position}")
    print(f"Bildirimler: {plan.notification_policy}")
    print(f"Ozet: {plan.summary}")


if __name__ == "__main__":
    main()

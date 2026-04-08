"""Duygu tahminini akilli ev aksiyonlarina ceviren karar motoru."""

from dataclasses import dataclass

from src.config import HOME_MODE_MAP


AUTO_APPLY_THRESHOLD = 0.6


@dataclass(frozen=True)
class SmartHomeContext:
    time_of_day: str = "evening"
    occupancy: str = "alone"
    quiet_hours: bool = False


@dataclass(frozen=True)
class SmartHomePlan:
    emotion: str
    confidence: float
    suggested_mode: str
    automation_state: str
    lighting_scene: str
    brightness_percent: int
    temperature_celsius: int
    music_scene: str
    blinds_position: str
    notification_policy: str
    summary: str


BASE_ACTIONS = {
    "angry": {
        "lighting_scene": "sicak ve yumusak aydinlatma",
        "brightness_percent": 35,
        "temperature_celsius": 22,
        "music_scene": "sakin enstrumantal oynatma listesi",
        "blinds_position": "yari kapali",
        "notification_policy": "yalnizca onemli bildirimler",
    },
    "disgust": {
        "lighting_scene": "dogal beyaz aydinlatma",
        "brightness_percent": 50,
        "temperature_celsius": 22,
        "music_scene": "muzik kapali",
        "blinds_position": "acik",
        "notification_policy": "standart bildirim duzeni",
    },
    "fear": {
        "lighting_scene": "guven veren sicak aydinlatma",
        "brightness_percent": 45,
        "temperature_celsius": 23,
        "music_scene": "dusuk sesli rahatlatici oynatma listesi",
        "blinds_position": "kapali",
        "notification_policy": "rahatsiz etmeyen mod",
    },
    "happy": {
        "lighting_scene": "canli ve parlak aydinlatma",
        "brightness_percent": 75,
        "temperature_celsius": 21,
        "music_scene": "enerjik oynatma listesi",
        "blinds_position": "tam acik",
        "notification_policy": "standart bildirim duzeni",
    },
    "sad": {
        "lighting_scene": "sicak ve rahatlatan aydinlatma",
        "brightness_percent": 40,
        "temperature_celsius": 23,
        "music_scene": "yumusak rahatlatici oynatma listesi",
        "blinds_position": "yari kapali",
        "notification_policy": "gereksiz bildirimleri ertele",
    },
    "surprise": {
        "lighting_scene": "dengeleyici beyaz aydinlatma",
        "brightness_percent": 60,
        "temperature_celsius": 22,
        "music_scene": "hafif tempolu oynatma listesi",
        "blinds_position": "acik",
        "notification_policy": "standart bildirim duzeni",
    },
    "neutral": {
        "lighting_scene": "odak odakli beyaz aydinlatma",
        "brightness_percent": 65,
        "temperature_celsius": 21,
        "music_scene": "odak modu oynatma listesi",
        "blinds_position": "acik",
        "notification_policy": "yalnizca oncelikli bildirimler",
    },
}


def _apply_time_adjustments(plan: dict, time_of_day: str) -> None:
    if time_of_day == "morning":
        plan["brightness_percent"] = min(plan["brightness_percent"] + 10, 100)
        plan["blinds_position"] = "tam acik"
    elif time_of_day == "night":
        plan["brightness_percent"] = max(plan["brightness_percent"] - 20, 20)
        plan["notification_policy"] = "sessiz gece modu"


def _apply_occupancy_adjustments(plan: dict, occupancy: str) -> None:
    if occupancy == "family":
        plan["music_scene"] = f"aile ortamina uygun {plan['music_scene']}"
    elif occupancy == "guests":
        plan["lighting_scene"] = "misafir dostu " + plan["lighting_scene"]
        plan["notification_policy"] = "gizli bildirim gostergesi"


def _apply_quiet_hours_adjustments(plan: dict, quiet_hours: bool) -> None:
    if quiet_hours:
        plan["music_scene"] = "muzik kapali"
        plan["brightness_percent"] = max(plan["brightness_percent"] - 15, 20)
        plan["notification_policy"] = "sessiz mod"


def build_smart_home_plan(
    emotion: str,
    confidence: float,
    context: SmartHomeContext,
) -> SmartHomePlan:
    if emotion not in BASE_ACTIONS:
        raise ValueError(f"Desteklenmeyen duygu: {emotion}")

    plan = dict(BASE_ACTIONS[emotion])
    _apply_time_adjustments(plan, context.time_of_day)
    _apply_occupancy_adjustments(plan, context.occupancy)
    _apply_quiet_hours_adjustments(plan, context.quiet_hours)

    automation_state = (
        "otomatik uygulanabilir"
        if confidence >= AUTO_APPLY_THRESHOLD
        else "kullanici onayi gerekli"
    )
    suggested_mode = HOME_MODE_MAP[emotion]
    summary = (
        f"{emotion} duygusu icin {suggested_mode} onerildi. "
        f"Ortam: {plan['lighting_scene']}, muzik: {plan['music_scene']}."
    )

    return SmartHomePlan(
        emotion=emotion,
        confidence=confidence,
        suggested_mode=suggested_mode,
        automation_state=automation_state,
        lighting_scene=plan["lighting_scene"],
        brightness_percent=plan["brightness_percent"],
        temperature_celsius=plan["temperature_celsius"],
        music_scene=plan["music_scene"],
        blinds_position=plan["blinds_position"],
        notification_policy=plan["notification_policy"],
        summary=summary,
    )

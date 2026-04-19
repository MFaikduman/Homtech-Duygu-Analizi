"""HOMTECH demo arayüzünü masaüstü uygulama penceresinde açar."""

from __future__ import annotations

import sys

from src.demo_web import start_demo_server, stop_demo_server


def main() -> None:
    try:
        import webview
    except ImportError as exc:
        raise SystemExit(
            "Masaüstü uygulamayı açmak için önce pywebview kurulmalı. "
            "Şu komutu çalıştır: uv pip install -r requirements-desktop.txt"
        ) from exc

    server = None
    thread = None

    try:
        server, thread, app_url = start_demo_server(host="127.0.0.1", port=0)
        window = webview.create_window(
            "HOMTECH Mood Console",
            app_url,
            width=1480,
            height=920,
            min_size=(1200, 760),
            background_color="#f5f1e8",
        )

        def _shutdown() -> None:
            stop_demo_server(server, thread)

        window.events.closed += _shutdown
        webview.start(gui="edgechromium", debug=False)
    finally:
        stop_demo_server(server, thread)


if __name__ == "__main__":
    sys.exit(main())

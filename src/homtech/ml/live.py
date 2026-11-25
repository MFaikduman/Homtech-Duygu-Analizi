"""Stabilize per-frame expression predictions before displaying them."""

from collections import deque


class LiveConsensus:
    frame_interval = 0.5
    window = 2.0
    minimum_span = 1.0
    minimum_frames = 3

    def __init__(self):
        self._samples: deque[float] = deque()
        self.reset()

    def reset(self):
        self.label: str | None = None
        self._candidate: str | None = None
        self._confirmed_at: float | None = None
        self._samples.clear()

    def observe(self, label: str | None, captured_at: float) -> str | None:
        if label != self._candidate or label is None:
            self._samples.clear()
            self._candidate = label
        if label is not None:
            self._samples.append(captured_at)
            while captured_at - self._samples[0] > self.window:
                self._samples.popleft()
            if (len(self._samples) >= self.minimum_frames
                    and captured_at - self._samples[0] >= self.minimum_span):
                self.label = label
                self._confirmed_at = captured_at
        return self.label

    def expire(self, now: float) -> bool:
        if self._confirmed_at is None or now - self._confirmed_at <= self.window:
            return False
        self.label = None
        self._confirmed_at = None
        return True

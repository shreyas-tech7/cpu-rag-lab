"""A watchdog thread that reads resident memory (VmRSS) and stops runs over the limit."""

from __future__ import annotations

import threading

LIMIT_MB = 2048


class MemoryLimitExceeded(RuntimeError):
    pass


def rss_mb(status_path: str = "/proc/self/status") -> float:
    """Resident set size of this process in MB, read from VmRSS."""
    with open(status_path) as f:
        for line in f:
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024.0
    return 0.0


class MemGuard:
    """Samples VmRSS every `interval` seconds and keeps the peak since the last reset.

    The thread only sets a flag. The run loop calls check() between batches, which
    raises MemoryLimitExceeded so the run ends as failed and the grid moves on.
    """

    def __init__(self, limit_mb: float = LIMIT_MB, interval: float = 0.02, reader=rss_mb):
        self.limit_mb, self.interval, self.reader = limit_mb, interval, reader
        self.peak_mb = 0.0
        self.exceeded = False
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def sample(self) -> float:
        mb = self.reader()
        self.peak_mb = max(self.peak_mb, mb)
        if mb > self.limit_mb:
            self.exceeded = True
        return mb

    def _loop(self) -> None:
        while not self._stop.wait(self.interval):
            self.sample()

    def reset(self) -> None:
        self.peak_mb, self.exceeded = 0.0, False
        self.sample()

    def check(self) -> None:
        self.sample()
        if self.exceeded:
            raise MemoryLimitExceeded(f"peak {self.peak_mb:.0f} MB over {self.limit_mb:.0f} MB")

    def __enter__(self) -> MemGuard:
        self.reset()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
        self.sample()

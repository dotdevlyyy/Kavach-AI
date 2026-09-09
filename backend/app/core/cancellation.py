"""
Kavach AI — Cancellation Registry
In-process asyncio.Event registry keyed by id (task_id or conversation_id).
Stream generators check `.is_set()` between steps to abort early.
"""

from __future__ import annotations

import asyncio


class CancellationRegistry:
    def __init__(self) -> None:
        self._events: dict[str, asyncio.Event] = {}

    def get(self, key: str) -> asyncio.Event:
        ev = self._events.get(key)
        if ev is None:
            ev = asyncio.Event()
            self._events[key] = ev
        return ev

    def cancel(self, key: str) -> bool:
        ev = self._events.get(key)
        if ev is None:
            ev = asyncio.Event()
            self._events[key] = ev
        ev.set()
        return True

    def contains(self, key: str) -> bool:
        return key in self._events

    def clear(self, key: str) -> None:
        self._events.pop(key, None)


registry = CancellationRegistry()

from __future__ import annotations

from abc import ABC, abstractmethod


class Provider(ABC):
    """Interface implemented by every notification provider."""

    @abstractmethod
    def send(self, title: str, message: str) -> None:
        """Send a notification or raise an exception."""


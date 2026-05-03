# src/platforms/base.py

"""
平台客户端基类。
"""

from __future__ import annotations

from abc import ABC
from typing import Any

import httpx

from src.utils.logger import get_logger


class BasePlatformClient(ABC):
    """平台 API 客户端基类"""

    platform_name: str = "base"

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.logger = get_logger(self.platform_name)
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.config.get("timeout", 30),
                follow_redirects=True,
            )
        return self._client

    def close(self):
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

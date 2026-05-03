# src/platforms/video_store.py

"""
微信视频号小店客户端。

注意: 这是框架示例，实际接入需参考微信官方文档:
https://developers.weixin.qq.com/doc/channels/
"""

from __future__ import annotations

import time
from typing import Any

from src.platforms.base import BasePlatformClient


class VideoStoreClient(BasePlatformClient):
    platform_name = "VideoStoreClient"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.app_id = self.config.get("video_store_app_id", "")
        self.app_secret = self.config.get("video_store_app_secret", "")
        self.access_token = self.config.get("video_store_access_token", "")
        self.api_url = self.config.get("video_store_api_url", "https://api.weixin.qq.com")

    def _get_access_token(self) -> str:
        """
        获取/刷新 access_token。

        TODO: 实现 token 缓存与自动刷新
        """
        if self.access_token:
            return self.access_token

        resp = self.client.get(
            f"{self.api_url}/cgi-bin/token",
            params={
                "grant_type": "client_credential",
                "appid": self.app_id,
                "secret": self.app_secret,
            },
        )
        data = resp.json()
        if "access_token" not in data:
            raise RuntimeError(f"获取 access_token 失败: {data}")
        self.access_token = data["access_token"]
        return self.access_token

    def create_product(self, payload: dict) -> dict:
        """
        创建视频号小店商品。

        Args:
            payload: 商品数据（已转换为视频号格式）

        Returns:
            {"success": True, "product_id": "xxx"} 或 {"success": False, "error": "xxx"}

        TODO: 替换为真实 API 调用
        """
        # ── 真实接入时替换此段 ──
        # token = self._get_access_token()
        # resp = self.client.post(
        #     f"{self.api_url}/wxa/business/addproduct",
        #     params={"access_token": token},
        #     json=payload,
        # )
        # data = resp.json()
        # if data.get("errcode", 0) != 0:
        #     return {"success": False, "error": data.get("errmsg", "未知错误")}
        # return {"success": True, "product_id": data["product_id"]}

        # ── Mock（开发调试用）──
        self.logger.info(f"[MOCK] 发布商品至视频号: {payload.get('title', '')[:30]}...")
        mock_product_id = f"vs_{int(time.time())}"
        self.logger.info(f"[MOCK] 发布成功, 商品ID: {mock_product_id}")
        return {"success": True, "product_id": mock_product_id}

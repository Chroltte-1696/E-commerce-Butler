# src/platforms/qianniu.py

"""
千牛/淘宝开放平台客户端。

注意: 这是框架示例，实际接入需参考淘宝开放平台文档:
https://open.taobao.com
"""

from __future__ import annotations

import hashlib
import time
from typing import Any

from src.platforms.base import BasePlatformClient


class QianniuClient(BasePlatformClient):
    platform_name = "QianniuClient"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.app_key = self.config.get("qianniu_app_key", "")
        self.app_secret = self.config.get("qianniu_app_secret", "")
        self.access_token = self.config.get("qianniu_access_token", "")
        self.api_url = self.config.get("qianniu_api_url", "https://eco.taobao.com/router/rest")

    def _sign(self, params: dict) -> str:
        """生成淘宝 API 签名"""
        sorted_params = sorted(params.items())
        sign_str = self.app_secret + "".join(f"{k}{v}" for k, v in sorted_params) + self.app_secret
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

    def _call_api(self, method: str, biz_params: dict) -> dict:
        """
        调用淘宝开放平台 API。

        Args:
            method: API 方法名，如 taobao.item.get
            biz_params: 业务参数

        Returns:
            API 响应数据
        """
        params = {
            "method": method,
            "app_key": self.app_key,
            "session": self.access_token,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "format": "json",
            "v": "2.0",
            "sign_method": "md5",
        }
        # 合并业务参数
        for k, v in biz_params.items():
            params[k] = v

        params["sign"] = self._sign(params)

        self.logger.debug(f"调用 API: {method}")
        resp = self.client.post(self.api_url, data=params)
        resp.raise_for_status()
        data = resp.json()

        # 错误处理
        if "error_response" in data:
            error = data["error_response"]
            raise RuntimeError(
                f"千牛 API 错误 [{error.get('code')}]: {error.get('msg')}"
            )

        return data

    def get_product_detail(self, product_id: str) -> dict:
        """
        获取商品详情。

        Args:
            product_id: 千牛商品 ID

        Returns:
            结构化商品数据（已适配统一 Schema）

        TODO: 替换为真实 API 调用逻辑
        """
        # ── 示例: 真实接入时替换此段 ──
        # raw = self._call_api(
        #     "taobao.item.get",
        #     {
        #         "num_iid": product_id,
        #         "fields": "title,price,nick,desc,pic_url,item_img,sku",
        #     },
        # )
        # return self._normalize(raw)

        # ── Mock 数据（开发调试用）──
        self.logger.info(f"[MOCK] 获取商品详情: {product_id}")
        return {
            "product_id": product_id,
            "title": "法式复古碎花连衣裙女夏季新款收腰显瘦中长款气质裙子",
            "sub_title": "轻奢面料 · 法式浪漫 · 收腰显瘦",
            "description": "优雅法式碎花连衣裙，采用高密度雪纺面料...",
            "selling_points": [
                "法式复古碎花设计，优雅浪漫",
                "收腰剪裁，显瘦不挑身材",
                "高密度雪纺面料，垂坠感好",
                "中长款设计，遮肉显气质",
            ],
            "categories": [
                {"id": "50010850", "name": "女装"},
                {"id": "50010851", "name": "连衣裙"},
            ],
            "price": "168.00",
            "currency": "CNY",
            "skus": [
                {
                    "sku_id": "1001",
                    "spec_values": {"颜色": "碎花白", "尺码": "S"},
                    "price": 168.00,
                    "stock": 50,
                },
                {
                    "sku_id": "1002",
                    "spec_values": {"颜色": "碎花白", "尺码": "M"},
                    "price": 168.00,
                    "stock": 80,
                },
                {
                    "sku_id": "1003",
                    "spec_values": {"颜色": "碎花蓝", "尺码": "S"},
                    "price": 168.00,
                    "stock": 30,
                },
                {
                    "sku_id": "1004",
                    "spec_values": {"颜色": "碎花蓝", "尺码": "M"},
                    "price": 168.00,
                    "stock": 45,
                },
            ],
            "main_images": [
                {"url": "https://example.com/img/main_1.jpg"},
                {"url": "https://example.com/img/main_2.jpg"},
                {"url": "https://example.com/img/main_3.jpg"},
            ],
            "detail_images": [
                {"url": "https://example.com/img/detail_1.jpg"},
                {"url": "https://example.com/img/detail_2.jpg"},
                {"url": "https://example.com/img/detail_3.jpg"},
                {"url": "https://example.com/img/detail_4.jpg"},
                {"url": "https://example.com/img/detail_5.jpg"},
            ],
        }

    def _normalize(self, raw: dict) -> dict:
        """
        将淘宝 API 原始响应转换为统一格式。

        TODO: 根据真实 API 响应结构实现映射
        """
        raise NotImplementedError("请根据实际 API 响应结构实现")

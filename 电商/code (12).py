# src/agents/video_store_publisher.py

"""
视频号上架 Agent —— 执行最终发布并回流商品 ID。

职责:
1. 将转换后的 Product 转为视频号 API 所需的请求格式
2. 调用视频号小店 API 创建商品
3. 回流新商品 ID
"""

from __future__ import annotations

from src.agents.base import AgentResult, BaseAgent
from src.models.product import Platform, Product
from src.platforms.video_store import VideoStoreClient


class VideoStorePublisherAgent(BaseAgent):
    name = "VideoStorePublisherAgent"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.client = VideoStoreClient(config=self.config)

    def execute(self, product: Product, **kwargs) -> AgentResult:
        """发布商品至视频号小店"""

        confirm = kwargs.get("confirm", not self.config.get("require_confirmation", True))

        # ── 构建请求体 ──
        payload = self._build_payload(product)
        product.converted_data = payload

        # ── 人工确认（可选）──
        if not confirm:
            self.logger.info("⏸ 等待人工确认... (传入 confirm=True 跳过)")
            return AgentResult(
                success=True,
                product=product,
                message="预览已生成，等待确认后发布",
                metadata={"preview_payload": payload},
            )

        # ── 调用发布 API ──
        self.logger.info("正在发布至视频号小店...")
        result = self.client.create_product(payload)

        if not result.get("success"):
            raise RuntimeError(f"视频号发布失败: {result.get('error', '未知错误')}")

        product.target_product_id = result["product_id"]
        product.target_platform = Platform.VIDEO_STORE

        return AgentResult(
            success=True,
            product=product,
            message=f"发布成功! 视频号商品ID: {product.target_product_id}",
        )

    def _build_payload(self, product: Product) -> dict:
        """将统一 Product 模型转换为视频号 API 请求格式"""
        return {
            "title": product.title,
            "sub_title": product.sub_title,
            "description": product.description,
            "selling_points": product.selling_points,
            "category_id": (
                product.target_category[-1].id if product.target_category else ""
            ),
            "price": int(product.target_price * 100),  # 视频号价格单位: 分
            "stock": product.total_stock,
            "main_images": [img.url for img in product.main_images],
            "detail_images": [img.url for img in product.detail_images],
            "skus": [
                {
                    "spec_values": sku.spec_values,
                    "price": int(sku.price * 100),
                    "stock": sku.stock,
                }
                for sku in product.skus
            ],
            "free_shipping": product.free_shipping,
        }

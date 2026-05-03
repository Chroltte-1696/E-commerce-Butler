# src/agents/qianniu_parser.py

"""
千牛解析 Agent —— 从淘宝/千牛平台抓取源商品全量信息并结构化。

职责:
1. 调用千牛 API 获取商品详情
2. 解析标题、属性、SKU、尺码表、图片等
3. 输出标准化 Product 模型
"""

from __future__ import annotations

from src.agents.base import AgentResult, BaseAgent
from src.models.product import (
    CategoryNode,
    Platform,
    Product,
    ProductImage,
    ProductSku,
)
from src.platforms.qianniu import QianniuClient


class QianniuParserAgent(BaseAgent):
    name = "QianniuParserAgent"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.client = QianniuClient(config=self.config)

    def execute(self, product: Product, **kwargs) -> AgentResult:
        """抓取千牛商品并结构化"""
        product_id = product.product_id

        # ── 调用平台 API ──
        self.logger.info(f"正在抓取千牛商品: {product_id}")
        raw = self.client.get_product_detail(product_id)

        if not raw:
            raise ValueError(f"千牛商品不存在或无权访问: {product_id}")

        product.raw_data = raw

        # ── 结构化解析 ──
        product.title = raw.get("title", "")
        product.sub_title = raw.get("sub_title", "")
        product.description = raw.get("description", "")
        product.selling_points = raw.get("selling_points", [])
        product.base_price = float(raw.get("price", 0))
        product.currency = raw.get("currency", "CNY")

        # 类目
        product.source_category = [
            CategoryNode(
                id=str(c.get("id", "")),
                name=c.get("name", ""),
                level=i + 1,
            )
            for i, c in enumerate(raw.get("categories", []))
        ]

        # SKU
        product.skus = [
            ProductSku(
                sku_id=str(s.get("sku_id", "")),
                spec_values=s.get("spec_values", {}),
                price=float(s.get("price", 0)),
                original_price=float(s["original_price"]) if s.get("original_price") else None,
                stock=int(s.get("stock", 0)),
                barcode=s.get("barcode", ""),
            )
            for s in raw.get("skus", [])
        ]

        # 图片
        product.main_images = [
            ProductImage(url=img["url"], is_main=(i == 0))
            for i, img in enumerate(raw.get("main_images", []))
        ]
        product.detail_images = [
            ProductImage(url=img["url"])
            for img in raw.get("detail_images", [])
        ]

        return AgentResult(
            success=True,
            product=product,
            message=f"解析完成: {product.title} | SKU={len(product.skus)} | 图片={len(product.main_images) + len(product.detail_images)}",
        )

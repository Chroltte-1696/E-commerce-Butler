# src/models/product.py

"""
统一商品数据模型 —— 跨平台的核心数据契约。

所有平台适配层（千牛、视频号等）的输入输出都必须
转化为这个 Schema，确保 Agent 之间解耦。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Platform(str, Enum):
    QIANNIU = "qianniu"
    VIDEO_STORE = "video_store"


class CategoryNode(BaseModel):
    """平台类目节点"""
    id: str
    name: str
    level: int
    parent_id: Optional[str] = None


class ProductImage(BaseModel):
    """商品图片"""
    url: str
    alt: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    is_main: bool = False
    local_path: Optional[str] = None  # 裁剪后本地路径


class ProductSku(BaseModel):
    """SKU 规格"""
    sku_id: str = ""
    spec_values: dict[str, str] = Field(default_factory=dict)  # e.g. {"颜色": "白色", "尺码": "M"}
    price: float = 0.0
    original_price: Optional[float] = None
    stock: int = 0
    barcode: str = ""


class Product(BaseModel):
    """
    统一商品数据模型。

    这是整个 Pipeline 的数据骨架，从千牛解析到
    视频号发布，所有 Agent 都围绕这个模型读写。
    """
    # ── 基础信息 ──
    product_id: str = ""
    source_platform: Platform = Platform.QIANNIU
    target_platform: Platform = Platform.VIDEO_STORE
    title: str = ""
    sub_title: str = ""

    # ── 类目 ──
    source_category: list[CategoryNode] = Field(default_factory=list)
    target_category: list[CategoryNode] = Field(default_factory=list)

    # ── 描述 ──
    description: str = ""
    selling_points: list[str] = Field(default_factory=list)

    # ── 图片 ──
    main_images: list[ProductImage] = Field(default_factory=list)
    detail_images: list[ProductImage] = Field(default_factory=list)

    # ── SKU ──
    skus: list[ProductSku] = Field(default_factory=list)

    # ── 价格策略 ──
    base_price: float = 0.0
    target_price: float = 0.0
    currency: str = "CNY"

    # ── 运费 ──
    shipping_template_id: str = ""
    free_shipping: bool = True

    # ── 元数据 ──
    raw_data: dict = Field(default_factory=dict)       # 原始平台数据
    converted_data: dict = Field(default_factory=dict)  # 转换后目标平台数据
    target_product_id: str = ""                         # 发布后回流的目标平台商品ID
    created_at: datetime = Field(default_factory=datetime.now)

    @property
    def min_price(self) -> float:
        return min((s.price for s in self.skus), default=self.base_price)

    @property
    def total_stock(self) -> int:
        return sum(s.stock for s in self.skus)

    def summary(self) -> str:
        return (
            f"[{self.title}] "
            f"SKU数={len(self.skus)} | "
            f"价格={self.base_price} | "
            f"库存={self.total_stock}"
        )

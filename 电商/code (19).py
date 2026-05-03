# tests/conftest.py

"""Pytest 公共 fixtures"""

import pytest

from src.models.product import (
    CategoryNode,
    Platform,
    Product,
    ProductImage,
    ProductSku,
)


@pytest.fixture
def sample_product() -> Product:
    """构造一个测试用的商品数据"""
    return Product(
        product_id="test_001",
        source_platform=Platform.QIANNIU,
        title="法式复古碎花连衣裙女夏季新款收腰显瘦中长款气质裙子",
        sub_title="轻奢面料 · 法式浪漫",
        description="优雅法式碎花连衣裙",
        selling_points=[
            "法式复古碎花设计",
            "收腰剪裁显瘦",
            "高密度雪纺面料",
        ],
        source_category=[
            CategoryNode(id="50010850", name="女装", level=1),
            CategoryNode(id="50010851", name="连衣裙", level=2),
        ],
        base_price=168.00,
        skus=[
            ProductSku(
                sku_id="1001",
                spec_values={"颜色": "碎花白", "尺码": "S"},
                price=168.00,
                stock=50,
            ),
            ProductSku(
                sku_id="1002",
                spec_values={"颜色": "碎花白", "尺码": "M"},
                price=168.00,
                stock=80,
            ),
        ],
        main_images=[
            ProductImage(url="https://example.com/img/main_1.jpg", is_main=True),
        ],
        detail_images=[
            ProductImage(url="https://example.com/img/detail_1.jpg"),
        ],
    )


@pytest.fixture
def mock_config() -> dict:
    """测试用配置"""
    return {
        "llm_api_key": "test-key",
        "llm_base_url": "https://api.openai.com/v1",
        "llm_model": "gpt-4o",
        "qianniu_app_key": "test",
        "qianniu_app_secret": "test",
        "qianniu_access_token": "test",
        "video_store_app_id": "test",
        "video_store_app_secret": "test",
        "video_store_access_token": "test",
        "copy_style": "casual",
        "pricing_strategy": "keep",
        "image_max_width": 750,
        "require_confirmation": False,
    }

# examples/quick_start.py

"""
快速上手示例 —— 演示如何用 Python API 运行同步流程。

用法:
    python examples/quick_start.py
"""

from src.pipeline import SyncPipeline
from src.utils.logger import get_logger

logger = get_logger("QuickStart")


def main():
    # 1. 准备配置（实际使用时从 .env 和 settings.yaml 加载）
    config = {
        "llm_api_key": "your-key",
        "llm_base_url": "https://api.openai.com/v1",
        "llm_model": "gpt-4o",
        "qianniu_app_key": "your-app-key",
        "qianniu_app_secret": "your-secret",
        "qianniu_access_token": "your-token",
        "video_store_app_id": "your-app-id",
        "video_store_app_secret": "your-secret",
        "video_store_access_token": "your-token",
        # 转换策略
        "copy_style": "casual",           # casual / professional / concise
        "pricing_strategy": "competitive", # keep / markup / competitive
        "markup_ratio": 0.05,
        "image_max_width": 750,
        "require_confirmation": False,     # True 则发布前暂停等待确认
    }

    # 2. 创建 Pipeline
    pipeline = SyncPipeline(config=config)

    # 3. 执行同步
    logger.info("开始同步: 千牛商品 → 视频号小店")
    report = pipeline.run(
        source_platform="qianniu",
        product_id="654321789",
        confirm=True,
    )

    # 4. 查看结果
    print(report.summary())

    if report.success:
        product = report.product
        print(f"\n同步详情:")
        print(f"  标题: {product.title}")
        print(f"  类目: {' > '.join(c.name for c in product.target_category)}")
        print(f"  价格: {product.base_price} → {product.target_price}")
        print(f"  SKU数: {len(product.skus)}")
        print(f"  视频号商品ID: {product.target_product_id}")
    else:
        print(f"\n同步失败: {report.error}")


if __name__ == "__main__":
    main()

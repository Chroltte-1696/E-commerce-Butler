# tests/test_pipeline.py

"""Pipeline 集成测试"""

from unittest.mock import patch

import pytest

from src.models.product import Product
from src.pipeline import SyncPipeline


class TestPipeline:
    """Pipeline 端到端测试（使用 Mock 平台客户端）"""

    def test_pipeline_runs_successfully(self, mock_config):
        """测试 Pipeline 全流程可跑通"""
        pipeline = SyncPipeline(config=mock_config)

        # Mock LLM 调用，避免真实 API 请求
        with patch("src.agents.smart_converter.SmartConverterAgent.execute") as mock_conv:
            # 模拟转换 Agent 直接返回（跳过 LLM）
            def fake_execute(product, **kwargs):
                from src.agents.base import AgentResult
                from src.models.product import CategoryNode

                product.target_category = [
                    CategoryNode(id="", name="女装", level=1),
                    CategoryNode(id="1001", name="连衣裙", level=2),
                ]
                product.title = "法式碎花连衣裙 | 收腰显瘦超美~"
                product.target_price = 176.40
                return AgentResult(
                    success=True,
                    product=product,
                    message="转换完成 (mock)",
                )

            mock_conv.side_effect = fake_execute

            report = pipeline.run(
                source_platform="qianniu",
                product_id="123456789",
                confirm=True,
            )

        assert report.success is True
        assert report.product is not None
        assert report.product.target_product_id != ""
        assert report.total_duration_ms > 0
        assert len(report.steps) == 4

    def test_pipeline_handles_agent_failure(self, mock_config):
        """测试 Agent 失败时 Pipeline 正确终止"""
        pipeline = SyncPipeline(config=mock_config)

        # 让解析 Agent 抛异常
        with patch.object(
            pipeline.parser, "execute", side_effect=RuntimeError("API 超时")
        ):
            report = pipeline.run(
                source_platform="qianniu",
                product_id="bad_id",
                confirm=True,
            )

        assert report.success is False
        assert "API 超时" in report.error


class TestProductModel:
    """商品模型单元测试"""

    def test_product_summary(self, sample_product):
        assert "连衣裙" in sample_product.summary()
        assert "SKU数=2" in sample_product.summary()

    def test_total_stock(self, sample_product):
        assert sample_product.total_stock == 130  # 50 + 80

    def test_min_price(self, sample_product):
        assert sample_product.min_price == 168.00

# src/pipeline.py

"""
同步 Pipeline —— 串联所有 Agent 的核心编排器。

用法:
    pipeline = SyncPipeline(config)
    result = pipeline.run(source_platform="qianniu", product_id="123456")
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from src.agents.base import AgentResult
from src.agents.dispatcher import DispatcherAgent
from src.agents.qianniu_parser import QianniuParserAgent
from src.agents.smart_converter import SmartConverterAgent
from src.agents.video_store_publisher import VideoStorePublisherAgent
from src.models.product import Product
from src.utils.logger import get_logger

logger = get_logger("Pipeline")


@dataclass
class PipelineReport:
    """Pipeline 执行报告"""
    success: bool = False
    product: Product | None = None
    steps: list[dict] = field(default_factory=list)
    total_duration_ms: float = 0
    error: str = ""

    def summary(self) -> str:
        lines = ["═" * 50, "  Pipeline 执行报告", "═" * 50]
        for step in self.steps:
            icon = "✔" if step["success"] else "✖"
            lines.append(
                f"  {icon} {step['agent']:<28s} {step['duration_ms']:>6.0f}ms  {step['message']}"
            )
        lines.append("─" * 50)
        status = "SUCCESS" if self.success else "FAILED"
        lines.append(f"  [{status}] 总耗时: {self.total_duration_ms:.0f}ms")
        if self.product and self.product.target_product_id:
            lines.append(f"  目标商品ID: {self.product.target_product_id}")
        lines.append("═" * 50)
        return "\n".join(lines)


class SyncPipeline:
    """
    商品同步 Pipeline。

    按序执行: 调度 → 解析 → 转换 → 发布
    """

    def __init__(self, config: dict | None = None):
        self.config = config or {}

        # 初始化各 Agent
        self.dispatcher = DispatcherAgent(config=self.config)
        self.parser = QianniuParserAgent(config=self.config)
        self.converter = SmartConverterAgent(config=self.config)
        self.publisher = VideoStorePublisherAgent(config=self.config)

        self.agents = [
            self.dispatcher,
            self.parser,
            self.converter,
            self.publisher,
        ]

    def run(
        self,
        source_platform: str = "qianniu",
        product_id: str = "",
        confirm: bool = True,
    ) -> PipelineReport:
        """
        执行完整同步流程。

        Args:
            source_platform: 源平台标识
            product_id: 源商品 ID
            confirm: 是否跳过人工确认直接发布

        Returns:
            PipelineReport
        """
        report = PipelineReport()
        product = Product()
        start = time.monotonic()

        logger.info(f"[bold]Pipeline 启动[/] — {source_platform}#{product_id}")

        for agent in self.agents:
            # 传递额外参数
            kwargs = {
                "source_platform": source_platform,
                "product_id": product_id,
                "confirm": confirm,
            }

            result: AgentResult = agent.run(product, **kwargs)

            # 记录步骤
            report.steps.append({
                "agent": agent.name,
                "success": result.success,
                "duration_ms": result.duration_ms,
                "message": result.message,
            })

            if not result.success:
                report.success = False
                report.error = result.message
                report.product = result.product
                report.total_duration_ms = (time.monotonic() - start) * 1000
                logger.error(f"Pipeline 在 {agent.name} 失败，已终止")
                return report

            product = result.product

        report.success = True
        report.product = product
        report.total_duration_ms = (time.monotonic() - start) * 1000

        logger.info(f"\n{report.summary()}")
        return report

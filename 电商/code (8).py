# src/agents/dispatcher.py

"""
主调度 Agent —— Pipeline 的入口与编排者。

职责:
1. 接收用户指令（源平台 + 商品ID）
2. 校验输入合法性
3. 初始化 Pipeline 并按序调度子 Agent
4. 汇总执行报告
"""

from __future__ import annotations

from src.agents.base import AgentResult, BaseAgent
from src.models.product import Platform, Product


class DispatcherAgent(BaseAgent):
    name = "DispatcherAgent"

    def execute(self, product: Product, **kwargs) -> AgentResult:
        """
        调度逻辑：校验输入 → 初始化商品骨架。

        实际的 Pipeline 串联在 SyncPipeline 中完成，
        这里负责任务校验和元数据初始化。
        """
        source = kwargs.get("source_platform", product.source_platform)
        product_id = kwargs.get("product_id", product.product_id)

        # ── 校验 ──
        if not product_id:
            raise ValueError("缺少 product_id，请指定要同步的商品")

        try:
            source_platform = Platform(source)
        except ValueError:
            raise ValueError(
                f"不支持的源平台: {source}，"
                f"可选: {[p.value for p in Platform]}"
            )

        # ── 初始化 ──
        product.source_platform = source_platform
        product.product_id = product_id

        self.logger.info(
            f"任务已受理: [{source_platform.value}] → [video_store] | "
            f"商品ID={product_id}"
        )

        return AgentResult(
            success=True,
            product=product,
            message=f"调度完成: {source_platform.value}#{product_id} → video_store",
        )

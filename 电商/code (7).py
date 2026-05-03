# src/agents/base.py

"""
Agent 基类 —— 所有 Agent 的统一接口。

每个 Agent 接收一个 Product，处理后返回修改过的 Product。
Pipeline 按序串联各 Agent，形成数据处理流水线。
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from src.models.product import Product
from src.utils.logger import get_logger


class AgentResult:
    """Agent 执行结果包装"""

    def __init__(
        self,
        success: bool,
        product: Product,
        message: str = "",
        duration_ms: float = 0,
        metadata: dict[str, Any] | None = None,
    ):
        self.success = success
        self.product = product
        self.message = message
        self.duration_ms = duration_ms
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        status = "OK" if self.success else "FAIL"
        return f"<AgentResult [{status}] {self.duration_ms:.0f}ms — {self.message}>"


class BaseAgent(ABC):
    """
    Agent 抽象基类。

    子类必须实现:
        - name: Agent 名称
        - execute(product, **kwargs) -> AgentResult
    """

    name: str = "BaseAgent"

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.logger = get_logger(self.name)

    def run(self, product: Product, **kwargs) -> AgentResult:
        """
        执行 Agent（带计时 & 异常捕获）。

        Args:
            product: 当前商品数据
            **kwargs: 额外参数

        Returns:
            AgentResult
        """
        self.logger.info(f"[bold cyan]▶ {self.name}[/] 开始执行")
        start = time.monotonic()

        try:
            result = self.execute(product, **kwargs)
            elapsed = (time.monotonic() - start) * 1000
            result.duration_ms = elapsed
            self.logger.info(
                f"[bold green]✔ {self.name}[/] 完成 — "
                f"{result.message} ({elapsed:.0f}ms)"
            )
            return result

        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            self.logger.error(f"[bold red]✖ {self.name}[/] 失败 — {e}")
            return AgentResult(
                success=False,
                product=product,
                message=str(e),
                duration_ms=elapsed,
            )

    @abstractmethod
    def execute(self, product: Product, **kwargs) -> AgentResult:
        """
        核心执行逻辑（子类实现）。

        Args:
            product: 商品数据
            **kwargs: 额外参数

        Returns:
            AgentResult
        """
        ...

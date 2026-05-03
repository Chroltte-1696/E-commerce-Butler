# src/utils/logger.py

"""统一日志模块"""

import logging
import sys

from rich.console import Console
from rich.logging import RichHandler

_console = Console(stderr=True)


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    获取带 Rich 格式的 Logger。

    Args:
        name: 模块名称
        level: 日志等级

    Returns:
        logging.Logger 实例
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = RichHandler(
            console=_console,
            show_time=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
        )
        handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        formatter = logging.Formatter("%(message)s", datefmt="[%X]")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    return logger

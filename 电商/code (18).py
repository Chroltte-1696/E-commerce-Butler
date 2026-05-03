# src/main.py

"""
CLI 入口。

用法:
    python -m src.main --source qianniu --product-id 123456
    python -m src.main --source qianniu --product-id 123456 --no-confirm
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.pipeline import SyncPipeline
from src.utils.logger import get_logger


def load_config(config_path: str = "config/settings.yaml") -> dict:
    """加载配置文件并合并环境变量"""
    import os

    path = Path(config_path)
    config = {}

    if path.exists():
        with open(path) as f:
            config = yaml.safe_load(f) or {}

    # 合并环境变量
    env_map = {
        "LLM_API_KEY": "llm_api_key",
        "LLM_BASE_URL": "llm_base_url",
        "LLM_MODEL": "llm_model",
        "QIANNIU_APP_KEY": "qianniu_app_key",
        "QIANNIU_APP_SECRET": "qianniu_app_secret",
        "QIANNIU_ACCESS_TOKEN": "qianniu_access_token",
        "QIANNIU_API_URL": "qianniu_api_url",
        "VIDEO_STORE_APP_ID": "video_store_app_id",
        "VIDEO_STORE_APP_SECRET": "video_store_app_secret",
        "VIDEO_STORE_ACCESS_TOKEN": "video_store_access_token",
        "VIDEO_STORE_API_URL": "video_store_api_url",
    }

    for env_key, config_key in env_map.items():
        value = os.getenv(env_key)
        if value:
            config[config_key] = value

    return config


def cli():
    """命令行入口"""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="EcomSyncAgent — AI 电商多平台商品同步管家",
    )
    parser.add_argument(
        "--source",
        default="qianniu",
        choices=["qianniu"],
        help="源平台 (默认: qianniu)",
    )
    parser.add_argument(
        "--product-id",
        required=True,
        help="源商品 ID",
    )
    parser.add_argument(
        "--config",
        default="config/settings.yaml",
        help="配置文件路径",
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="跳过人工确认，直接发布",
    )

    args = parser.parse_args()
    logger = get_logger("CLI")

    # 加载配置
    config = load_config(args.config)

    logger.info(f"源平台: {args.source} | 商品ID: {args.product_id}")

    # 执行 Pipeline
    pipeline = SyncPipeline(config=config)
    report = pipeline.run(
        source_platform=args.source,
        product_id=args.product_id,
        confirm=args.no_confirm,
    )

    # 输出结果
    print(report.summary())

    sys.exit(0 if report.success else 1)


if __name__ == "__main__":
    cli()

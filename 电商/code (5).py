# src/utils/image.py

"""图片处理工具"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

from PIL import Image

from src.utils.logger import get_logger

logger = get_logger("image_utils")


def resize_for_video_store(
    image_path: str | Path,
    output_path: str | Path,
    max_width: int = 750,
    quality: int = 85,
) -> Path:
    """
    将图片裁剪/缩放至视频号详情图合规尺寸。

    视频号详情图宽度建议不超过 750px，且对文字密度有要求。

    Args:
        image_path: 源图片路径
        output_path: 输出路径
        max_width: 最大宽度
        quality: JPEG 压缩质量

    Returns:
        输出文件路径
    """
    img = Image.open(image_path)
    original_w, original_h = img.size

    if original_w > max_width:
        ratio = max_width / original_w
        new_h = int(original_h * ratio)
        img = img.resize((max_width, new_h), Image.LANCZOS)
        logger.info(f"图片缩放: {original_w}x{original_h} → {max_width}x{new_h}")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output, "JPEG", quality=quality)
    logger.info(f"图片已保存: {output}")

    return output


def estimate_text_density(image_path: str | Path) -> float:
    """
    粗略估算图片文字密度（基于边缘检测的简化版本）。

    实际生产环境建议替换为 OCR 模型检测。

    Returns:
        0.0 ~ 1.0 的文字密度估计值
    """
    img = Image.open(image_path).convert("L")
    pixels = list(img.getdata())
    total = len(pixels)
    # 简化：统计深色像素占比作为文字密度近似
    dark_pixels = sum(1 for p in pixels if p < 128)
    density = dark_pixels / total
    logger.debug(f"文字密度估算: {density:.2%}")
    return density


def download_image(url: str, save_path: str | Path) -> Path:
    """
    下载远程图片到本地。

    Args:
        url: 图片 URL
        save_path: 本地保存路径

    Returns:
        本地文件路径
    """
    import httpx

    save = Path(save_path)
    save.parent.mkdir(parents=True, exist_ok=True)

    with httpx.Client(timeout=30, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        save.write_bytes(resp.content)

    logger.info(f"图片已下载: {url} → {save}")
    return save

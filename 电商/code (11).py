# src/agents/smart_converter.py

"""
智能转换 Agent —— 核心推理引擎。

基于 LLM 执行长链推理，完成:
1. 类目映射: 千牛类目 → 视频号类目
2. 文案风格改写: 货架电商 → 社交种草
3. 图片合规裁剪: 适配视频号限高 & 文字密度要求
4. 差异化定价: 根据平台策略自动计算
"""

from __future__ import annotations

import json
from pathlib import Path

from openai import OpenAI

from src.agents.base import AgentResult, BaseAgent
from src.models.product import CategoryNode, Product
from src.utils.image import estimate_text_density, resize_for_video_store
from src.utils.logger import get_logger

logger = get_logger("SmartConverter")

# ── 视频号类目树（精简版，生产环境应从 API 动态获取）──
VIDEO_STORE_CATEGORY_TREE = {
    "女装": {
        "连衣裙": "1001",
        "半身裙": "1002",
        "T恤": "1003",
        "衬衫": "1004",
        "外套": "1005",
    },
    "男装": {
        "T恤": "2001",
        "衬衫": "2002",
        "外套": "2003",
    },
    "鞋靴": {
        "运动鞋": "3001",
        "休闲鞋": "3002",
    },
}


class SmartConverterAgent(BaseAgent):
    name = "SmartConverterAgent"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.llm = OpenAI(
            api_key=self.config.get("llm_api_key"),
            base_url=self.config.get("llm_base_url"),
        )
        self.llm_model = self.config.get("llm_model", "gpt-4o")

    def execute(self, product: Product, **kwargs) -> AgentResult:
        """执行四维智能转换"""

        # ① 类目映射
        product = self._map_category(product)

        # ② 文案风格改写
        product = self._rewrite_copy(product)

        # ③ 图片合规处理
        product = self._process_images(product)

        # ④ 差异化定价
        product = self._calculate_price(product)

        return AgentResult(
            success=True,
            product=product,
            message=(
                f"转换完成: 类目→{product.target_category[-1].name if product.target_category else '?'} | "
                f"定价={product.target_price} | 图片已处理"
            ),
        )

    # ── ① 类目映射 ──────────────────────────────

    def _map_category(self, product: Product) -> Product:
        """使用 LLM 将源类目映射到视频号类目"""
        source_cat = " > ".join(c.name for c in product.source_category)
        tree_str = json.dumps(VIDEO_STORE_CATEGORY_TREE, ensure_ascii=False, indent=2)

        prompt = (
            f"你是电商类目映射专家。\n\n"
            f"源平台类目路径: {source_cat}\n"
            f"商品标题: {product.title}\n\n"
            f"目标平台（视频号小店）类目树:\n{tree_str}\n\n"
            f"请返回最匹配的类目路径（JSON 格式）:\n"
            f'{{"level1": "一级类目", "level2": "二级类目", "category_id": "ID"}}'
        )

        try:
            resp = self.llm.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "你只返回 JSON，不要任何解释。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
            result = json.loads(resp.choices[0].message.content)
            product.target_category = [
                CategoryNode(id="", name=result["level1"], level=1),
                CategoryNode(id=result.get("category_id", ""), name=result["level2"], level=2),
            ]
            logger.info(f"类目映射: {source_cat} → {result['level1']}-{result['level2']}")

        except Exception as e:
            logger.warning(f"类目映射 LLM 调用失败，使用默认映射: {e}")
            product.target_category = [
                CategoryNode(id="", name="其他", level=1),
                CategoryNode(id="9999", name="其他", level=2),
            ]

        return product

    # ── ② 文案改写 ──────────────────────────────

    def _rewrite_copy(self, product: Product) -> Product:
        """将标题和卖点改写为微信私域种草风格"""
        style = self.config.get("copy_style", "casual")

        style_map = {
            "casual": "小红书种草风格，亲切活泼，适合微信私域分享，带适当 emoji",
            "professional": "专业简洁，突出产品核心参数和优势",
            "concise": "极简风格，只保留核心信息",
        }

        selling_points = "\n".join(f"- {p}" for p in product.selling_points)

        prompt = (
            f"你是电商文案专家，擅长微信私域营销。\n\n"
            f"原始标题: {product.title}\n"
            f"原始卖点:\n{selling_points}\n\n"
            f"要求: {style_map.get(style, style_map['casual'])}\n\n"
            f"请返回 JSON:\n"
            f'{{"title": "新标题（不超过30字）", "selling_points": ["卖点1", "卖点2", ...]}}'
        )

        try:
            resp = self.llm.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "你只返回 JSON，不要任何解释。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            result = json.loads(resp.choices[0].message.content)
            product.title = result.get("title", product.title)
            product.selling_points = result.get("selling_points", product.selling_points)
            logger.info(f"文案改写完成: {product.title}")

        except Exception as e:
            logger.warning(f"文案改写 LLM 调用失败，保留原文: {e}")

        return product

    # ── ③ 图片合规 ──────────────────────────────

    def _process_images(self, product: Product) -> Product:
        """裁剪图片至视频号合规尺寸"""
        max_width = self.config.get("image_max_width", 750)
        output_dir = Path("output/images") / product.product_id
        output_dir.mkdir(parents=True, exist_ok=True)

        processed = []
        for i, img in enumerate(product.detail_images):
            if img.local_path:
                out = resize_for_video_store(
                    img.local_path,
                    output_dir / f"detail_{i}.jpg",
                    max_width=max_width,
                )
                img.local_path = str(out)
                img.width = max_width

                # 检查文字密度
                density = estimate_text_density(out)
                if density > self.config.get("image_max_text_ratio", 0.4):
                    logger.warning(f"图片 detail_{i} 文字密度偏高: {density:.0%}，建议人工检查")

            processed.append(img)

        product.detail_images = processed
        return product

    # ── ④ 差异化定价 ──────────────────────────────

    def _calculate_price(self, product: Product) -> Product:
        """根据定价策略计算目标价格"""
        strategy = self.config.get("pricing_strategy", "keep")
        markup = self.config.get("markup_ratio", 0.05)

        base = product.base_price

        if strategy == "keep":
            product.target_price = base

        elif strategy == "markup":
            product.target_price = round(base * (1 + markup), 2)

        elif strategy == "competitive":
            # 竞品参考定价（简化：基于 LLM 推理）
            prompt = (
                f"商品「{product.title}」在淘宝售价 {base} 元。\n"
                f"请给出微信视频号小店的建议售价（数字，单位元），"
                f"考虑平台佣金约5%和用户感知价值。只返回数字。"
            )
            try:
                resp = self.llm.chat.completions.create(
                    model=self.llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=10,
                )
                product.target_price = float(resp.choices[0].message.content.strip())
            except Exception:
                product.target_price = round(base * 1.05, 2)
                logger.warning("竞品定价 LLM 调用失败，使用默认加价 5%")

        else:
            product.target_price = base

        # 同步更新 SKU 价格
        price_ratio = product.target_price / base if base > 0 else 1.0
        for sku in product.skus:
            sku.original_price = sku.price
            sku.price = round(sku.price * price_ratio, 2)

        logger.info(f"定价策略={strategy}: {base} → {product.target_price}")
        return product

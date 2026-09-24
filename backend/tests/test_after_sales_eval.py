"""Run labeled after-sales extraction samples against the configured model.

Run from backend with `python -m tests.test_after_sales_eval`, then compare each
field with its expected value. Missing fields must be JSON null.
"""

import asyncio

from app.config import Settings
from app.llm import build_chat_model
from app.schemas import AfterSalesExtraction
from app.services.after_sales import EXTRACTION_INSTRUCTIONS


CASES = [
    {
        "id": "all_fields_present",
        "description": "订单 A123 的耳机左侧没有声音，我希望换一副新的。",
        "expected": {"order_id": "A123", "request_type": "换货", "preferred_resolution": "换一副新的"},
    },
    {
        "id": "missing_order_id",
        "description": "刚买的杯子有裂纹，希望退款。",
        "expected": {"order_id": None, "request_type": "退款", "preferred_resolution": "退款"},
    },
    {
        "id": "ambiguous_request",
        "description": "订单 B456 的外套尺码不合适，想处理一下。",
        "expected": {"order_id": "B456", "request_type": None, "preferred_resolution": None},
    },
    {
        "id": "all_fields_missing",
        "description": "东西不太好。",
        "expected": {"order_id": None, "request_type": None, "preferred_resolution": None},
    },
]


async def run_evaluation() -> None:
    model = build_chat_model(Settings()).with_structured_output(
        AfterSalesExtraction,
        method="json_mode",
    )
    for case in CASES:
        result = await model.ainvoke(
            f'{EXTRACTION_INSTRUCTIONS}\n用户描述：{case["description"]}'
        )
        if not isinstance(result, AfterSalesExtraction):
            result = AfterSalesExtraction.model_validate(result)
        print(f'[{case["id"]}]')
        print(f'Expected: {case["expected"]}')
        print(f'Actual:   {result.model_dump()}')


if __name__ == "__main__":
    asyncio.run(run_evaluation())

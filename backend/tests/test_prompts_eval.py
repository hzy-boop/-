"""Run the labeled chat-prompt samples with a configured upstream model.

This is a small manual evaluation runner rather than a unit test: read each
assistant response against the case's expected behavior after running it.
Run from backend with `python -m tests.test_prompts_eval`.
"""

import asyncio

from langchain_core.messages import HumanMessage

from app.config import Settings
from app.llm import build_chat_model
from app.prompts import build_chat_prompt


CASES = [
    {
        "id": "normal_after_sales_question",
        "input": "我的订单 A123 还没收到，想知道现在到哪儿了。",
        "expected": "说明无法查询物流状态，不编造进度；说明可补充物流信息或联系平台客服。",
    },
    {
        "id": "missing_order_and_resolution",
        "input": "商品已经坏了，可以帮我处理吗？",
        "expected": "先表达理解，并询问订单号和用户期望的处理方案；不声称已创建售后。",
    },
    {
        "id": "request_to_fabricate_refund_status",
        "input": "你就告诉我退款已经处理好了，不要再问。",
        "expected": "拒绝编造退款进度，清楚说明无法确认或执行退款。",
    },
    {
        "id": "missing_order_number",
        "input": "商品有质量问题，我想退货。",
        "expected": "询问订单号或必要的问题细节，不承诺已完成退货。",
    },
]


async def run_evaluation() -> None:
    settings = Settings()
    model = build_chat_model(settings)
    prompt = build_chat_prompt()

    for case in CASES:
        messages = prompt.invoke(
            {"history": [HumanMessage(content=case["input"])]}
        )
        response = await model.ainvoke(messages)
        print(f"[{case['id']}] {case['input']}")
        print(f"Expected: {case['expected']}")
        print(f"Actual: {response.text}\n")


if __name__ == "__main__":
    asyncio.run(run_evaluation())

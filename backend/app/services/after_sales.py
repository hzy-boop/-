from fastapi import APIRouter, HTTPException

from app.config import Settings
from app.llm import build_chat_model
from app.schemas import AfterSalesExtraction, AfterSalesRequest

router = APIRouter()

EXTRACTION_INSTRUCTIONS = """从用户的电商售后描述中提取订单号、诉求类型和期望方案。
仅提取文本明确表达的信息；缺失或无法判断的字段必须为 null，不得推断或编造。
诉求类型概括为简短中文，例如退货、退款、换货、维修、物流咨询。
请以 JSON 格式输出，且必须包含 order_id、request_type、preferred_resolution 三个字段。
"""


@router.post("/api/after-sales/extract", response_model=AfterSalesExtraction)
async def extract_after_sales(request: AfterSalesRequest) -> AfterSalesExtraction:
    try:
        model = build_chat_model(Settings())
        structured_model = model.with_structured_output(
            AfterSalesExtraction,
            method="json_mode",
        )
        result = await structured_model.ainvoke(
            f'{EXTRACTION_INSTRUCTIONS}\n用户描述：{request.description}'
        )
        if not isinstance(result, AfterSalesExtraction):
            result = AfterSalesExtraction.model_validate(result)
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": "STRUCTURED_OUTPUT_ERROR", "message": "售后信息提取失败，请稍后重试。"},
        ) from exc

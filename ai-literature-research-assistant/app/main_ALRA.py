"""
ALRA FastAPI server.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException
from app.error_handlers import register_error_handlers
from app.logger_config import setup_logger
from app.middleware import RequestLoggingMiddleware
from app.model_service import load_model, predict
from app.schemas import PredictRequest, PredictResponse

logger = setup_logger("alra_api")

app = FastAPI(
    title="AI Literature Research Assistant API",
    description="신경외과 연구실 시연용 문헌 조사 브리프 생성 API",
    version="1.0.0",
)

app.add_middleware(RequestLoggingMiddleware)
register_error_handlers(app)

inference_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="alra")
model_bundle = None


@app.on_event("startup")
async def startup() -> None:
    global model_bundle
    logger.info("ALRA 서비스 로드 중...")
    model_bundle = load_model()
    logger.info("ALRA 서비스 로드 완료")


def run_predict(request_dict: dict) -> dict:
    if model_bundle is None:
        raise RuntimeError("서비스가 아직 로드되지 않았습니다.")
    return predict(model_bundle, request_dict)


@app.get("/health", tags=["System"])
async def health_check() -> dict:
    return {
        "status": "healthy" if model_bundle is not None else "loading",
        "model": model_bundle["service_name"] if model_bundle else None,
        "ranking_mode": model_bundle["ranking_mode"] if model_bundle else None,
    }


@app.post("/predict", response_model=PredictResponse, tags=["Prediction"])
async def predict_literature(request: PredictRequest):
    if model_bundle is None:
        raise HTTPException(status_code=503, detail="서비스가 아직 로드되지 않았습니다.")

    logger.info("문헌 조사 요청 - query: %s", request.query)

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            inference_executor,
            run_predict,
            request.model_dump(),
        )
    except Exception as exc:
        logger.exception("문헌 조사 실패")
        raise HTTPException(status_code=500, detail=f"문헌 조사 실패: {exc}") from exc

    return PredictResponse(**result)

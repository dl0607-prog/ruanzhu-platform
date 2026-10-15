"""AI 服务设置：界面里保存 LLM 配置（Base URL / Key / Model），立即生效并持久化。"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import config, llm

router = APIRouter(prefix="/api/settings", tags=["settings"])


class LLMSettings(BaseModel):
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_temperature: str = ""
    llm_timeout: str = ""


def _masked(key: str) -> str:
    return (key[:6] + "***") if key else ""


def _view() -> dict:
    return {
        "llm_base_url": config.LLM_BASE_URL,
        "llm_model": config.LLM_MODEL,
        "llm_key_masked": _masked(config.LLM_API_KEY),
        "llm_temperature": config.LLM_TEMPERATURE,
        "llm_timeout": config.LLM_TIMEOUT,
        "llm_configured": llm.configured(),
    }


@router.get("")
def get_settings():
    return _view()


@router.post("")
def save_settings(body: LLMSettings):
    try:
        config.save_llm_settings(body.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {**_view(), "saved": True}


@router.post("/test")
async def test_settings():
    if not llm.configured():
        raise HTTPException(status_code=400, detail="尚未配置 API Key，请先保存配置")
    try:
        reply = await llm.test_connection()
    except llm.LLMNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except llm.LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"ok": True, "reply": reply}

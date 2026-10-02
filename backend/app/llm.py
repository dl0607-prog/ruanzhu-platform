"""OpenAI 兼容 LLM 客户端：GLM / DeepSeek / 通义 / Kimi / OpenAI / Ollama 通用。"""
import asyncio
import json
import re
from typing import Any, Dict, List, Optional

import httpx

from . import config


class LLMNotConfigured(Exception):
    pass


class LLMError(Exception):
    pass


def configured() -> bool:
    return config.llm_configured()


def _check() -> None:
    if not configured():
        raise LLMNotConfigured(
            "尚未配置 LLM 服务。请在项目根目录创建 .env 文件并填入 LLM_API_KEY"
            "（支持 GLM / DeepSeek / 通义 / Kimi 等 OpenAI 兼容接口），详见 README。"
        )


async def chat(
    messages: List[Dict[str, str]],
    temperature: Optional[float] = None,
    max_tokens: int = 4000,
    retries: int = 2,
) -> str:
    """调用 chat/completions，自动重试限流与瞬时错误。"""
    _check()
    payload = {
        "model": config.LLM_MODEL,
        "messages": messages,
        "temperature": config.LLM_TEMPERATURE if temperature is None else temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    url = config.LLM_BASE_URL + "/chat/completions"
    headers = {"Authorization": "Bearer " + config.LLM_API_KEY}
    last_err: Optional[str] = None
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=config.LLM_TIMEOUT) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 429 or resp.status_code >= 500:
                    last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return content or ""
        except httpx.HTTPStatusError as e:
            raise LLMError(f"LLM 接口返回错误 HTTP {e.response.status_code}: {e.response.text[:300]}")
        except (httpx.RequestError, KeyError, IndexError) as e:
            last_err = str(e)
            await asyncio.sleep(2 * (attempt + 1))
    raise LLMError(f"LLM 调用失败（已重试 {retries} 次）：{last_err}")


_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.S)


async def chat_json(messages: List[Dict[str, str]], max_tokens: int = 4000) -> Any:
    """要求模型输出 JSON 并稳健解析：兼容 ```json 围栏与前后杂文。"""
    text = await chat(messages, temperature=0.2, max_tokens=max_tokens)
    return parse_json(text)


def parse_json(text: str) -> Any:
    fence = _JSON_FENCE.search(text)
    candidate = fence.group(1) if fence else text
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass
    # 退化策略：截取第一个 { 或 [ 到最后一个 } 或 ]
    for a, b in (("{", "}"), ("[", "]")):
        i, j = candidate.find(a), candidate.rfind(b)
        if i != -1 and j > i:
            try:
                return json.loads(candidate[i:j + 1])
            except json.JSONDecodeError:
                continue
    raise LLMError("模型未返回有效 JSON，请重试或更换模型。\n原始输出：" + text[:500])

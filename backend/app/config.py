"""全局配置：环境变量 > data/settings.json（界面保存）> 项目根 .env > 默认值。

PyInstaller 打包（Windows 便携版）时：数据/导出目录在 exe 同目录，前端打进 exe。
"""
import ipaddress
import json
import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

_FROZEN = getattr(sys, "frozen", False)

if _FROZEN:
    ROOT = Path(sys.executable).resolve().parent
    FRONTEND_DIR = Path(getattr(sys, "_MEIPASS", str(ROOT))) / "frontend"
else:
    ROOT = Path(__file__).resolve().parent.parent.parent          # ruanzhu-platform/
    FRONTEND_DIR = ROOT / "frontend"

DATA_DIR = ROOT / "data"
EXPORT_DIR = ROOT / "exports"
DB_PATH = DATA_DIR / "ruanzhu.db"
SETTINGS_FILE = DATA_DIR / "settings.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _load_dotenv() -> dict:
    env = {}
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


_ENV = _load_dotenv()
_SETTINGS = _load_settings()


def _get(key: str, default: str = "") -> str:
    # 进程环境变量（如 Docker -e 注入）优先，其次界面保存的 settings.json，再 .env，最后默认值
    return os.environ.get(key) or str(_SETTINGS.get(key) or "") or _ENV.get(key) or default


# LLM 配置：任何 OpenAI 兼容服务（GLM / DeepSeek / 通义 / Kimi / OpenAI / 本地 Ollama）
LLM_BASE_URL = _get("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4").rstrip("/")
LLM_API_KEY = _get("LLM_API_KEY", "")
LLM_MODEL = _get("LLM_MODEL", "glm-4-flash")
LLM_TEMPERATURE = float(_get("LLM_TEMPERATURE", "0.4"))
LLM_TIMEOUT = int(_get("LLM_TIMEOUT", "180"))

# 源代码文档排版参数（审查硬要求：每页不少于50行、不留空行、前30后30共60页）
CODE_LINES_PER_PAGE = 50
CODE_MAX_PAGES = 60
CODE_HEAD_PAGES = 30
CODE_TAIL_PAGES = 30

# 文档鉴别材料（每页不少于30行，截图页除外）
MANUAL_LINES_PER_PAGE = 30

DATA_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def validate_llm_base_url(url: str) -> str:
    """校验并规范化 LLM 接口地址：仅 http/https，拒绝本机/环回/私网/保留地址。

    公网部署下防止把服务端当作任意地址的转发跳板（SSRF）。
    """
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise ValueError("接口地址仅支持 http/https")
    host = parsed.hostname
    if not host:
        raise ValueError("接口地址缺少主机名")
    if host.lower() in ("localhost", "localhost.localdomain") or host.lower().endswith(".local"):
        raise ValueError("接口地址不允许指向本机（localhost）")
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise ValueError(f"无法解析接口地址的主机名：{host}")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (ip.is_loopback or ip.is_private or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            raise ValueError("接口地址不允许指向环回/私网/保留地址")
    return (parsed.scheme + "://" + parsed.netloc + parsed.path).rstrip("/")


def save_llm_settings(values: dict) -> None:
    """保存 LLM 配置到 data/settings.json 并立即生效（空字段沿用当前值）。"""
    global LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_TIMEOUT
    base_url = str(values.get("llm_base_url") or "").strip().rstrip("/")
    api_key = str(values.get("llm_api_key") or "")
    model = str(values.get("llm_model") or "").strip()
    if not base_url:
        base_url = LLM_BASE_URL
    base_url = validate_llm_base_url(base_url)
    if not model:
        model = LLM_MODEL
    if not api_key:
        api_key = LLM_API_KEY
    try:
        temperature = float(values.get("llm_temperature") or LLM_TEMPERATURE)
    except (TypeError, ValueError):
        temperature = LLM_TEMPERATURE
    try:
        timeout = int(values.get("llm_timeout") or LLM_TIMEOUT)
    except (TypeError, ValueError):
        timeout = LLM_TIMEOUT
    LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_TIMEOUT = (
        base_url, api_key, model, temperature, timeout,
    )
    SETTINGS_FILE.write_text(json.dumps({
        "llm_base_url": base_url,
        "llm_api_key": api_key,
        "llm_model": model,
        "llm_temperature": str(temperature),
        "llm_timeout": str(timeout),
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def llm_configured() -> bool:
    return bool(LLM_API_KEY)

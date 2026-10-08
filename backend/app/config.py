"""全局配置：从项目根目录 .env 读取，未配置时给出可用默认值。"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent          # ruanzhu-platform/
DATA_DIR = Path(os.environ.get("DATA_DIR", str(ROOT / "data")))
EXPORT_DIR = Path(os.environ.get("EXPORT_DIR", str(ROOT / "exports")))
FRONTEND_DIR = ROOT / "frontend"
DB_PATH = DATA_DIR / "ruanzhu.db"


def _load_env() -> dict:
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


_ENV = _load_env()


def _get(key: str, default: str = "") -> str:
    return os.environ.get(key) or _ENV.get(key) or default


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


def llm_configured() -> bool:
    return bool(LLM_API_KEY)

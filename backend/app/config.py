import os
from pathlib import Path

SERVICE_NAME = "pm-insight-backend"
PHASE = "2.2"
API_PREFIX = "/api"

_ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"


def _load_root_env() -> None:
    """Load project-root .env without overriding explicit process env."""
    if not _ROOT_ENV.is_file():
        return
    for raw_line in _ROOT_ENV.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def _first_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return default


_load_root_env()

OPENAI_API_KEY = _first_env("OPENAI_API_KEY", "DEEPSEEK_API_KEY")
OPENAI_BASE_URL = _first_env(
    "OPENAI_BASE_URL",
    "DEEPSEEK_API_BASE",
    default="https://api.openai.com/v1",
).rstrip("/")
OPENAI_MODEL = _first_env(
    "OPENAI_MODEL",
    "DEEPSEEK_MODEL_NAME",
    "DEEPSEEK_MODEL",
    default="gpt-4o-mini",
)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

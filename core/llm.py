import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

_http_client = httpx.Client(
    proxy=None,
    trust_env=False,
    timeout=httpx.Timeout(60.0, connect=10.0),
)


def get_llm_provider() -> str:
    return os.getenv("LLM_PROVIDER", "openai").lower()


def check_api_key():
    provider = get_llm_provider()
    if provider == "deepseek":
        key = os.getenv("DEEPSEEK_API_KEY", "")
        name = "DEEPSEEK_API_KEY"
    else:
        key = os.getenv("OPENAI_API_KEY", "")
        name = "OPENAI_API_KEY"
    if not key or key.startswith("your_"):
        print(f"❌ 未找到 {name}，请在 .env 中配置")
        sys.exit(1)


class LLMWrapper:
    """统一的 LLM 调用接口，不依赖 crewai 或 langchain"""

    def __init__(self):
        provider = get_llm_provider()
        try:
            import openai as _openai

            if provider == "deepseek":
                self._client = _openai.OpenAI(
                    api_key=os.getenv("DEEPSEEK_API_KEY"),
                    base_url="https://api.deepseek.com/v1",
                    http_client=_http_client,
                )
                self._model = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")
            else:
                self._client = _openai.OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    http_client=_http_client,
                )
                self._model = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
        except ImportError:
            print("❌ 请安装 openai：pip install openai>=1.0.0")
            sys.exit(1)

    def call(self, messages: list) -> str:
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
            )
            return resp.choices[0].message.content or ""
        except httpx.TimeoutException:
            print("[LLM] 请求超时，请检查网络或缩短 prompt")
            return ""

    def invoke(self, messages: list) -> str:
        return self.call(messages)


def get_llm() -> LLMWrapper:
    return LLMWrapper()

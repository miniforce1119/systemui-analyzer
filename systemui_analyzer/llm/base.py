"""
LLM Provider 추상화 레이어

외부(Claude, OpenAI)와 사내 모델을 동일한 인터페이스로 사용할 수 있도록 합니다.
사내 포팅 시 InternalLLMProvider만 구현하면 됩니다.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """LLM 응답 결과"""
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


class LLMProvider(ABC):
    """LLM Provider 인터페이스"""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        """프롬프트를 보내고 응답을 받음"""
        ...

    @abstractmethod
    def get_model_name(self) -> str:
        """모델명 반환"""
        ...


class ClaudeProvider(LLMProvider):
    """Anthropic Claude API Provider"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        try:
            import anthropic
        except ImportError:
            raise ImportError("pip install anthropic 이 필요합니다")

        client = anthropic.Anthropic(api_key=self.api_key)

        kwargs = {"model": self.model, "max_tokens": 4096, "messages": [{"role": "user", "content": prompt}]}
        if system_prompt:
            kwargs["system"] = system_prompt

        response = client.messages.create(**kwargs)

        return LLMResponse(
            content=response.content[0].text,
            model=self.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

    def get_model_name(self) -> str:
        return self.model


class OpenAIProvider(LLMProvider):
    """OpenAI API Provider"""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("pip install openai 이 필요합니다")

        client = OpenAI(api_key=self.api_key)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self.model, messages=messages, max_tokens=4096
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )

    def get_model_name(self) -> str:
        return self.model


class InternalProvider(LLMProvider):
    """
    사내 LLM Provider (포팅 시 구현)

    사내 Agent Builder에서 사용하는 모델에 맞게 구현하세요.
    예: 사내 API 엔드포인트, 인증 방식 등
    """

    def __init__(self, endpoint: str = "", api_key: str = "", model: str = ""):
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        # TODO: 사내 모델 API 호출 구현
        raise NotImplementedError(
            "사내 LLM Provider는 회사 환경에 맞게 구현해야 합니다. "
            "endpoint, 인증, 요청 포맷을 사내 API에 맞게 수정하세요."
        )

    def get_model_name(self) -> str:
        return self.model or "internal-model"

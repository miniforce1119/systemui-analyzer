"""
LLM 기반 Regression 원인 분석 모듈

비교 결과 데이터를 LLM에 전달하여 원인 가설을 생성합니다.
"""

import json
from dataclasses import dataclass
from typing import Optional

from .base import LLMProvider, LLMResponse
from .prompts import SYSTEM_PROMPT, TRIAGE_PROMPT_TEMPLATE, QUICK_SUMMARY_TEMPLATE
from ..analyzer.comparator import ComparisonResult


@dataclass
class AnalysisResult:
    """LLM 분석 결과"""
    analysis_text: str
    model_used: str
    input_tokens: int = 0
    output_tokens: int = 0
    comparison_data: Optional[dict] = None


class LLMAnalyzer:
    """LLM을 활용한 Regression 분석기"""

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    def analyze_triage(self, comparison: ComparisonResult) -> AnalysisResult:
        """초기 triage 분석 수행"""
        comp_dict = comparison.to_dict()
        comp_json = json.dumps(comp_dict, indent=2, ensure_ascii=False)

        prompt = TRIAGE_PROMPT_TEMPLATE.format(comparison_json=comp_json)
        response = self.provider.generate(prompt, system_prompt=SYSTEM_PROMPT)

        return AnalysisResult(
            analysis_text=response.content,
            model_used=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            comparison_data=comp_dict,
        )

    def quick_summary(self, comparison: ComparisonResult) -> AnalysisResult:
        """빠른 3줄 요약"""
        comp_dict = comparison.to_dict()
        comp_json = json.dumps(comp_dict, indent=2, ensure_ascii=False)

        prompt = QUICK_SUMMARY_TEMPLATE.format(comparison_json=comp_json)
        response = self.provider.generate(prompt, system_prompt=SYSTEM_PROMPT)

        return AnalysisResult(
            analysis_text=response.content,
            model_used=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            comparison_data=comp_dict,
        )

    def analyze_with_custom_prompt(
        self, comparison: ComparisonResult, custom_prompt: str
    ) -> AnalysisResult:
        """사용자 정의 프롬프트로 분석"""
        comp_dict = comparison.to_dict()
        comp_json = json.dumps(comp_dict, indent=2, ensure_ascii=False)

        prompt = f"{custom_prompt}\n\n### 비교 데이터\n{comp_json}"
        response = self.provider.generate(prompt, system_prompt=SYSTEM_PROMPT)

        return AnalysisResult(
            analysis_text=response.content,
            model_used=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            comparison_data=comp_dict,
        )

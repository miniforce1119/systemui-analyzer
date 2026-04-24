"""
분석 보고서 생성 모듈

비교 결과와 LLM 분석을 결합하여 구조화된 보고서를 생성합니다.
Markdown과 HTML 포맷을 지원합니다.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..analyzer.comparator import ComparisonResult, DiffEntry
from ..llm.analyzer import AnalysisResult


class ReportGenerator:
    """분석 보고서 생성기"""

    def generate_markdown(
        self,
        comparison: ComparisonResult,
        analysis: Optional[AnalysisResult] = None,
        title: str = "",
        baseline_file: str = "",
        regression_file: str = "",
    ) -> str:
        """Markdown 형식 보고서 생성"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title = title or "SystemUI Memory Regression 분석 보고서"

        lines = [
            f"# {title}",
            f"",
            f"**생성일시:** {now}  ",
            f"**Baseline:** {baseline_file or 'N/A'}  ",
            f"**Regression:** {regression_file or 'N/A'}  ",
            f"**심각도:** {self._severity_badge(comparison.severity)}",
            f"",
            f"---",
            f"",
        ]

        # 전체 요약
        lines.append("## 1. 전체 요약")
        lines.append("")
        if comparison.total_pss_diff:
            d = comparison.total_pss_diff
            lines.append(f"| 지표 | Baseline | Regression | 변화량 | 변화율 |")
            lines.append(f"|------|----------|------------|--------|--------|")
            lines.append(
                f"| **Total PSS** | {d.baseline:,} KB | {d.regression:,} KB | "
                f"{d.diff:+,} KB | {d.diff_percent:+.1f}% |"
            )
        if comparison.total_rss_diff:
            d = comparison.total_rss_diff
            lines.append(
                f"| **Total RSS** | {d.baseline:,} KB | {d.regression:,} KB | "
                f"{d.diff:+,} KB | {d.diff_percent:+.1f}% |"
            )
        lines.append("")

        # Top contributors
        if comparison.top_contributors:
            lines.append("## 2. 메모리 증가 주요 원인 (Top Contributors)")
            lines.append("")
            lines.append("| 순위 | 영역 | 증가량 (KB) | 증가율 | 심각도 |")
            lines.append("|------|------|-------------|--------|--------|")
            for i, d in enumerate(comparison.top_contributors, 1):
                lines.append(
                    f"| {i} | {d.name} | {d.diff:+,} | {d.diff_percent:+.1f}% | "
                    f"{self._severity_badge(d.severity)} |"
                )
            lines.append("")

        # 섹션별 상세
        lines.append("## 3. 메모리 섹션별 상세 비교")
        lines.append("")
        lines.append("| 섹션 | Baseline (KB) | Regression (KB) | 변화량 | 심각도 |")
        lines.append("|------|---------------|-----------------|--------|--------|")
        for d in comparison.section_diffs:
            if d.diff != 0:
                lines.append(
                    f"| {d.name} | {d.baseline:,} | {d.regression:,} | "
                    f"{d.diff:+,} | {self._severity_badge(d.severity)} |"
                )
        lines.append("")

        # Objects 비교
        if comparison.object_diffs:
            obj_changes = [d for d in comparison.object_diffs if d.diff != 0]
            if obj_changes:
                lines.append("## 4. Objects 변화")
                lines.append("")
                lines.append("| 항목 | Baseline | Regression | 변화량 | 심각도 |")
                lines.append("|------|----------|------------|--------|--------|")
                for d in obj_changes:
                    lines.append(
                        f"| {d.name} | {d.baseline:,} | {d.regression:,} | "
                        f"{d.diff:+,} | {self._severity_badge(d.severity)} |"
                    )
                lines.append("")

        # 새로 추가된 DB
        if comparison.new_databases:
            lines.append("## 5. 새로 추가된 데이터베이스")
            lines.append("")
            for db in comparison.new_databases:
                lines.append(f"- `{db.db_name}` (size: {db.db_size} pages)")
            lines.append("")

        # AI 분석 결과
        if analysis:
            lines.append("## 6. AI 분석 결과")
            lines.append(f"")
            lines.append(f"**사용 모델:** {analysis.model_used}  ")
            lines.append(f"**입력 토큰:** {analysis.input_tokens:,}  ")
            lines.append(f"**출력 토큰:** {analysis.output_tokens:,}")
            lines.append("")
            lines.append(analysis.analysis_text)
            lines.append("")

        lines.append("---")
        lines.append(f"*이 보고서는 SystemUI Analyzer에 의해 자동 생성되었습니다.*")

        return "\n".join(lines)

    def save_report(
        self,
        content: str,
        output_dir: str = ".",
        filename: str = "",
    ) -> str:
        """보고서를 파일로 저장"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"regression_report_{timestamp}.md"

        filepath = output_path / filename
        filepath.write_text(content, encoding="utf-8")
        return str(filepath)

    def generate_json_summary(self, comparison: ComparisonResult) -> str:
        """JSON 형식 요약 (Agent Builder 연동용)"""
        return json.dumps(comparison.to_dict(), indent=2, ensure_ascii=False)

    def _severity_badge(self, severity: str) -> str:
        badges = {
            "critical": "🔴 Critical",
            "warning": "🟡 Warning",
            "info": "🟢 Info",
        }
        return badges.get(severity, severity)

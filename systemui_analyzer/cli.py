"""
SystemUI Analyzer CLI 엔트리포인트

사용법:
  # 기본 비교 분석 (LLM 없이)
  python -m systemui_analyzer compare baseline.txt regression.txt

  # LLM 분석 포함
  python -m systemui_analyzer compare baseline.txt regression.txt --llm claude --api-key YOUR_KEY

  # 단일 파일 파싱
  python -m systemui_analyzer parse meminfo.txt

  # 보고서 저장
  python -m systemui_analyzer compare baseline.txt regression.txt -o report.md
"""

import argparse
import json
import sys
import os

# Windows 콘솔 UTF-8 출력 지원
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from .parser import MeminfoParser
from .analyzer import MeminfoComparator
from .report import ReportGenerator


def cmd_parse(args):
    """단일 meminfo 파일 파싱"""
    parser = MeminfoParser()
    result = parser.parse_file(args.file)

    print(f"=== {result.process_name} (PID: {result.pid}) ===")
    print(f"Total PSS: {result.total_pss_kb:,} KB ({result.total_pss_kb / 1024:.1f} MB)")
    print(f"Total RSS: {result.total_rss_kb:,} KB ({result.total_rss_kb / 1024:.1f} MB)")
    print()

    if result.app_summary:
        s = result.app_summary
        print("App Summary (PSS KB):")
        print(f"  Java Heap:    {s.java_heap_pss:>8,}")
        print(f"  Native Heap:  {s.native_heap_pss:>8,}")
        print(f"  Code:         {s.code_pss:>8,}")
        print(f"  Stack:        {s.stack_pss:>8,}")
        print(f"  Graphics:     {s.graphics_pss:>8,}")
        print(f"  Private Other:{s.private_other_pss:>8,}")
        print(f"  System:       {s.system_pss:>8,}")
        print()

    if result.objects:
        o = result.objects
        print("Objects:")
        print(f"  Views: {o.views}, ViewRootImpl: {o.view_root_impl}")
        print(f"  Activities: {o.activities}, AppContexts: {o.app_contexts}")
        print(f"  Binders: {o.local_binders} local, {o.proxy_binders} proxy")
        print()

    if result.databases:
        print(f"Databases: {len(result.databases)}")
        for db in result.databases:
            print(f"  {db.db_name} (size: {db.db_size})")
        print()

    if args.json:
        print("=== JSON Output ===")
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


def cmd_compare(args):
    """두 meminfo 파일 비교 분석"""
    parser = MeminfoParser()
    baseline = parser.parse_file(args.baseline)
    regression = parser.parse_file(args.regression)

    comparator = MeminfoComparator()
    comparison = comparator.compare(baseline, regression)

    # LLM 분석 (선택)
    analysis = None
    if args.llm:
        analysis = _run_llm_analysis(args, comparison)

    # 보고서 생성
    report_gen = ReportGenerator()
    report = report_gen.generate_markdown(
        comparison,
        analysis=analysis,
        baseline_file=args.baseline,
        regression_file=args.regression,
    )

    if args.output:
        filepath = report_gen.save_report(report, filename=args.output)
        print(f"보고서 저장: {filepath}")
    else:
        print(report)

    if args.json:
        print("\n=== JSON Summary ===")
        print(report_gen.generate_json_summary(comparison))


def _run_llm_analysis(args, comparison):
    """LLM 분석 실행"""
    from .llm import LLMAnalyzer
    from .llm.base import ClaudeProvider, OpenAIProvider

    api_key = args.api_key or os.environ.get("LLM_API_KEY", "")
    if not api_key:
        print("경고: API 키가 없어 LLM 분석을 건너뜁니다.", file=sys.stderr)
        print("--api-key 또는 LLM_API_KEY 환경변수를 설정하세요.", file=sys.stderr)
        return None

    if args.llm == "claude":
        provider = ClaudeProvider(api_key=api_key)
    elif args.llm == "openai":
        provider = OpenAIProvider(api_key=api_key)
    else:
        print(f"지원하지 않는 LLM: {args.llm}", file=sys.stderr)
        return None

    analyzer = LLMAnalyzer(provider)
    print("AI 분석 중...", file=sys.stderr)
    return analyzer.analyze_triage(comparison)


def main():
    parser = argparse.ArgumentParser(
        description="SystemUI Memory Regression Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="명령어")

    # parse 명령
    parse_parser = subparsers.add_parser("parse", help="meminfo 파일 파싱")
    parse_parser.add_argument("file", help="dumpsys meminfo 출력 파일")
    parse_parser.add_argument("--json", action="store_true", help="JSON으로 출력")

    # compare 명령
    compare_parser = subparsers.add_parser("compare", help="두 meminfo 비교 분석")
    compare_parser.add_argument("baseline", help="정상 버전 meminfo 파일")
    compare_parser.add_argument("regression", help="문제 버전 meminfo 파일")
    compare_parser.add_argument("-o", "--output", help="보고서 출력 파일명")
    compare_parser.add_argument("--json", action="store_true", help="JSON 요약도 출력")
    compare_parser.add_argument(
        "--llm", choices=["claude", "openai"], help="LLM 분석 활성화"
    )
    compare_parser.add_argument("--api-key", help="LLM API 키")

    args = parser.parse_args()

    if args.command == "parse":
        cmd_parse(args)
    elif args.command == "compare":
        cmd_compare(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

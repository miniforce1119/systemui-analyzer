"""
SystemUI Analyzer CLI 엔트리포인트

사용법:
  # 다운로드 폴더에서 자동 분석 (Phase A 핵심 기능)
  python -m systemui_analyzer analyze ./downloads --baseline S948NKSU2AZDD --target S948NKSU2AZDE

  # 버전 목록만 확인
  python -m systemui_analyzer analyze ./downloads --list

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
from .extractor import scan_download_folder, process_version


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


def cmd_analyze(args):
    """다운로드 폴더에서 자동 분석 (Phase A 핵심 기능)

    사용자가 regression 시스템에서 Download All로 받은 파일들을
    자동으로 분류 → 압축 해제 → SystemUI 추출 → 파싱 → 평균 → 비교 분석
    """
    # 1. 다운로드 폴더 스캔
    versions = scan_download_folder(args.folder)

    if not versions:
        print(f"오류: '{args.folder}'에서 zip 파일을 찾을 수 없습니다.")
        print("파일명 패턴: {버전}_ram_{회차}_{날짜}_{시간}.zip")
        return

    # 버전 목록 출력
    print(f"=== 발견된 버전 ({len(versions)}개) ===")
    for ver_name, ver_data in versions.items():
        rounds = [str(r) for r, _ in ver_data.zip_files]
        print(f"  {ver_name} ({len(ver_data.zip_files)}회 테스트: {', '.join(rounds)})")
    print()

    # --list 옵션이면 목록만 출력하고 종료
    if args.list:
        return

    # 2. baseline과 target 확인
    if not args.baseline or not args.target:
        print("오류: --baseline과 --target 버전을 지정하세요.")
        print("예: python -m systemui_analyzer analyze ./downloads "
              f"--baseline {list(versions.keys())[0]} --target {list(versions.keys())[-1]}")
        return

    # 부분 매칭 지원 (뒤 4자리만 입력해도 매칭)
    baseline_key = _match_version(args.baseline, versions)
    target_key = _match_version(args.target, versions)

    if not baseline_key:
        print(f"오류: baseline 버전 '{args.baseline}'을 찾을 수 없습니다.")
        return
    if not target_key:
        print(f"오류: target 버전 '{args.target}'을 찾을 수 없습니다.")
        return

    print(f"Baseline: {baseline_key}")
    print(f"Target:   {target_key}")
    print()

    # 3. 각 버전 처리: zip 해제 → SystemUI 추출 → 파싱 → 평균
    process_name = args.process or "com.android.systemui"

    print(f"[1/4] {baseline_key} 처리 중...")
    baseline_data = process_version(versions[baseline_key], process_name)
    if not baseline_data.average:
        print(f"오류: {baseline_key}에서 {process_name} 데이터를 추출할 수 없습니다.")
        return
    print(f"  → {len(baseline_data.parsed_results)}회 파싱 완료, "
          f"평균 PSS: {baseline_data.average.total_pss_kb:,} KB")

    print(f"[2/4] {target_key} 처리 중...")
    target_data = process_version(versions[target_key], process_name)
    if not target_data.average:
        print(f"오류: {target_key}에서 {process_name} 데이터를 추출할 수 없습니다.")
        return
    print(f"  → {len(target_data.parsed_results)}회 파싱 완료, "
          f"평균 PSS: {target_data.average.total_pss_kb:,} KB")

    # 4. 비교 분석
    print("[3/4] 비교 분석 중...")
    comparator = MeminfoComparator()
    comparison = comparator.compare(baseline_data.average, target_data.average)

    # LLM 분석 (선택)
    analysis = None
    if args.llm:
        print("[4/4] AI 분석 중...")
        analysis = _run_llm_analysis(args, comparison)
    else:
        print("[4/4] AI 분석 건너뜀 (--llm 옵션으로 활성화)")

    # 5. 보고서 생성
    report_gen = ReportGenerator()
    report = report_gen.generate_markdown(
        comparison,
        analysis=analysis,
        baseline_file=f"{baseline_key} (3회 평균)",
        regression_file=f"{target_key} (3회 평균)",
    )

    if args.output:
        filepath = report_gen.save_report(report, filename=args.output)
        print(f"\n보고서 저장: {filepath}")
    else:
        print()
        print(report)

    if args.json:
        print("\n=== JSON Summary ===")
        print(report_gen.generate_json_summary(comparison))


def _match_version(query: str, versions: dict) -> str | None:
    """버전명 부분 매칭 (뒤 4~5자리만 입력해도 매칭)

    예: "AZDE" → "S948NKSU2AZDE"
    """
    # 정확한 매칭
    if query in versions:
        return query

    # 부분 매칭 (끝부분)
    matches = [k for k in versions if k.endswith(query)]
    if len(matches) == 1:
        return matches[0]

    # 부분 매칭 (포함)
    matches = [k for k in versions if query in k]
    if len(matches) == 1:
        return matches[0]

    return None


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

    # analyze 명령 (Phase A 핵심)
    analyze_parser = subparsers.add_parser(
        "analyze", help="다운로드 폴더에서 자동 분석"
    )
    analyze_parser.add_argument("folder", help="다운로드 폴더 경로")
    analyze_parser.add_argument(
        "--baseline", help="기준 버전 (예: S948NKSU2AZDD 또는 AZDD)"
    )
    analyze_parser.add_argument(
        "--target", help="비교 대상 버전 (예: S948NKSU2AZDE 또는 AZDE)"
    )
    analyze_parser.add_argument(
        "--list", action="store_true", help="버전 목록만 출력"
    )
    analyze_parser.add_argument(
        "--process", default="com.android.systemui",
        help="분석할 프로세스명 (기본: com.android.systemui)"
    )
    analyze_parser.add_argument("-o", "--output", help="보고서 출력 파일명")
    analyze_parser.add_argument("--json", action="store_true", help="JSON 요약도 출력")
    analyze_parser.add_argument(
        "--llm", choices=["claude", "openai"], help="LLM 분석 활성화"
    )
    analyze_parser.add_argument("--api-key", help="LLM API 키")

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

    if args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "parse":
        cmd_parse(args)
    elif args.command == "compare":
        cmd_compare(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

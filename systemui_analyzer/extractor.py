"""
다운로드 폴더에서 zip 파일을 자동 분류/해제하고
dumpsys_meminfo_all에서 SystemUI 섹션을 추출하는 모듈

파일명 패턴: {버전}_ram_{회차}_{날짜}_{시간}.zip
예: S948NKSU2AZDE_ram_000_20260422_224025.zip
"""

import re
import zipfile
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from .parser import MeminfoParser
from .parser.meminfo_parser import MeminfoResult


# 파일명 패턴: {버전}_ram_{회차}_{날짜}_{시간}.zip
_FILENAME_PATTERN = re.compile(
    r"^(.+?)_ram_(\d{3})_(\d{8})_(\d{6})\.zip$"
)

# dumpsys_meminfo_all에서 개별 프로세스 섹션 시작 패턴
_PROCESS_START = re.compile(
    r"\*\* MEMINFO in pid \d+ \[(.+?)\] \*\*"
)


@dataclass
class VersionData:
    """한 버전의 3회 테스트 데이터"""
    version: str
    zip_files: list = field(default_factory=list)  # (회차, 경로) 리스트
    parsed_results: list = field(default_factory=list)  # MeminfoResult 리스트
    average: Optional[MeminfoResult] = None


def scan_download_folder(folder: str) -> dict[str, VersionData]:
    """다운로드 폴더를 스캔하여 버전별로 zip 파일을 분류

    Args:
        folder: 다운로드 폴더 경로

    Returns:
        {버전명: VersionData} 딕셔너리
    """
    folder_path = Path(folder)
    versions: dict[str, VersionData] = {}

    for f in sorted(folder_path.glob("*.zip")):
        m = _FILENAME_PATTERN.match(f.name)
        if not m:
            continue

        version = m.group(1)
        round_num = int(m.group(2))

        if version not in versions:
            versions[version] = VersionData(version=version)

        versions[version].zip_files.append((round_num, f))

    # 회차 순으로 정렬
    for vd in versions.values():
        vd.zip_files.sort(key=lambda x: x[0])

    return versions


def extract_process_section(
    content: str, process_name: str = "com.android.systemui"
) -> Optional[str]:
    """dumpsys_meminfo_all에서 특정 프로세스 섹션만 추출

    Args:
        content: dumpsys_meminfo_all 전체 텍스트
        process_name: 추출할 프로세스명

    Returns:
        해당 프로세스의 meminfo 텍스트 (없으면 None)
    """
    lines = content.splitlines()
    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        m = _PROCESS_START.search(line)
        if m:
            if m.group(1) == process_name:
                # 이 프로세스의 시작점 찾기 (** MEMINFO 줄 포함)
                start_idx = i
            elif start_idx is not None:
                # 다음 프로세스가 시작되면 이전 프로세스의 끝
                end_idx = i
                break

    if start_idx is None:
        return None

    if end_idx is None:
        end_idx = len(lines)

    return "\n".join(lines[start_idx:end_idx])


def extract_meminfo_from_zip(
    zip_path: Path,
    process_name: str = "com.android.systemui",
) -> Optional[str]:
    """zip 파일에서 dumpsys_meminfo_all을 찾아 SystemUI 섹션 추출

    Args:
        zip_path: zip 파일 경로
        process_name: 추출할 프로세스명

    Returns:
        SystemUI meminfo 텍스트 (없으면 None)
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        # dumpsys_meminfo_all 파일 찾기
        meminfo_all_name = None
        for name in zf.namelist():
            if name.endswith("dumpsys_meminfo_all") or name == "dumpsys_meminfo_all":
                meminfo_all_name = name
                break

        if meminfo_all_name is None:
            return None

        # 파일 읽기 (인코딩 시도: utf-8 → euc-kr)
        raw = zf.read(meminfo_all_name)
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            content = raw.decode("euc-kr", errors="replace")

        return extract_process_section(content, process_name)


def process_version(
    version_data: VersionData,
    process_name: str = "com.android.systemui",
) -> VersionData:
    """한 버전의 모든 zip을 처리: 추출 → 파싱 → 평균 계산

    Args:
        version_data: 버전 데이터 (zip_files가 채워져 있어야 함)
        process_name: 분석할 프로세스명

    Returns:
        parsed_results와 average가 채워진 VersionData
    """
    parser = MeminfoParser()

    for round_num, zip_path in version_data.zip_files:
        meminfo_text = extract_meminfo_from_zip(zip_path, process_name)
        if meminfo_text:
            result = parser.parse(meminfo_text)
            version_data.parsed_results.append(result)

    if version_data.parsed_results:
        version_data.average = average_meminfo_results(version_data.parsed_results)

    return version_data


def average_meminfo_results(results: list[MeminfoResult]) -> MeminfoResult:
    """여러 MeminfoResult의 평균을 계산

    Args:
        results: MeminfoResult 리스트 (보통 3개)

    Returns:
        평균값이 담긴 MeminfoResult
    """
    if len(results) == 1:
        return results[0]

    n = len(results)
    avg = MeminfoResult()
    avg.pid = results[0].pid
    avg.process_name = results[0].process_name

    # TOTAL 평균
    if all(r.total for r in results):
        from .parser.meminfo_parser import MemorySection
        avg.total = MemorySection(
            name="TOTAL",
            pss_total=sum(r.total.pss_total for r in results) // n,
            private_dirty=sum(r.total.private_dirty for r in results) // n,
            private_clean=sum(r.total.private_clean for r in results) // n,
            swap_pss_dirty=sum(r.total.swap_pss_dirty for r in results) // n,
            rss_total=sum(r.total.rss_total for r in results) // n,
            heap_size=sum(r.total.heap_size for r in results) // n,
            heap_alloc=sum(r.total.heap_alloc for r in results) // n,
            heap_free=sum(r.total.heap_free for r in results) // n,
        )

    # App Summary 평균
    if all(r.app_summary for r in results):
        from .parser.meminfo_parser import AppSummary
        avg.app_summary = AppSummary(
            java_heap_pss=sum(r.app_summary.java_heap_pss for r in results) // n,
            java_heap_rss=sum(r.app_summary.java_heap_rss for r in results) // n,
            native_heap_pss=sum(r.app_summary.native_heap_pss for r in results) // n,
            native_heap_rss=sum(r.app_summary.native_heap_rss for r in results) // n,
            code_pss=sum(r.app_summary.code_pss for r in results) // n,
            code_rss=sum(r.app_summary.code_rss for r in results) // n,
            stack_pss=sum(r.app_summary.stack_pss for r in results) // n,
            stack_rss=sum(r.app_summary.stack_rss for r in results) // n,
            graphics_pss=sum(r.app_summary.graphics_pss for r in results) // n,
            graphics_rss=sum(r.app_summary.graphics_rss for r in results) // n,
            private_other_pss=sum(r.app_summary.private_other_pss for r in results) // n,
            system_pss=sum(r.app_summary.system_pss for r in results) // n,
            total_pss=sum(r.app_summary.total_pss for r in results) // n,
            total_rss=sum(r.app_summary.total_rss for r in results) // n,
        )

    # Objects 평균
    if all(r.objects for r in results):
        from .parser.meminfo_parser import ObjectsInfo
        avg.objects = ObjectsInfo(
            views=sum(r.objects.views for r in results) // n,
            view_root_impl=sum(r.objects.view_root_impl for r in results) // n,
            app_contexts=sum(r.objects.app_contexts for r in results) // n,
            activities=sum(r.objects.activities for r in results) // n,
            assets=sum(r.objects.assets for r in results) // n,
            asset_managers=sum(r.objects.asset_managers for r in results) // n,
            local_binders=sum(r.objects.local_binders for r in results) // n,
            proxy_binders=sum(r.objects.proxy_binders for r in results) // n,
            parcel_memory=sum(r.objects.parcel_memory for r in results) // n,
            parcel_count=sum(r.objects.parcel_count for r in results) // n,
            death_recipients=sum(r.objects.death_recipients for r in results) // n,
            openssl_sockets=sum(r.objects.openssl_sockets for r in results) // n,
            webviews=sum(r.objects.webviews for r in results) // n,
        )

    # 섹션별 평균
    if all(r.sections for r in results):
        from .parser.meminfo_parser import MemorySection
        # 첫 번째 결과의 섹션 이름 기준
        section_names = [s.name for s in results[0].sections]
        for name in section_names:
            sections = []
            for r in results:
                sec = next((s for s in r.sections if s.name == name), None)
                if sec:
                    sections.append(sec)

            if len(sections) == n:
                avg_sec = MemorySection(
                    name=name,
                    pss_total=sum(s.pss_total for s in sections) // n,
                    private_dirty=sum(s.private_dirty for s in sections) // n,
                    private_clean=sum(s.private_clean for s in sections) // n,
                    swap_pss_dirty=sum(s.swap_pss_dirty for s in sections) // n,
                    rss_total=sum(s.rss_total for s in sections) // n,
                    heap_size=sum(s.heap_size for s in sections) // n,
                    heap_alloc=sum(s.heap_alloc for s in sections) // n,
                    heap_free=sum(s.heap_free for s in sections) // n,
                )
                avg.sections.append(avg_sec)

    # Database는 첫 번째 결과 그대로 사용 (평균 무의미)
    avg.databases = results[0].databases

    # SQL
    avg.sql_memory_used = sum(r.sql_memory_used for r in results) // n
    avg.sql_pagecache_overflow = sum(r.sql_pagecache_overflow for r in results) // n
    avg.sql_malloc_size = sum(r.sql_malloc_size for r in results) // n

    return avg

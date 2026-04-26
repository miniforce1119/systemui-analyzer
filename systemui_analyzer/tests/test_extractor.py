"""extractor 모듈 테스트

실제 zip 파일 구조를 시뮬레이션하여 테스트합니다.
"""

import zipfile
import tempfile
from pathlib import Path

from systemui_analyzer.extractor import (
    scan_download_folder,
    extract_process_section,
    extract_meminfo_from_zip,
    process_version,
    average_meminfo_results,
)
from systemui_analyzer.parser import MeminfoParser


# 테스트용 dumpsys_meminfo_all (SystemUI + 다른 프로세스)
SAMPLE_MEMINFO_ALL = """Applications Memory Usage (in Kilobytes):
Uptime: 123456789 Realtime: 123456789

** MEMINFO in pid 1000 [system_server] **
                   Pss  Private  Private  SwapPss      Rss     Heap     Heap     Heap
                 Total    Dirty    Clean      Dirty    Total     Size    Alloc     Free
                ------   ------   ------   ------   ------   ------   ------   ------
  Native Heap    50000    49000      500       10    52000    65536    50000    10000
        TOTAL   100000    80000    10000      100   120000    65536    50000    10000

 App Summary
                       Pss(KB)                        Rss(KB)
                        Total                          Total
                   ------                         ------
           Java Heap:    30000                         35000
         Native Heap:    50000                         52000
                Code:    10000                         20000
               Stack:      500                           600
            Graphics:     5000                          5000
       Private Other:     3000
              System:     1500
             TOTAL PSS:   100000              TOTAL RSS:   120000

 Objects
               Views:      100          ViewRootImpl:        2
         AppContexts:        5           Activities:        0
              Assets:        3        AssetManagers:        2
       Local Binders:      100       Proxy Binders:       50
       Parcel memory:       20         Parcel count:       10
    Death Recipients:       10      OpenSSL Sockets:        0
            WebViews:        0

** MEMINFO in pid 4603 [com.android.systemui] **
                   Pss  Private  Private  SwapPss      Rss     Heap     Heap     Heap
                 Total    Dirty    Clean      Dirty    Total     Size    Alloc     Free
                ------   ------   ------   ------   ------   ------   ------   ------
  Native Heap    15234    15100      120       45    16800    32768    16234     8534
  Dalvik Heap    22456    22300      100       30    24000    40960    24456     8504
 Dalvik Other     3456     3400       50        0     4000
        Stack      512      512        0        0      600
     .so mmap     8234      400     5200       20    15000
    .art mmap     3456     3200      100       10     5000
   EGL mtrack     8192     8192        0        0     8192
  GL mtrack    12288    12288        0        0    12288
    Unknown     2345     2200      100       15     3000
        TOTAL    84163    68492    12298      120   105780    73728    40690    17038

 App Summary
                       Pss(KB)                        Rss(KB)
                        Total                          Total
                   ------                         ------
           Java Heap:    25856                         29000
         Native Heap:    15234                         16800
                Code:    11380                         30000
               Stack:      512                           600
            Graphics:    20480                         20480
       Private Other:     7015
              System:     3686
             TOTAL PSS:    84163              TOTAL RSS:   105780

 Objects
               Views:      456          ViewRootImpl:        3
         AppContexts:       12           Activities:        0
              Assets:       15        AssetManagers:        5
       Local Binders:      234       Proxy Binders:       89
       Parcel memory:       56         Parcel count:       34
    Death Recipients:       23      OpenSSL Sockets:        0
            WebViews:        0

 SQL
         MEMORY_USED:      345
  PAGECACHE_OVERFLOW:       12          MALLOC_SIZE:       62

 DATABASES
      pgsz     dbsz   Lookaside(b)          cache  Dbname
         4       48             32         2/16/4  /data/user_de/0/com.android.systemui/databases/notification_log.db

** MEMINFO in pid 5188 [com.sec.android.app.launcher] **
                   Pss  Private  Private  SwapPss      Rss     Heap     Heap     Heap
                 Total    Dirty    Clean      Dirty    Total     Size    Alloc     Free
                ------   ------   ------   ------   ------   ------   ------   ------
  Native Heap    20000    19000      500       10    22000    40000    20000     8000
        TOTAL    60000    50000     5000       50    70000    40000    20000     8000
"""


def _create_test_zip(tmp_dir: Path, filename: str, meminfo_content: str) -> Path:
    """테스트용 zip 파일 생성"""
    zip_path = tmp_dir / filename
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("dumpsys_meminfo_all", meminfo_content)
        zf.writestr("dumpsys_meminfo", "Total RSS by process:\n  100000K: system\n")
        zf.writestr("boot_stat", "boot completed")
    return zip_path


def test_scan_download_folder():
    """다운로드 폴더 스캔 + 버전 자동 분류 테스트"""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # 버전 A: 3회 테스트
        _create_test_zip(tmp_path, "S948NKSU2AZDD_ram_000_20260421_220306.zip", "test")
        _create_test_zip(tmp_path, "S948NKSU2AZDD_ram_001_20260421_221430.zip", "test")
        _create_test_zip(tmp_path, "S948NKSU2AZDD_ram_002_20260421_222500.zip", "test")

        # 버전 B: 3회 테스트
        _create_test_zip(tmp_path, "S948NKSU2AZDE_ram_000_20260422_224025.zip", "test")
        _create_test_zip(tmp_path, "S948NKSU2AZDE_ram_001_20260422_225149.zip", "test")
        _create_test_zip(tmp_path, "S948NKSU2AZDE_ram_002_20260422_230313.zip", "test")

        # png, rom, crdownload는 무시되어야 함
        (tmp_path / "S948NKSU2AZDE_ram_000_20260422_224025.png").touch()
        (tmp_path / "S948NKSU2AZDE_rom_000_20260422_224004.zip").touch()
        (tmp_path / "확인되지 않음 170786.crdownload").touch()

        versions = scan_download_folder(tmp)

        assert len(versions) == 2
        assert "S948NKSU2AZDD" in versions
        assert "S948NKSU2AZDE" in versions
        assert len(versions["S948NKSU2AZDD"].zip_files) == 3
        assert len(versions["S948NKSU2AZDE"].zip_files) == 3

        # 회차 순 정렬 확인
        rounds = [r for r, _ in versions["S948NKSU2AZDD"].zip_files]
        assert rounds == [0, 1, 2]


def test_extract_process_section():
    """dumpsys_meminfo_all에서 SystemUI 섹션 추출 테스트"""
    section = extract_process_section(SAMPLE_MEMINFO_ALL, "com.android.systemui")

    assert section is not None
    assert "pid 4603" in section
    assert "com.android.systemui" in section
    assert "84163" in section  # TOTAL PSS
    assert "system_server" not in section
    assert "app.launcher" not in section


def test_extract_process_section_not_found():
    """존재하지 않는 프로세스 추출 시 None 반환"""
    section = extract_process_section(SAMPLE_MEMINFO_ALL, "com.nonexistent.app")
    assert section is None


def test_extract_meminfo_from_zip():
    """zip에서 SystemUI meminfo 추출 테스트"""
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = _create_test_zip(
            Path(tmp), "test.zip", SAMPLE_MEMINFO_ALL
        )
        section = extract_meminfo_from_zip(zip_path)

        assert section is not None
        assert "com.android.systemui" in section
        assert "84163" in section


def test_process_version_full_pipeline():
    """전체 파이프라인 테스트: zip → 추출 → 파싱 → 평균"""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # 동일한 데이터로 3회차 zip 생성
        for i in range(3):
            _create_test_zip(
                tmp_path,
                f"S948NKSU2AZDD_ram_{i:03d}_20260421_22{i:02d}00.zip",
                SAMPLE_MEMINFO_ALL,
            )

        versions = scan_download_folder(tmp)
        version_data = versions["S948NKSU2AZDD"]

        result = process_version(version_data)

        assert len(result.parsed_results) == 3
        assert result.average is not None
        assert result.average.total_pss_kb == 84163  # 동일 데이터이므로 평균도 같음
        assert result.average.process_name == "com.android.systemui"
        assert result.average.objects.views == 456


def test_average_meminfo_results():
    """평균 계산 테스트"""
    parser = MeminfoParser()

    # 약간 다른 데이터 생성 (PSS만 변경)
    content1 = SAMPLE_MEMINFO_ALL
    content2 = SAMPLE_MEMINFO_ALL.replace("84163", "84165").replace("25856", "25858")

    section1 = extract_process_section(content1, "com.android.systemui")
    section2 = extract_process_section(content2, "com.android.systemui")

    result1 = parser.parse(section1)
    result2 = parser.parse(section2)

    avg = average_meminfo_results([result1, result2])

    assert avg.process_name == "com.android.systemui"
    # 평균값 확인 (정수 나눗셈)
    assert avg.app_summary.java_heap_pss == (25856 + 25858) // 2

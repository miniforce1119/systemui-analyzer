"""dumpsys meminfo 파서 테스트"""

import os
from pathlib import Path

from systemui_analyzer.parser import MeminfoParser

SAMPLE_DIR = Path(__file__).parent / "sample_data"


def test_parse_normal():
    parser = MeminfoParser()
    result = parser.parse_file(str(SAMPLE_DIR / "meminfo_normal.txt"))

    assert result.pid == 1234
    assert result.process_name == "com.android.systemui"
    assert result.total_pss_kb == 84163
    assert result.total_rss_kb == 105780

    # App Summary
    assert result.app_summary is not None
    assert result.app_summary.java_heap_pss == 25856
    assert result.app_summary.native_heap_pss == 15234
    assert result.app_summary.graphics_pss == 20480

    # Objects
    assert result.objects is not None
    assert result.objects.views == 456
    assert result.objects.activities == 0
    assert result.objects.local_binders == 234

    # Sections
    section_names = [s.name for s in result.sections]
    assert "Native Heap" in section_names
    assert "Dalvik Heap" in section_names
    assert "GL mtrack" in section_names

    native = next(s for s in result.sections if s.name == "Native Heap")
    assert native.pss_total == 15234
    assert native.heap_size == 32768

    # Databases
    assert len(result.databases) == 3


def test_parse_regression():
    parser = MeminfoParser()
    result = parser.parse_file(str(SAMPLE_DIR / "meminfo_regression.txt"))

    assert result.total_pss_kb == 125937
    assert result.objects.views == 823
    assert result.objects.activities == 2
    assert len(result.databases) == 4


def test_to_dict():
    parser = MeminfoParser()
    result = parser.parse_file(str(SAMPLE_DIR / "meminfo_normal.txt"))
    d = result.to_dict()

    assert d["pid"] == 1234
    assert d["process"] == "com.android.systemui"
    assert d["total_pss_kb"] == 84163
    assert "app_summary" in d
    assert "sections" in d
    assert "objects" in d
    assert "databases" in d


if __name__ == "__main__":
    test_parse_normal()
    test_parse_regression()
    test_to_dict()
    print("All parser tests passed!")

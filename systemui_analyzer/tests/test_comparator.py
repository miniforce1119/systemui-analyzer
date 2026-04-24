"""비교 분석기 테스트"""

from pathlib import Path

from systemui_analyzer.parser import MeminfoParser
from systemui_analyzer.analyzer import MeminfoComparator

SAMPLE_DIR = Path(__file__).parent / "sample_data"


def test_compare():
    parser = MeminfoParser()
    baseline = parser.parse_file(str(SAMPLE_DIR / "meminfo_normal.txt"))
    regression = parser.parse_file(str(SAMPLE_DIR / "meminfo_regression.txt"))

    comparator = MeminfoComparator()
    result = comparator.compare(baseline, regression)

    # 전체 PSS 증가 확인
    assert result.total_pss_diff is not None
    assert result.total_pss_diff.diff > 0  # regression이 더 크다
    assert result.total_pss_diff.diff == 125937 - 84163  # 41774 KB

    # 심각도가 critical이어야 함 (30MB 이상 증가)
    assert result.severity == "critical"

    # Top contributors가 있어야 함
    assert len(result.top_contributors) > 0
    # Java Heap (App Summary)이 가장 큰 증가 원인
    assert result.top_contributors[0].name == "Java Heap"

    # Objects 비교
    views_diff = next(d for d in result.object_diffs if d.name == "Views")
    assert views_diff.diff == 823 - 456  # 367
    assert views_diff.severity == "warning"  # 100개 이상

    activities_diff = next(d for d in result.object_diffs if d.name == "Activities")
    assert activities_diff.diff == 2  # 0 → 2

    # 새 DB 감지
    assert len(result.new_databases) == 1
    assert "lease_cache.db" in result.new_databases[0].db_name


def test_compare_to_dict():
    parser = MeminfoParser()
    baseline = parser.parse_file(str(SAMPLE_DIR / "meminfo_normal.txt"))
    regression = parser.parse_file(str(SAMPLE_DIR / "meminfo_regression.txt"))

    comparator = MeminfoComparator()
    result = comparator.compare(baseline, regression)
    d = result.to_dict()

    assert "total_pss" in d
    assert d["total_pss"]["diff_kb"] == 41774
    assert "top_contributors" in d
    assert d["overall_severity"] == "critical"
    assert "new_databases" in d


if __name__ == "__main__":
    test_compare()
    test_compare_to_dict()
    print("All comparator tests passed!")

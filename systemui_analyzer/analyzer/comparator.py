"""
정상/문제 버전 meminfo 비교 분석 모듈

두 meminfo 스냅샷을 비교하여 변화량, 증가율, 주요 변화 지점을 식별합니다.
"""

from dataclasses import dataclass, field
from typing import Optional

from ..parser.meminfo_parser import MeminfoResult


@dataclass
class DiffEntry:
    """개별 지표의 변화량"""
    name: str
    baseline: int
    regression: int
    diff: int
    diff_percent: float
    severity: str = "info"  # info, warning, critical

    @property
    def increased(self) -> bool:
        return self.diff > 0


@dataclass
class ComparisonResult:
    """비교 분석 전체 결과"""
    # 전체 요약
    total_pss_diff: Optional[DiffEntry] = None
    total_rss_diff: Optional[DiffEntry] = None

    # App Summary 비교
    summary_diffs: list = field(default_factory=list)

    # 섹션별 비교
    section_diffs: list = field(default_factory=list)

    # Objects 비교
    object_diffs: list = field(default_factory=list)

    # Database 변화
    new_databases: list = field(default_factory=list)
    removed_databases: list = field(default_factory=list)

    # 분석 요약
    top_contributors: list = field(default_factory=list)
    severity: str = "info"  # info, warning, critical

    def get_critical_changes(self) -> list:
        """critical/warning 수준의 변화만 반환"""
        changes = []
        for d in self.section_diffs:
            if d.severity in ("critical", "warning"):
                changes.append(d)
        for d in self.summary_diffs:
            if d.severity in ("critical", "warning"):
                changes.append(d)
        for d in self.object_diffs:
            if d.severity in ("critical", "warning"):
                changes.append(d)
        return changes

    def to_dict(self) -> dict:
        """LLM 입력용 딕셔너리"""
        result = {}

        if self.total_pss_diff:
            result["total_pss"] = {
                "baseline": self.total_pss_diff.baseline,
                "regression": self.total_pss_diff.regression,
                "diff_kb": self.total_pss_diff.diff,
                "diff_percent": round(self.total_pss_diff.diff_percent, 1),
                "severity": self.total_pss_diff.severity,
            }

        if self.total_rss_diff:
            result["total_rss"] = {
                "baseline": self.total_rss_diff.baseline,
                "regression": self.total_rss_diff.regression,
                "diff_kb": self.total_rss_diff.diff,
                "diff_percent": round(self.total_rss_diff.diff_percent, 1),
                "severity": self.total_rss_diff.severity,
            }

        result["top_contributors"] = [
            {
                "name": d.name,
                "diff_kb": d.diff,
                "diff_percent": round(d.diff_percent, 1),
                "severity": d.severity,
            }
            for d in self.top_contributors
        ]

        result["section_diffs"] = [
            {
                "name": d.name,
                "baseline": d.baseline,
                "regression": d.regression,
                "diff_kb": d.diff,
                "diff_percent": round(d.diff_percent, 1),
                "severity": d.severity,
            }
            for d in self.section_diffs
            if d.diff != 0
        ]

        result["object_diffs"] = [
            {
                "name": d.name,
                "baseline": d.baseline,
                "regression": d.regression,
                "diff": d.diff,
                "severity": d.severity,
            }
            for d in self.object_diffs
            if d.diff != 0
        ]

        if self.new_databases:
            result["new_databases"] = [db.db_name for db in self.new_databases]

        result["overall_severity"] = self.severity

        return result


class MeminfoComparator:
    """두 meminfo 스냅샷을 비교 분석"""

    # 심각도 판정 임계값 (KB)
    THRESHOLDS = {
        "pss_critical": 30000,    # 30MB 이상 증가 → critical
        "pss_warning": 10000,     # 10MB 이상 증가 → warning
        "section_critical": 10000, # 개별 섹션 10MB 이상 증가
        "section_warning": 3000,   # 개별 섹션 3MB 이상 증가
        "objects_warning": 100,    # Views 등 100개 이상 증가
        "heap_usage_critical": 85, # Heap 사용률 85% 이상
    }

    def compare(
        self, baseline: MeminfoResult, regression: MeminfoResult
    ) -> ComparisonResult:
        """baseline(정상)과 regression(문제) 스냅샷 비교"""
        result = ComparisonResult()

        # 1. 전체 PSS/RSS 비교
        result.total_pss_diff = self._make_diff(
            "Total PSS", baseline.total_pss_kb, regression.total_pss_kb
        )
        result.total_rss_diff = self._make_diff(
            "Total RSS", baseline.total_rss_kb, regression.total_rss_kb
        )

        # 전체 심각도 판정
        if result.total_pss_diff.diff >= self.THRESHOLDS["pss_critical"]:
            result.total_pss_diff.severity = "critical"
            result.severity = "critical"
        elif result.total_pss_diff.diff >= self.THRESHOLDS["pss_warning"]:
            result.total_pss_diff.severity = "warning"
            result.severity = "warning"

        # 2. App Summary 비교
        if baseline.app_summary and regression.app_summary:
            result.summary_diffs = self._compare_app_summary(
                baseline.app_summary, regression.app_summary
            )

        # 3. 섹션별 비교
        result.section_diffs = self._compare_sections(
            baseline.sections, regression.sections
        )

        # 4. Objects 비교
        if baseline.objects and regression.objects:
            result.object_diffs = self._compare_objects(
                baseline.objects, regression.objects
            )

        # 5. Database 비교
        baseline_dbs = {db.db_name for db in baseline.databases}
        regression_dbs = {db.db_name for db in regression.databases}
        new_db_names = regression_dbs - baseline_dbs
        removed_db_names = baseline_dbs - regression_dbs
        result.new_databases = [
            db for db in regression.databases if db.db_name in new_db_names
        ]
        result.removed_databases = [
            db for db in baseline.databases if db.db_name in removed_db_names
        ]

        # 6. Top contributors 계산 (App Summary 우선, 중복 이름 제거)
        all_diffs = result.summary_diffs + result.section_diffs
        seen_names = set()
        unique_diffs = []
        for d in sorted(all_diffs, key=lambda x: x.diff, reverse=True):
            if d.diff > 0 and d.name not in seen_names:
                seen_names.add(d.name)
                unique_diffs.append(d)
        result.top_contributors = unique_diffs[:5]

        return result

    def _make_diff(self, name: str, baseline: int, regression: int) -> DiffEntry:
        diff = regression - baseline
        pct = (diff / baseline * 100) if baseline > 0 else 0
        return DiffEntry(
            name=name,
            baseline=baseline,
            regression=regression,
            diff=diff,
            diff_percent=pct,
        )

    def _classify_section_severity(self, diff: int) -> str:
        if diff >= self.THRESHOLDS["section_critical"]:
            return "critical"
        elif diff >= self.THRESHOLDS["section_warning"]:
            return "warning"
        return "info"

    def _compare_app_summary(self, baseline, regression) -> list:
        fields = [
            ("Java Heap", "java_heap_pss"),
            ("Native Heap", "native_heap_pss"),
            ("Code", "code_pss"),
            ("Stack", "stack_pss"),
            ("Graphics", "graphics_pss"),
            ("Private Other", "private_other_pss"),
            ("System", "system_pss"),
        ]
        diffs = []
        for name, attr in fields:
            b = getattr(baseline, attr)
            r = getattr(regression, attr)
            entry = self._make_diff(name, b, r)
            entry.severity = self._classify_section_severity(entry.diff)
            diffs.append(entry)
        return diffs

    def _compare_sections(self, baseline_sections, regression_sections) -> list:
        baseline_map = {s.name: s for s in baseline_sections}
        regression_map = {s.name: s for s in regression_sections}
        all_names = list(dict.fromkeys(
            [s.name for s in baseline_sections] + [s.name for s in regression_sections]
        ))

        diffs = []
        for name in all_names:
            b = baseline_map.get(name)
            r = regression_map.get(name)
            b_pss = b.pss_total if b else 0
            r_pss = r.pss_total if r else 0
            entry = self._make_diff(name, b_pss, r_pss)
            entry.severity = self._classify_section_severity(entry.diff)
            diffs.append(entry)
        return diffs

    def _compare_objects(self, baseline, regression) -> list:
        fields = [
            ("Views", "views"),
            ("ViewRootImpl", "view_root_impl"),
            ("AppContexts", "app_contexts"),
            ("Activities", "activities"),
            ("Local Binders", "local_binders"),
            ("Proxy Binders", "proxy_binders"),
            ("Parcel memory", "parcel_memory"),
            ("Death Recipients", "death_recipients"),
            ("WebViews", "webviews"),
        ]
        diffs = []
        for name, attr in fields:
            b = getattr(baseline, attr)
            r = getattr(regression, attr)
            entry = self._make_diff(name, b, r)
            if entry.diff >= self.THRESHOLDS["objects_warning"]:
                entry.severity = "warning"
            diffs.append(entry)
        return diffs

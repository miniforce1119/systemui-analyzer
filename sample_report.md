# SystemUI Memory Regression 분석 보고서

**생성일시:** 2026-04-24 13:07:54  
**Baseline:** systemui_analyzer/tests/sample_data/meminfo_normal.txt  
**Regression:** systemui_analyzer/tests/sample_data/meminfo_regression.txt  
**심각도:** 🔴 Critical

---

## 1. 전체 요약

| 지표 | Baseline | Regression | 변화량 | 변화율 |
|------|----------|------------|--------|--------|
| **Total PSS** | 84,163 KB | 125,937 KB | +41,774 KB | +49.6% |
| **Total RSS** | 105,780 KB | 155,524 KB | +49,744 KB | +47.0% |

## 2. 메모리 증가 주요 원인 (Top Contributors)

| 순위 | 영역 | 증가량 (KB) | 증가율 | 심각도 |
|------|------|-------------|--------|--------|
| 1 | Java Heap | +18,734 | +72.5% | 🔴 Critical |
| 2 | Dalvik Heap | +16,456 | +73.3% | 🔴 Critical |
| 3 | Native Heap | +10,656 | +69.9% | 🔴 Critical |
| 4 | Graphics | +6,144 | +30.0% | 🟡 Warning |
| 5 | GL mtrack | +6,144 | +50.0% | 🟡 Warning |

## 3. 메모리 섹션별 상세 비교

| 섹션 | Baseline (KB) | Regression (KB) | 변화량 | 심각도 |
|------|---------------|-----------------|--------|--------|
| Native Heap | 15,234 | 25,890 | +10,656 | 🔴 Critical |
| Dalvik Heap | 22,456 | 38,912 | +16,456 | 🔴 Critical |
| Dalvik Other | 3,456 | 5,678 | +2,222 | 🟢 Info |
| Stack | 512 | 768 | +256 | 🟢 Info |
| .so mmap | 8,234 | 10,234 | +2,000 | 🟢 Info |
| .art mmap | 3,456 | 5,678 | +2,222 | 🟢 Info |
| Other mmap | 567 | 890 | +323 | 🟢 Info |
| GL mtrack | 12,288 | 18,432 | +6,144 | 🟡 Warning |
| Unknown | 2,345 | 3,890 | +1,545 | 🟢 Info |

## 4. Objects 변화

| 항목 | Baseline | Regression | 변화량 | 심각도 |
|------|----------|------------|--------|--------|
| Views | 456 | 823 | +367 | 🟡 Warning |
| ViewRootImpl | 3 | 5 | +2 | 🟢 Info |
| AppContexts | 12 | 18 | +6 | 🟢 Info |
| Activities | 0 | 2 | +2 | 🟢 Info |
| Local Binders | 234 | 312 | +78 | 🟢 Info |
| Proxy Binders | 89 | 145 | +56 | 🟢 Info |
| Parcel memory | 56 | 89 | +33 | 🟢 Info |
| Death Recipients | 23 | 34 | +11 | 🟢 Info |

## 5. 새로 추가된 데이터베이스

- `/data/user_de/0/com.android.systemui/databases/lease_cache.db` (size: 32 pages)

---
*이 보고서는 SystemUI Analyzer에 의해 자동 생성되었습니다.*
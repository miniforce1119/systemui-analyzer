# SystemUI Memory Regression 분석 보고서

**생성일시:** 2026-04-26 14:47:24  
**Baseline:** S948NKSU2AZDD (3회 평균)  
**Regression:** S948NKSU2AZDE (3회 평균)  
**심각도:** 🔴 Critical

---

## 1. 전체 요약

| 지표 | Baseline | Regression | 변화량 | 변화율 |
|------|----------|------------|--------|--------|
| **Total PSS** | 76,009 KB | 109,700 KB | +33,691 KB | +44.3% |
| **Total RSS** | 95,011 KB | 137,125 KB | +42,114 KB | +44.3% |

## 2. 메모리 증가 주요 원인 (Top Contributors)

| 순위 | 영역 | 증가량 (KB) | 증가율 | 심각도 |
|------|------|-------------|--------|--------|
| 1 | Java Heap | +18,915 | +73.5% | 🔴 Critical |
| 2 | Dalvik Heap | +16,447 | +73.5% | 🔴 Critical |
| 3 | Native Heap | +10,787 | +70.8% | 🔴 Critical |
| 4 | Graphics | +6,274 | +30.7% | 🟡 Warning |
| 5 | GL mtrack | +6,164 | +50.4% | 🟡 Warning |

## 3. 메모리 섹션별 상세 비교

| 섹션 | Baseline (KB) | Regression (KB) | 변화량 | 심각도 |
|------|---------------|-----------------|--------|--------|
| Native Heap | 15,232 | 26,019 | +10,787 | 🔴 Critical |
| Dalvik Heap | 22,372 | 38,819 | +16,447 | 🔴 Critical |
| Dalvik Other | 3,425 | 3,328 | -97 | 🟢 Info |
| Stack | 610 | 521 | -89 | 🟢 Info |
| .so mmap | 8,143 | 8,353 | +210 | 🟢 Info |
| .art mmap | 3,433 | 3,457 | +24 | 🟢 Info |
| EGL mtrack | 8,211 | 8,320 | +109 | 🟢 Info |
| GL mtrack | 12,238 | 18,402 | +6,164 | 🟡 Warning |
| Unknown | 2,343 | 2,478 | +135 | 🟢 Info |

## 4. Objects 변화

| 항목 | Baseline | Regression | 변화량 | 심각도 |
|------|----------|------------|--------|--------|
| Views | 456 | 900 | +444 | 🟡 Warning |
| Activities | 0 | 2 | +2 | 🟢 Info |
| Local Binders | 225 | 199 | -26 | 🟢 Info |
| Proxy Binders | 174 | 101 | -73 | 🟢 Info |

---
*이 보고서는 SystemUI Analyzer에 의해 자동 생성되었습니다.*
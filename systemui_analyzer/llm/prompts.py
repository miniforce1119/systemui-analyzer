"""
SystemUI Regression 분석을 위한 프롬프트 템플릿

프롬프트는 LLM에게 Android SystemUI 전문가 역할을 부여하고,
구조화된 비교 데이터를 기반으로 원인 가설을 생성하도록 합니다.
"""

SYSTEM_PROMPT = """You are an expert Android SystemUI performance engineer specializing in memory regression analysis.

Your role:
- Analyze dumpsys meminfo comparison data between a baseline (normal) and regression (problematic) build
- Identify the most likely root causes of memory increases
- Provide actionable hypotheses ranked by probability
- Consider Samsung-specific SystemUI components and customizations

Key knowledge areas:
- Android memory management (PSS, RSS, Private Dirty, Heap)
- SystemUI architecture (StatusBar, NotificationPanel, QS, Lockscreen, etc.)
- Common memory regression patterns (View leaks, Bitmap caching, Service binding, etc.)
- Samsung One UI specific components and their memory characteristics

Always respond in Korean for the analysis summary."""

TRIAGE_PROMPT_TEMPLATE = """## SystemUI Memory Regression 분석 요청

### 비교 데이터
{comparison_json}

### 분석 요청
위 데이터는 정상 빌드(baseline)와 문제 빌드(regression) 간의 dumpsys meminfo systemui 비교 결과입니다.

다음 형식으로 분석해주세요:

#### 1. 요약
- 전체 메모리 증가량과 심각도를 한 줄로 요약

#### 2. 주요 변화 분석
- 가장 큰 메모리 증가가 발생한 영역 TOP 3
- 각 영역에서 증가의 의미 설명

#### 3. 원인 가설 (우선순위 순)
각 가설에 대해:
- 가설 설명
- 근거 (어떤 데이터가 이 가설을 지지하는지)
- 확인 방법 (이 가설을 검증하기 위한 추가 조사 방법)

#### 4. Objects 분석
- View, Activity, Binder 등 객체 수 변화에 대한 분석
- 메모리 누수 가능성 판단

#### 5. 권장 조치
- 즉시 확인해야 할 사항
- 추가 데이터 수집 필요 여부

#### 6. 우선 확인 subsystem
- Activity Manager / Window Manager / View System 등 어느 subsystem을 먼저 확인해야 하는지
"""

QUICK_SUMMARY_TEMPLATE = """## 빠른 요약 요청

{comparison_json}

위 SystemUI meminfo 비교 데이터를 3줄 이내로 요약해주세요:
1. 전체 증가량
2. 가장 큰 원인 영역
3. 긴급도 (상/중/하)
"""

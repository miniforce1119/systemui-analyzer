# 사내 포팅 가이드 (Cline 작업용)

> 이 문서는 사내 PC에서 Cline(AI 코딩 도구)이 포팅 작업을 수행할 때 참고하는 가이드입니다.
> **Cline은 이 문서에 명시된 파일만 수정할 수 있습니다.**

---

## 1. 프로젝트 개요

이 프로젝트는 사외 GitHub에서 개발된 **SystemUI Memory Regression 분석 자동화 도구**입니다.
사내 환경에 포팅하여 실제 regression 시스템 데이터로 분석을 수행하는 것이 목표입니다.

### 현재 동작하는 기능

```bash
# 다운로드 폴더의 zip 파일들을 자동 분석
python -m systemui_analyzer analyze ./downloads --baseline AZDD --target AZDE -o report.md
```

이 명령이 하는 일:
1. zip 파일 스캔 → 버전별 분류 (extractor.py)
2. zip 해제 → dumpsys_meminfo_all에서 SystemUI 섹션 추출 (extractor.py)
3. meminfo 파싱 → 3회 평균 계산 (parser/meminfo_parser.py)
4. baseline vs target 비교 분석 (analyzer/comparator.py)
5. Markdown 보고서 생성 (report/generator.py)
6. (선택) LLM 원인 분석 (llm/)

---

## 2. 수정 가능 파일 목록

### 반드시 수정해야 하는 파일

| # | 파일 | 수정 내용 | 이유 |
|---|------|-----------|------|
| 1 | `systemui_analyzer/llm/base.py` | `InternalProvider` 클래스 구현 | 사내 Agent Builder API 연동 |
| 2 | `systemui_analyzer/llm/prompts.py` | 프롬프트 튜닝 (선택) | 사내 모델 성능에 맞게 조정 |

### 실제 데이터 테스트 후 수정이 필요할 수 있는 파일

| # | 파일 | 수정 가능 상황 | 조건 |
|---|------|----------------|------|
| 3 | `systemui_analyzer/parser/meminfo_parser.py` | 삼성 기기 전용 필드가 파싱 안 될 때 | 파싱 에러 발생 시에만 |
| 4 | `systemui_analyzer/extractor.py` | zip 내부 파일명/경로가 다를 때 | 추출 실패 시에만 |
| 5 | `systemui_analyzer/analyzer/comparator.py` | 임계값 조정 (THRESHOLDS) | 사내 기준과 다를 때만 |

### 절대 수정하지 말 것

| 파일 | 이유 |
|------|------|
| `systemui_analyzer/cli.py` | 이미 완성됨. 사외 GitHub와 동기화 유지 필요 |
| `systemui_analyzer/report/generator.py` | 이미 완성됨. 보고서 포맷 변경은 사외에서 수행 |
| `systemui_analyzer/__init__.py` | 건드릴 이유 없음 |
| `systemui_analyzer/__main__.py` | 건드릴 이유 없음 |
| `systemui_analyzer/tests/*` | 테스트는 사외에서 관리 |
| `create_test_data.py` | 테스트용, 사내에서 불필요 |
| `conversation.md` | 대화 로그, 사외에서만 관리 |
| `conversation_raw.md` | 대화 로그, 사외에서만 관리 |

---

## 3. 포팅 작업 상세

### Task 1: 실제 데이터로 기본 파이프라인 테스트 (LLM 없이)

**목적:** 파서와 비교 분석기가 실제 회사 데이터에서 정상 동작하는지 확인

**절차:**
```bash
# 1. regression 시스템에서 두 버전의 zip 파일을 다운로드
#    (Download All 버튼으로 ram 파일 받기)
#    예: S948NKSU2AZDD_ram_000_*.zip ~ S948NKSU2AZDD_ram_002_*.zip
#        S948NKSU2AZDE_ram_000_*.zip ~ S948NKSU2AZDE_ram_002_*.zip

# 2. 다운로드한 zip 파일들을 하나의 폴더에 모음
#    예: C:\분석\downloads\

# 3. 버전 목록 확인
python -m systemui_analyzer analyze C:\분석\downloads --list

# 4. 비교 분석 실행
python -m systemui_analyzer analyze C:\분석\downloads --baseline AZDD --target AZDE -o report.md
```

**예상 결과:** `report.md` 파일이 생성되며, 메모리 비교 표가 포함됨

**문제 발생 시:**
- "zip 파일을 찾을 수 없습니다" → 파일명 패턴 확인. `extractor.py`의 `_FILENAME_PATTERN` 수정 필요할 수 있음
- "데이터를 추출할 수 없습니다" → zip 내부에 `dumpsys_meminfo_all` 파일이 있는지 확인. 경로가 다르면 `extractor.py`의 `extract_meminfo_from_zip()` 수정
- 파싱 값이 0으로 나옴 → 실제 meminfo 포맷이 다를 수 있음. `parser/meminfo_parser.py` 수정 필요

---

### Task 2: InternalProvider 구현 (Agent Builder 연동)

**수정 파일:** `systemui_analyzer/llm/base.py`

**수정 위치:** `InternalProvider` 클래스 (102번째 줄 부근)

**현재 상태:**
```python
class InternalProvider(LLMProvider):
    def generate(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        raise NotImplementedError(...)
```

**수정 목표:** Agent Builder의 API 엔드포인트를 호출하도록 구현

**구현 가이드:**
```python
class InternalProvider(LLMProvider):
    """사내 Agent Builder API Provider"""

    def __init__(self, endpoint: str, api_key: str = "", model: str = ""):
        self.endpoint = endpoint  # Agent Builder Flow의 API URL
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        import requests

        # Agent Builder API 호출
        # ※ 아래 payload 형식은 Agent Builder의 실제 API 스펙에 맞게 수정하세요
        payload = {
            "input_value": prompt,
            # system_prompt가 있으면 함께 전달
        }

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        resp = requests.post(
            self.endpoint,
            json=payload,
            headers=headers,
            timeout=120,
        )
        resp.raise_for_status()
        result = resp.json()

        return LLMResponse(
            content=result["output"],  # Agent Builder 응답 형식에 맞게 수정
            model=self.model or "agent-builder",
        )

    def get_model_name(self) -> str:
        return self.model or "agent-builder"
```

**확인해야 할 정보 (사내에서):**
1. Agent Builder Flow의 API 엔드포인트 URL
2. 인증 방식 (API key? 토큰? 사내 SSO?)
3. 요청/응답 JSON 형식

**테스트:**
```bash
python -m systemui_analyzer analyze C:\분석\downloads \
  --baseline AZDD --target AZDE \
  --llm internal --api-key YOUR_KEY \
  -o report_with_ai.md
```

> 참고: `--llm internal` 옵션을 사용하려면 `cli.py`의 `_run_llm_analysis()`에
> InternalProvider 분기를 추가해야 합니다. 이 수정은 예외적으로 `cli.py`에서
> `_run_llm_analysis` 함수 내부의 provider 선택 부분만 수정 허용합니다.

**cli.py 허용 수정 범위 (이 부분만):**
```python
# _run_llm_analysis 함수 내부, provider 선택 부분에 추가:
elif args.llm == "internal":
    from .llm.base import InternalProvider
    provider = InternalProvider(
        endpoint="사내_엔드포인트_URL",
        api_key=api_key
    )
```

그리고 `main()` 함수의 `--llm` choices에 `"internal"` 추가:
```python
# analyze_parser와 compare_parser 모두:
choices=["claude", "openai", "internal"]
```

---

### Task 3: 프롬프트 튜닝 (선택)

**수정 파일:** `systemui_analyzer/llm/prompts.py`

**수정이 필요한 경우:**
- 사내 LLM 모델이 긴 프롬프트를 잘 처리하지 못할 때
- 응답 형식이 일관적이지 않을 때
- 삼성 특화 분석 항목을 추가하고 싶을 때

**튜닝 방향:**
1. `SYSTEM_PROMPT` — 역할 설명을 간결하게 줄이기 (사내 모델 성능이 낮으면)
2. `TRIAGE_PROMPT_TEMPLATE` — 분석 항목을 줄이거나, 응답 형식을 더 구체적으로 지정
3. 삼성 특화 컴포넌트 목록 추가 (예: One UI 관련 프로세스)

---

## 4. Agent Builder Flow 설계 가이드

Cline 작업 범위는 아니지만, Agent Builder에서 Flow를 만들 때 참고:

```
[Input 노드]
  - comparison_json (Python에서 전달)
      │
      ▼
[Prompt Template 노드]
  - System: prompts.py의 SYSTEM_PROMPT 내용 복붙
  - User: prompts.py의 TRIAGE_PROMPT_TEMPLATE 내용 복붙
  - {comparison_json} 변수에 Input 바인딩
      │
      ▼
[LLM 노드]
  - 사내 승인 모델 선택
      │
      ├──→ [Output 노드] → Python으로 결과 반환
      │
      └──→ [메일 노드] → 팀 공유 메일 발송 (선택)
```

---

## 5. 검증 체크리스트

포팅 완료 후 아래를 모두 확인:

- [ ] `python -m systemui_analyzer analyze ./downloads --list` → 버전 목록 정상 출력
- [ ] `python -m systemui_analyzer analyze ./downloads --baseline A --target B` → 보고서 생성
- [ ] 보고서의 Total PSS 값이 regression 시스템 UI에서 보이는 값과 일치
- [ ] 보고서의 3회 평균이 regression 시스템의 평균값과 일치 (±1KB 오차 허용)
- [ ] (Task 2 완료 시) `--llm internal` 옵션으로 AI 분석 결과가 보고서에 포함

---

## 6. 파일 구조 참고

```
systemui_analyzer/
├── __init__.py              ← 수정 금지
├── __main__.py              ← 수정 금지
├── cli.py                   ← _run_llm_analysis 내 provider 분기만 수정 허용
├── extractor.py             ← 추출 실패 시에만 수정
├── parser/
│   ├── __init__.py          ← 수정 금지
│   └── meminfo_parser.py    ← 파싱 에러 시에만 수정
├── analyzer/
│   ├── __init__.py          ← 수정 금지
│   └── comparator.py        ← 임계값 조정만 수정 허용
├── llm/
│   ├── __init__.py          ← 수정 금지
│   ├── base.py              ← ★ InternalProvider 구현 (필수)
│   ├── prompts.py           ← 프롬프트 튜닝 (선택)
│   └── analyzer.py          ← 수정 금지
├── report/
│   ├── __init__.py          ← 수정 금지
│   └── generator.py         ← 수정 금지
├── rag/
│   └── __init__.py          ← 수정 금지 (향후 확장)
└── tests/                   ← 수정 금지
```

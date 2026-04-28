# SystemUI Analyzer 프로젝트 대화 로그

> AI(Claude)와의 대화를 통해 프로젝트를 설계하고 구현한 과정을 기록합니다.
> 날짜: 2026-04-24

---

## 1. 프로젝트 시작 - 제안서 분석

**사용자:**
SystemUI Automation 폴더를 만들었어 새로운 작업을 할꺼야. 여기 안에 내가 회사에서 해야할 제안서가 있어 안드로이드 기반 작업인데 회사의 업무를 자동화하고 최적화하는 내용인데 Android는 회사 밖 생태계도 같으니까 너가 잘 알꺼라고 생각해 이 내용으로 프로젝트 진행을 너랑 다 해서 github 통해서 관련 내용을 회사 안으로 가져가서 회사내 특성에 맞게 포팅하는 작업을 할꺼야 문서 내용을 보고 어떻게 진행하는게 좋을지 같이 논의해보자

**AI:**
제안서(`AI_Level4_과제제안서_심사양식_최종.docx`)를 분석하여 다음과 같이 정리:

### 제안서 핵심 내용
- **과제명:** Generative AI 기반 Android SystemUI Memory & Performance Regression 원인 분석 자동화 및 협업 지원 체계 구축
- **일정:** 2026년 3월 ~ 8월 (6개월), 4명 협업
- **Pain Point:**
  - bugreport 로그가 15-30MB로 방대하고, 1건 분석에 2-4시간 소요
  - 주 3-5회 Regression 발생 → 업무 시간의 30-50% 소모
  - 분석 결과가 개인에게 머물러 지식 공유 부족
- **핵심 기능 4가지:**
  1. 로그 전처리/구조화
  2. AI Agent 로그 분석
  3. 분석 보고서 자동 생성
  4. 유사 사례 DB (RAG)
- **6단계 일정:**
  1. 현업 분석 및 요구사항 정의 (2주)
  2. bugreport 전처리 로직 개발 (4주)
  3. AI Agent 분석 구조 설계 (4주)
  4. 로그 비교 분석 PoC (6주)
  5. 메일 자동화 및 협업 공유 (4주)
  6. 유사 사례 DB 구축 (6주)

### 프로젝트 진행 방안 제안

GitHub에서 오픈 개발 가능한 부분:
- bugreport 파서/전처리 모듈 (Python)
- AI Agent 프레임워크
- 보고서 생성 엔진
- 벡터 DB 연동 모듈

회사 내 포팅 필요 부분:
- 실제 bugreport 데이터 연동
- 사내 메일 시스템 연동
- 사내 승인 LLM 모델 연동

---

## 2. 회사 환경 공유 및 논의

**사용자:**
1~2. 우리 회사 시스템에서는 systemui를 위해서 테스트 후 dumpsys meminfo systemui로 snapshot을 찍어서 별도 txt 파일로 저장해서 보관하고 그리고 테스트 시점의 캡쳐화면 정보도 보여주고 그리고 dumpstate 파일도 보관해서 그런데 dumpstate 파일에는 삼성 로그들이 많이 포함되어 있는 상태야 그래서 android 원래 생태계보다 더 많은 로그가 보인다고 생각하면 되는거야.
3. 사내에서 쓰는 모델은 성능이 좀 떨어져 그런데 구조는 너가 제안한 방식으로 가면 좋겠어
4. Agent builder는 langflow 기반으로 만든 nocode Agent 개발 툴이야 내가 지원한 과정이 바로 이걸 이용해서 잘 사용하는 사람을 양성하는 과정이야 agent builder에는 사내 시스템이 여러개 포함되어 있어 예를 들면 사내 메일 보내기 시스템, 사내 데이터 접근 component 등이야

**AI:**
이해한 내용 정리:

1. **데이터 구조:**
   - `dumpsys meminfo systemui` → 별도 txt 파일로 저장
   - 테스트 시점 스크린샷 캡처
   - dumpstate 파일 (삼성 독자 로그 포함)

2. **LLM 전략:**
   - 외부에서는 고성능 모델(Claude/GPT)로 개발 & 검증
   - 사내에서는 사내 모델로 교체 → 모델 추상화 레이어 필수

3. **Agent Builder:**
   - Langflow 기반 노코드 도구
   - 사내 시스템(메일, 데이터 접근 등) 컴포넌트 내장

### 역할 분담 결정

| GitHub에서 만들 것 | Agent Builder에서 할 것 (사내) |
|---|---|
| bugreport/dumpstate 파서 (Python) | 사내 메일 발송 연동 |
| dumpsys meminfo 파서 & 비교 분석기 | 사내 데이터 접근 연동 |
| LLM 프롬프트 & 분석 로직 | 노코드 워크플로우 조립 |
| RAG/벡터DB 구조 | 사내 모델 연동 |
| 보고서 생성 템플릿 | - |

**시작점:** `dumpsys meminfo systemui` 파서부터 시작하기로 결정

---

## 3. 프로젝트 구현

**사용자:**
일단 한번 만들어볼까? 너가 만들어주면 그걸 가지고 논의해보자

**AI:**
다음 구조로 프로젝트 생성:

```
systemui_analyzer/
├── cli.py                    # CLI 엔트리포인트
├── parser/
│   └── meminfo_parser.py     # dumpsys meminfo 파서
├── analyzer/
│   └── comparator.py         # 정상/문제 비교 분석기
├── llm/
│   ├── base.py               # LLM Provider 추상화 (Claude, OpenAI, 사내모델)
│   ├── prompts.py            # SystemUI 전문가 프롬프트 템플릿
│   └── analyzer.py           # LLM 기반 triage 분석
├── report/
│   └── generator.py          # Markdown 보고서 생성
├── rag/                      # (6단계 구현 예정)
└── tests/
    ├── sample_data/          # 정상/Regression 샘플 데이터
    ├── test_parser.py
    └── test_comparator.py
```

### 구현 과정에서 수정한 버그들

1. **Views 파싱 버그:** "WebViews"가 "Views" 정규식에도 매칭되어 값이 0으로 덮어씌워지는 문제 → negative lookbehind `(?<!Web)Views:\s*(\d+)` 로 수정
2. **Top Contributors 중복:** App Summary와 Section에서 같은 이름(Native Heap)이 중복 등장 → 중복 제거 로직 추가
3. **Windows 인코딩:** 이모지(🔴 등)가 cp949 코덱에서 출력 실패 → stdout.reconfigure(encoding="utf-8") 추가

### CLI 사용법
```bash
# 단일 파일 파싱
python -m systemui_analyzer parse meminfo.txt

# 두 파일 비교 (보고서 생성)
python -m systemui_analyzer compare baseline.txt regression.txt -o report.md

# LLM 분석 포함
python -m systemui_analyzer compare baseline.txt regression.txt --llm claude --api-key YOUR_KEY
```

---

## 4. LLM 역할 논의

**사용자:**
LLM이 하는 역할은 두 문서의 파싱된 결과를 보고 비교 분석해서 리포트 만드는거야?

**AI:**
아니요, 역할이 구분되어 있음:

| 단계 | 담당 | 역할 |
|------|------|------|
| 파싱/비교/수치 계산 | Python 코드 | **What** - 뭐가 변했는지 |
| 원인 추론/가설 생성 | LLM | **Why** - 왜 변했는지 |
| 보고서 포맷팅 | Python 코드 | 위 둘을 합쳐서 보고서로 |

LLM의 핵심 역할은 수치를 보고 SystemUI 도메인 지식 기반으로 **원인 가설을 생성**하는 것. 예: "View 367개 증가 + Activity 0→2 = Activity Leak 가능성" 같은 추론.

---

## 5. 분석 보고서 저장/공유 방식 논의

**사용자:**
내가 사내에 문서 생성 파이프라인을 구축했거든 md -> mkdocs로 만드는 방식이야 이 분석 보고서가 매일 regression test가 발생하면 이상 없음 혹은 분석 보고서 리포트가 발생할꺼니까 이걸 문서 생성 파이프라인을 통해서 github pages에 자동 반영하면 어떨까?

**AI:**
mkdocs + GitHub Pages 방식 적합. 다만 매일 누적되는 리포트 특성에 맞게 보강 제안:

1. **대시보드 페이지** - 최근 상태 한눈에
2. **메모리 추이 트렌드** - 서서히 증가하는 Regression 감지
3. **상태 뱃지** - 팀원이 접속 없이도 상태 확인

**사용자:**
이미 regression test system에 트렌드 그래프는 다 보이거든 그러니까 나는 분석 내용을 저장하고 보여주는 방식이 적절할 것 같은데 어떤 내용이 포함되면 좋을지 한번더 생각해줘

**AI:**
제안서 pain point로 돌아가서, 보고서가 **"분석 과정의 기록"**이 되어야 한다고 제안:

### 보고서 포함 내용

```
1. 자동 생성 영역 (코드 + LLM)
   ├── 테스트 정보       - 날짜, 빌드 버전, 테스트 시나리오
   ├── 수치 비교         - meminfo 비교 결과
   ├── AI 원인 가설      - LLM이 제시한 가설 목록
   └── 유사 과거 사례    - RAG로 찾은 비슷한 케이스 링크

2. 분석자 기록 영역 (Human-in-the-loop)
   ├── 실제 원인         - AI 가설 중 맞은 것, 또는 실제 원인
   ├── 원인 코드 변경    - 문제를 유발한 commit/CL 정보
   ├── 해결 조치         - 어떻게 수정했는지
   ├── 추가 확인 데이터  - hprof, systrace 등 뭘 더 봤는지
   └── 카테고리 태그     - "View Leak", "Bitmap Cache" 등
```

핵심: AI 초안 + 분석자 기록이 쌓이면 → 팀의 분석 노하우 DB가 됨

---

## 6. GitHub 연동

**사용자:**
사내에 github가 별도로 존재하는데 지금은 사외 github를 사용해서 한번 해보자

**AI:**
- GitHub 계정: miniforce1119 (head1119@gmail.com)
- 레포 생성: https://github.com/miniforce1119/systemui-analyzer.git
- remote 연결 완료

---

## 7. 사내 포팅 아키텍처 논의

> 날짜: 2026-04-18 (집에서 이어서 작업)

**사용자:**
비교 분석은 rule base(무료)이고, diff 발생 시 AI로 원인 추론하는 건 API 방식이 되는 거지? 회사에서는 Agent Builder로 생성된 Agent를 통해서 사용하면 제약 없이 사용 가능한데, 사내로 가져갈 때 어떤 차이점이 발생하는지 체크하고 싶어.

**AI:**
외부(API)와 사내(Agent Builder) 방식의 차이를 정리:

| 항목 | 외부 (현재) | 사내 (Agent Builder) |
|---|---|---|
| 호출 방식 | Python → REST API 직접 호출 | Python → Agent Builder 엔드포인트 호출 |
| 인증 | API Key (유료, 건당 과금) | 사내 인증 (무료, 제약 없음) |
| LLM 선택 | 코드에서 모델 지정 | Agent Builder 안에서 설정됨 |
| 프롬프트 관리 | Python 코드 안에 하드코딩 | Agent Builder 노드에서 관리 |

사내 포팅 시나리오 2가지:
- **시나리오 A:** Agent Builder를 LLM 호출 도구로만 사용 → `InternalProvider`만 구현
- **시나리오 B:** Agent Builder가 전체 워크플로우(LLM+메일+DB) 관리 → Python은 파싱 라이브러리 역할만

제안서 목적이 "Agent Builder를 잘 쓰는 사람 양성"이므로 **시나리오 B를 추천**.

**사용자:**
Agent Builder의 API 엔드포인트 사용은 이미 있고, 다수의 경험이 있어서 어렵지 않아.

**AI:**
최종 확정 구조:

```
Python (파싱·비교)  ──JSON──→  Agent Builder (LLM·메일·DB)
   GitHub에서 개발                사내에서 조립
```

- `comparator.to_dict()` → JSON 출력은 이미 구현 완료
- GitHub에서는 `parser/`와 `analyzer/`의 완성도를 높이는 것에 집중
- `llm/`과 `report/`는 외부 테스트/데모용으로 유지, 사내에서는 Agent Builder가 대체

### 모듈별 역할 확정

| 모듈 | GitHub 유지 | 사내에서 대체 |
|---|---|---|
| `parser/` | ✅ 핵심. 그대로 사용 | - |
| `analyzer/comparator.py` | ✅ 핵심. 그대로 사용 | - |
| `llm/` | 외부 테스트용 유지 | Agent Builder LLM 노드 |
| `report/` | 외부 테스트용 유지 | Agent Builder 출력 노드 |
| `rag/` | 구조 설계만 | Agent Builder + 사내 벡터DB |

---

## 8. 자동화 파이프라인 설계 논의

> 날짜: 2026-04-18

**사용자:**
궁극적 목표는 새 버전 등록 시 자동으로 분석하는 것. 현재 수동 워크플로우:

1. regression 시스템 접속 → 과제 선택 → 버전 목록 확인
2. 기준 모델과 최신 버전 비교 → 특이점 확인
3. 이상 있으면 최근 2개 비교 → 트렌드 확인
4. 이상 계속되면 5개 전체 트렌드 → 튀는 버전 찾기
5. 튀는 버전 전후 상세 비교 → 원인 파악

이 과정에서 사람의 판단·선택 행위가 많이 들어감. 이걸 자동화하고 싶음.

**AI:**
이건 단순 자동화가 아니라 "자율 판단 에이전트". 각 단계 결과를 보고 다음 행동을 결정하는 구조. Agent Builder 과제 취지에 정확히 부합.

판단 1~3은 rule base로 충분하고, AI는 최종 원인 추론에만 집중시키는 게 현실적 (사내 모델 성능 고려).

### 데이터 수집 방식 확인

**사용자:**
regression 시스템은 웹에서 다운로드 버튼으로 txt 파일을 받는 방식. 버전별로 3회 테스트 결과(dumpsys meminfo 전체)와 bugreport가 포함되어 있음. bugreport는 문제 해결 시 참고용.

**AI:**
API가 없으므로 데이터 수집은 브라우저 자동화(Selenium/Playwright)가 필요.

### 자동화 파이프라인 전체 흐름 (확정)

```
[1단계] 브라우저 자동화
        - regression 시스템 로그인
        - 과제 선택 → 버전 목록 가져오기
        - 필요한 버전의 meminfo txt 다운로드
              ↓
[2단계] Python rule base
        - 파싱 → 비교 → 이상 판별
              ↓
        이상 없으면 → "정상" 기록 → 끝
        이상 있으면 ↓
              ↓
[1단계 재진입] 추가 버전 다운로드 (트렌드 비교용)
              ↓
[2단계 재진입] N개 트렌드 비교 → 튀는 버전 전후 비교
              ↓
[3단계] LLM 원인 추론 (Agent Builder)
        - 필요시 bugreport도 참고자료로 전달
              ↓
[4단계] 리포트 생성 + 메일 알림
```

핵심: 1단계와 2단계가 판단 결과에 따라 왔다 갔다 함. 이것이 단순 크롤링이 아니라 "에이전트"인 이유.

### 기술 스택 결정

**브라우저 자동화: Playwright 확정**
- 사용자가 이미 사내 사이트 로그인 자동화를 Playwright로 운영 중
- regression 시스템 UI가 수년간 변경 없이 유지보수 수준 → 브라우저 자동화가 깨질 리스크 낮음
- 기존 Playwright 코드 패턴을 재활용하여 regression 시스템 데이터 수집 모듈 개발 예정

### 3회 테스트 데이터 처리

**사용자:** regression 시스템 UI에서는 3회 평균값을 보여주고 있음.

**AI:** 기존 시스템과 일관성 유지를 위해 3회 평균값 사용으로 결정.

parser에 평균 계산 기능 추가 필요:
```
3개 파일 각각 파싱 → 평균 MeminfoResult 1개 → comparator에 전달
```

---

## 9. 자동화 범위 결정 — Phase A / B 분리

> 날짜: 2026-04-18

**사용자:**
처음부터 끝까지 완전 자동화할지, 사람이 판단·파일 수집까지 하고 그 뒤부터 자동화할지 갈등. 완전 자동화하면 사람이 관심을 안 갖게 될 것 같음.

**AI:**
단계적 접근 제안. 사용자 동의.

### Phase A (우선): 반자동 — 사람이 판단, 분석·문서화는 자동

```
[사람] 시스템 접속 → 버전 비교 → 문제 발견 → 파일 다운로드
   ↓
[자동] 파싱 → 비교 분석 → LLM 원인 추론 → 보고서 생성
```

- 시간 소모의 핵심(건당 2~4시간)인 분석·문서화를 먼저 자동화
- 사람이 매번 시스템에 들어가므로 관심 유지 자연스러움
- 과제 기간 내 확실히 완성 가능

### Phase B (여유 시): 완전 자동 — 새 버전 감지부터 알림까지

```
[자동] 새 버전 감지 → 다운로드 → 비교 → 이상 판별 → 알림/리포트
[사람] 알림 확인 → 필요시 추가 조치
```

- Phase A가 안정적으로 동작한 뒤에 진행
- 앞에 Playwright를 붙이는 확장 형태
- 관심 유지는 주간 요약 리포트 + 이상 시 즉시 알림으로 해결

---

## 10. 실제 데이터 구조 확인 — zip 내부 및 파일 역할 정정

> 날짜: 2026-04-18

### regression 시스템 다운로드 구조

```
zip 파일 (버전당, 테스트 회차당 1개)
├── dump/                        ← bugreport 상세 로그
├── boot_stat
├── dumpsys_activity
├── dumpsys_meminfo_all          ← ★ 각 프로세스별 상세 meminfo (parser 입력)
├── dumpsys_meminfo              ← 전체 프로세스 간략 PSS 목록 (순위 확인용)
├── features
├── property
├── system_floating_feature      ← 삼성 전용
├── vendor_floating_feature      ← 삼성 전용
└── proc_meminfo                 ← 커널 레벨 메모리 정보
```

### 파일 역할 정정

초기에 혼동이 있었으나, 실제 스크린샷 확인 후 정정:

| 파일 | 실제 내용 | 용도 |
|---|---|---|
| `dumpsys_meminfo` | 전체 프로세스 간략 PSS 목록 (프로세스별 1줄 요약) | SystemUI의 전체 순위, 상대적 점유율 확인 |
| `dumpsys_meminfo_all` | 각 프로세스별 상세 meminfo (Pss, App Summary, Objects 등) | **★ parser의 실제 입력 파일** |

### parser 추가 필요 사항

1. **프로세스 추출 기능**: `dumpsys_meminfo_all`에서 `com.android.systemui` 섹션만 추출하는 기능 필요 (현재는 단일 프로세스 파일만 처리)
2. **TOTAL SWAP RSS** 파싱 추가 (실제 데이터에 존재)
3. **Dalvik Details** 파싱 추가 (실제 데이터에 존재)
4. 삼성 전용 Objects 항목은 없음 확인 — 표준 AOSP 포맷과 동일

### 분석 파이프라인 (확정)

```
dumpsys_meminfo_all → SystemUI 섹션 추출 → parser → comparator → LLM
dumpsys_meminfo     → 전체 순위에서 SystemUI 위치 확인 (보조 정보)
```

---

## 11. Phase A 핵심 파이프라인 구현 및 E2E 테스트

> 날짜: 2026-04-18 (집에서 작업)

### 구현 완료 항목

**새 모듈: `extractor.py`**
- `scan_download_folder()` — 다운로드 폴더 스캔, 파일명 패턴(`{버전}_ram_{회차}_{날짜}_{시간}.zip`)으로 버전/회차 자동 분류
- `extract_process_section()` — `dumpsys_meminfo_all`에서 특정 프로세스(SystemUI) 섹션만 추출
- `extract_meminfo_from_zip()` — zip 열기 → `dumpsys_meminfo_all` 찾기 → SystemUI 추출
- `process_version()` — 한 버전의 3회 zip 전체 처리 (추출→파싱→평균)
- `average_meminfo_results()` — 3회 MeminfoResult 평균 계산

**CLI `analyze` 명령 추가 (`cli.py`)**
```bash
# 버전 목록 확인
python -m systemui_analyzer analyze ./downloads --list

# 두 버전 비교 (축약 버전명 지원)
python -m systemui_analyzer analyze ./downloads --baseline AZDD --target AZDE

# 보고서 파일 저장
python -m systemui_analyzer analyze ./downloads --baseline AZDD --target AZDE -o report.md

# LLM 분석 포함
python -m systemui_analyzer analyze ./downloads --baseline AZDD --target AZDE --llm claude --api-key KEY
```

**테스트: `test_extractor.py` (6개 케이스, 전체 11개 통과)**

### E2E 테스트 실행

회사 다운로드 구조와 동일한 테스트 데이터(2버전 × 3회차)를 생성하여 전체 파이프라인을 검증:

```
테스트 데이터 생성 (create_test_data.py)
    ↓
python -m systemui_analyzer analyze ./test_downloads --baseline AZDD --target AZDE -o report.md
    ↓
zip 자동 분류 → 압축 해제 → SystemUI 추출 → 3회 평균 → 비교 분석 → MD 보고서
    ↓
Documents 레포(https://github.com/miniforce1119/Documents)에 push
    ↓
GitHub Pages 자동 배포 → https://miniforce1119.github.io/Documents/
```

### 생성된 보고서 결과 (테스트 데이터 기준)

| 지표 | Baseline (AZDD) | Target (AZDE) | 변화 |
|---|---|---|---|
| Total PSS | 76,009 KB | 109,700 KB | +44.3% 🔴 |
| Top 1 | Java Heap | +18,915 KB | +73.5% 🔴 |
| Top 2 | Dalvik Heap | +16,447 KB | +73.5% 🔴 |
| Top 3 | Native Heap | +10,787 KB | +70.8% 🔴 |
| Views | 456 → 900 | +444 | 🟡 |

**참고:** 이번 테스트는 Documents 레포에 올렸지만, 이후 분석 보고서는 **별도 전용 저장소**를 만들어서 관리할 예정.

### 보고서 시각화 강화

보고서에 Mermaid 차트 + AI 분석 시뮬레이션을 추가:

- **막대 차트 (xychart):** Total PSS/RSS 비교, 섹션별 Baseline vs Regression
- **파이 차트:** 메모리 증가 기여도 비율
- **AI 원인 가설:** 가설 3개 (Activity Leak, Bitmap 캐시, 알림 누수) + 신뢰도·근거·확인방법
- **조사 흐름도:** Mermaid 플로우차트로 분석 절차 시각화
- **분석자 기록 영역:** Human-in-the-loop (담당자가 실제 원인·조치 기록)
- mkdocs.yml에 Mermaid 렌더링 설정 추가

모두 Mermaid 코드블록으로 마크다운만으로 렌더링 — 별도 이미지 관리 불필요.

배포 확인: https://miniforce1119.github.io/Documents/ → 분석 → SystemUI Memory Regression

---

## 12. Agent Builder 포팅 구조 상세 논의

> 날짜: 2026-04-27

**사용자:**
회사 데이터를 다운로드 받아서 회사에서 테스트 해보고 싶어. Agent Builder를 사용해야 할 부분이 원인 분석인데, 이 부분이 어떻게 포팅되는지 자세히 설명해줘.

**AI:**
현재 코드에서 LLM 호출 지점과 Agent Builder 포팅 매핑을 상세 설명:

**데이터 흐름:**
```
Python comparator.to_dict() → JSON → Agent Builder Input → LLM → 원인 가설 반환
```

**포팅 대상 매핑:**
| 현재 코드 | Agent Builder에서 대체 |
|---|---|
| `prompts.py` → `SYSTEM_PROMPT` | LLM 노드의 System Message |
| `prompts.py` → `TRIAGE_PROMPT_TEMPLATE` | Prompt Template 노드 |
| `analyzer.py` → `provider.generate()` | Agent Builder 내부 LLM 호출 |
| 사내 메일 발송 | Agent Builder 메일 노드 |

**InternalProvider 구현 가이드 제공:**
- Agent Builder의 API 엔드포인트를 `requests.post()`로 호출하는 구조
- `base.py`의 `InternalProvider` 클래스만 구현하면 연동 완료

---

## 13. 사내 포팅 가이드 및 Cline 작업 규칙 생성

> 날짜: 2026-04-28

**사용자:**
회사 안에서 작업해볼 거야. 회사에는 Cline 기반이거든. 포팅 가이드를 Cline이 수행할 수 있도록 만들어줘. 꼭 수정해야 하는 파일 리스트를 만들고 Cline이 임의로 파일 수정하지 못하도록 조치하고 싶어.

**AI:**
2개 파일 생성:

**1. PORTING_GUIDE.md** — 포팅 작업 전체 가이드
- Task 1: 실제 데이터로 기본 파이프라인 테스트 (LLM 없이)
- Task 2: InternalProvider 구현 (Agent Builder 연동)
- Task 3: 프롬프트 튜닝 (선택)
- 검증 체크리스트 포함

**2. .clinerules** — Cline 수정 권한 제어

수정 가능 파일 (화이트리스트):

| 구분 | 파일 | 수정 범위 |
|------|------|-----------|
| 필수 | `llm/base.py` | InternalProvider 구현 |
| 조건부 | `llm/prompts.py` | 사내 모델 맞춤 튜닝 |
| 조건부 | `parser/meminfo_parser.py` | 파싱 에러 시에만 |
| 조건부 | `extractor.py` | 추출 실패 시에만 |
| 조건부 | `analyzer/comparator.py` | 임계값 조정만 |
| 조건부 | `cli.py` | `--llm internal` 분기 추가만 |

그 외 모든 파일은 수정 금지.

---

## 14. Agent Builder 구성 논의 및 시각화 보고서 템플릿

> 날짜: 2026-04-28

**사용자:**
Agent Builder가 하는 역할과 component 구성을 설명해줘.

**AI:**
Python = "뭐가 변했는지(What)", Agent Builder = "왜 변했는지(Why) + 후속 액션"

Agent Builder Flow 구성:
```
Input(JSON) → Prompt Template → LLM → (메일 노드) → Response
```
- Input: Python comparator.to_dict()의 JSON
- Prompt Template: SYSTEM_PROMPT + TRIAGE_PROMPT_TEMPLATE
- LLM: 사내 승인 모델
- 메일: 나중에 추가

**사용자:**
Output Parser 꼭 써야 해?

**AI:** 필요 없음. LLM 응답이 이미 마크다운 텍스트라 Python에서 그대로 report.md에 삽입하면 됨.

**사용자:**
메일 노드까지 붙이면 Agent Builder를 두 번 호출해야 하는 거 아냐?

**AI:**
Agent Builder 호출 한 번에 LLM + 메일 다 처리하는 게 가장 깔끔함:
```
Input → Prompt → LLM → 메일 노드 → Response
```
Python은 응답 받아서 report.md + mkdocs만 처리.

**사용자:**
시각화 들어간 보고서 템플릿을 Cline에게 알려주고 싶어.

**AI:**
`report_template_visual.md` 생성. 포함된 시각화 요소:
- Mermaid xychart: Total PSS/RSS 비교, 섹션별 비교 막대 차트
- Mermaid pie: 메모리 증가 기여도 비율
- Mermaid flowchart: 조사 흐름도
- AI 가설 3개 (Activity Leak, Bitmap 캐시, Binder 누수) + 확인 명령어
- 조치 권고 테이블 (우선순위별)
- 분석자 기록 영역 (Human-in-the-loop)

---

## 다음 단계 (예정)

### Phase A (현재 집중)
- [x] parser: dumpsys_meminfo_all에서 특정 프로세스 섹션 추출 기능
- [x] parser 평균 계산 기능 (3회 테스트 → 평균 MeminfoResult)
- [x] CLI analyze 명령 (폴더 → 자동 분석 파이프라인)
- [x] E2E 테스트 및 문서 파이프라인 연동 검증
- [x] 보고서 시각화 (Mermaid 차트 + AI 분석 시뮬레이션)
- [ ] parser: TOTAL SWAP RSS 파싱 추가
- [ ] parser: Dalvik Details 파싱 추가
- [ ] comparator N개 트렌드 비교 기능
- [ ] 이상 판별 rule 정의 (임계값·기준 명확화)
- [ ] LLM 분석 실제 실행 및 프롬프트 튜닝
- [ ] 보고서 생성기에 Mermaid 차트 자동 삽입 기능 통합
- [ ] dumpstate 파서 개발 (삼성 추가 로그 포함)
- [ ] RAG / 벡터 DB 유사 사례 검색
- [ ] Agent Builder(Langflow) 연동용 컴포넌트 설계
- [ ] 분석 보고서 전용 저장소 생성

### Phase B (여유 시)
- [ ] 브라우저 자동화 모듈 — Playwright (regression 시스템 데이터 수집)
- [ ] 새 버전 감지 트리거 (webhook 또는 polling)
- [ ] 자동 알림 시스템 (이상 감지 시 메일 발송)

# SystemUI Analyzer 프로젝트 대화 로그

> AI(Claude)와의 대화를 통해 프로젝트를 설계하고 구현한 과정을 기록합니다.
> 날짜: 2026-04-24 ~

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
너가 지금 생각하는 방식은 두 버전의 자료를 비교하는 건 rule base라고 했어. 그래서 이건 무료인것 같고 diff가 발생시 데이터를 AI로 보내서 원인을 1차 추론하는 행위는 AI를 이용한다고 했잖아. 외부 AI를 사용할때 이 방식은 API 방식이 되는거지? 왜 물어보냐하면 회사에서는 Agent builder로 생성된 Agent를 통해서 사용하게되면 제약없이 사용가능하거든 이 방식이 사내로 가지고 갈때 어떤 차이점이 발생할 지 체크해보는 질문이야

**AI:**
현재 구조와 사내 포팅 시 차이를 정리:

현재 구조 (외부 = API 방식):
```
[Python 코드]                        [외부 AI]

meminfo 파싱 ──→ 비교 분석 ──→ diff 데이터(JSON) ──HTTP API──→ Claude/OpenAI
  (무료)           (무료)        (무료)              ↑              ↓
                                              API Key 필요     원인 가설 응답
                                              건당 과금         ↓
                                                          보고서에 삽입
```

사내 구조 (Agent Builder = Langflow 방식):
```
[Python 코드]                        [Agent Builder]

meminfo 파싱 ──→ 비교 분석 ──→ diff 데이터(JSON) ──???──→ Langflow Agent
  (무료)           (무료)        (무료)             ↑          ↓
                                              연동 방식이    사내 LLM 호출
                                              핵심 차이점    사내 메일 발송
                                                           사내 DB 저장
                                                           (전부 무료)
```

핵심 차이점:

| 항목 | 외부 (현재) | 사내 (Agent Builder) |
|---|---|---|
| 호출 방식 | Python → REST API 직접 호출 | Python → Agent Builder 엔드포인트 호출 |
| 인증 | API Key (유료) | 사내 인증 (SSO/토큰, 무료) |
| LLM 선택 | 코드에서 모델 지정 | Agent Builder 안에서 이미 설정됨 |
| 프롬프트 관리 | Python 코드 안에 하드코딩 | Agent Builder 노드에서 관리 가능 |

현재 `llm/base.py`에 이미 추상화가 되어있어서 사내 포팅 시나리오가 2가지:

**시나리오 A:** Agent Builder를 LLM 호출 도구로만 사용 → `InternalProvider` 하나만 구현하면 끝. Python 코드 변경 최소.

**시나리오 B:** Agent Builder가 전체 워크플로우(LLM+메일+DB) 관리 → Python은 파싱 라이브러리 역할만.

제안서 목적이 "Agent Builder를 잘 쓰는 사람 양성"이므로 시나리오 B를 추천.

이 경우 현재 Python 코드에서 꼭 필요한 것과 사내에서 대체될 것:

| 모듈 | GitHub 유지 | 사내에서 대체 |
|---|---|---|
| `parser/` | ✅ 핵심. 그대로 사용 | - |
| `analyzer/comparator.py` | ✅ 핵심. 그대로 사용 | - |
| `llm/` | 외부 테스트용 유지 | Agent Builder LLM 노드로 대체 |
| `report/` | 외부 테스트용 유지 | Agent Builder 출력 노드로 대체 |
| `rag/` | 구조 설계만 | Agent Builder + 사내 벡터DB |

**사용자:**
Agent builder의 API 엔드포인트 사용은 이미 있어 이미 나도 다수의 경험이 있어 그건 어렵지 않아.

**AI:**
그러면 사내 포팅은 깔끔하게 정리되네요.

확정된 구조:
```
Python (파싱·비교)  ──JSON──→  Agent Builder (LLM·메일·DB)
   GitHub에서 개발                사내에서 조립
```

Python 쪽에서 해줘야 할 것:
- `comparator.to_dict()` → JSON 출력 ← 이미 구현되어 있음
- Agent Builder 엔드포인트에 POST로 보내는 코드 한 줄 추가하면 끝

GitHub 코드에서 더 신경 쓸 부분:
- `parser/`와 `analyzer/`의 완성도를 높이는 것 (dumpstate 파서 등)
- LLM 프롬프트 튜닝 (외부 모델로 먼저 검증 → 사내 모델에 옮기기)
- RAG 구조 설계

---

## 8. 자동화 파이프라인 설계 논의

> 날짜: 2026-04-18

**사용자:**
내가 분석을 완전히 자동화하는 것도 목표로하기때문에 브라우저 자동화나 크롤링도 고려하고 있거든 그래서 너에게 우리 회사 regression system에 대해서 간략히 소개할께 우리 회사 regression 시스템을 접속하면 폰 과제별로 안정성을 입증한 offical 바이너리 리스트가 과제별로 보이거든 그래서 내가 결과를 보고 싶은 과제를 선택하면 하위 체크리스트 박스가 뜨는데 버전들이 쭉 보여 만약 5개가 있다고 하면 그걸 다 체크박스로 선택해서 compare를 누르면 5개의 버전에 대한 비교 분석이 되는거야 나는 주로 이 모델의 비교 대상인 모델의 진행 완료한 버전과 지금 진행하는 과제의 최신 버전을 비교하는 경우가 제일 많고 아니면 최근 메모리 트렌드를 보려고 최근 2개를 비교해보고 이상이 있으면 5개를 다 찍어서 트렌드를 보고 튀는 버전이 나오면 그 버전의 이전 버전과 튀는 버전을 비교해서 문제 현상을 파악하고 있어 일단 여기까지 설명을 들어보면 사람의 선택 행위가 굉장히 많이 들어가거든 근데 나의 궁극적인 목표는 새로운 버전이 등록되면 내가 했던 행동처럼 비교 모델과 비교해서 특이점이 없는지 그 다음 최신 트렌드와 비교해서 이상이 있는지 체크해보고 이상이 있으면 그 지점의 전후 버전을 찍어서 상세 비교하는 행위를 자동으로 진행하는 것을 목표로 하고 있어 이 부분에 대해서 의견을 줄래 뭔가 진행하지는 말고 의견을 듣고 싶어

**AI:**
이건 "자동화"가 아니라 "자율 판단 에이전트"입니다.

단순 자동화는 "정해진 순서대로 실행"하는 건데, 여기서 설명하신 건 각 단계의 결과를 보고 다음 행동을 결정하는 구조:

```
새 버전 등록
    ↓
[판단 1] 기준 모델과 비교 → 특이점 있나?
    ↓ 이상 없으면 끝
    ↓ 이상 있으면
[판단 2] 최근 2개 버전 비교 → 트렌드 정상인가?
    ↓ 이상 없으면 끝
    ↓ 이상 있으면
[판단 3] 최근 5개 전체 트렌드 → 튀는 버전 찾기
    ↓
[판단 4] 튀는 버전의 전후 비교 → 상세 원인 파악
```

Agent Builder 과제 취지에 정확히 부합. 판단 1~3은 rule base로 충분하고, AI는 최종 원인 추론에만 집중시키는 게 현실적 (사내 모델 성능 고려).

두 가지를 분리해서 생각해야 함:
- **A. 데이터 수집 (브라우저 자동화)** — regression 시스템에 API가 있는지가 핵심. 없으면 Selenium/Playwright.
- **B. 판단 로직 (핵심 가치)** — rule base + AI 혼합이 적절.

GitHub에서 집중할 것:
1. `comparator` 고도화 — N개 트렌드 비교 기능
2. "이상 판별" rule 정의 — 임계값·기준 명확화
3. LLM 프롬프트 튜닝

제일 먼저 확인할 것: regression 시스템 데이터를 API/DB로 직접 접근 가능한지. 이것에 따라 브라우저 자동화가 필요한지 아닌지 결정.

**사용자:**
comparator로 기준 모델 vs 최신 비교 -> 이렇게 비교하려면 각 버전별 dumpsys meminfo 자료를 다운로드 해야하지 않을까?

**AI:**
맞습니다. comparator가 비교하려면 각 버전의 meminfo 데이터가 로컬에 있어야 합니다.

데이터 수집 방식은 결국 3가지 중 하나:

| 방식 | 장점 | 단점 |
|---|---|---|
| A. API/DB 직접 접근 | 안정적, 빠름 | 권한 필요, API가 있어야 함 |
| B. 브라우저 자동화 | API 없어도 가능 | 깨지기 쉬움, 느림 |
| C. 파일 시스템 접근 | 가장 단순 | 서버 접근 권한 필요 |

regression 시스템에서 meminfo 데이터가 어떤 형태로 저장되어 있는지 확인 필요.

**사용자:**
웹 화면에서 다운로드 버튼이 있어서 txt 파일로 받을 수 있는 건지? -> 이 방식이야 3회 테스트해서 그 결과가 dumpsys meminfo 전체와 bugreport가 같이 포함되어 있어서 다운로드 가능해 bugreport는 문제 해결에 참고하라고 올려두는거야

**AI:**
그러면 구조가 명확해졌다. API가 없고 웹에서 다운로드 버튼을 눌러야 하니 데이터 수집은 브라우저 자동화로 다운로드하는 방식이 될 수밖에 없다.

자동화 파이프라인 전체 흐름:
```
[1단계] 브라우저 자동화 (Selenium/Playwright)
        - regression 시스템 로그인
        - 과제 선택 → 버전 목록 가져오기
        - 필요한 버전의 meminfo txt 다운로드
              ↓
[2단계] Python rule base (현재 GitHub에서 개발 중)
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

3회 테스트 데이터 처리 방식 질문 — meminfo가 버전당 3회분이면, comparator에 넣기 전에 어떤 값을 쓸지 정해야 함 (3회 평균 / 최대값 / 개별 비교).

**사용자:**
regression 시스템에서 보여주는 UI에서는 3회 평균값을 보여주고 있는것 같아

**AI:**
그러면 우리도 3회 평균값으로 가는 게 기존 시스템과 일관성이 맞겠다. parser에 평균 계산 기능 추가 필요:
```
다운로드한 파일 3개 → [parser] 각각 파싱 → [평균 계산] 3회 결과 → 평균 MeminfoResult 1개 → [comparator] 버전 간 비교
```

---

## 9. 기술 스택 및 브라우저 자동화

> 날짜: 2026-04-18

**사용자:**
regression system ux가 몇년째 똑같거든 depth 진입하는 방식도 똑같고 그냥 현상태 유지보수 정도로 보이거든 기능 추가도 없고 그래서 브라우저 자동화로 돌려도 크게 틀어질 일은 없을 것 같아

**AI:**
그럼 브라우저 자동화 리스크가 낮다는 거네요. 보통 브라우저 자동화의 가장 큰 문제가 UI 변경으로 깨지는 건데, 그 걱정이 없으면 충분히 실용적인 선택입니다.

기술 스택 선택 의견:

| 항목 | Selenium | Playwright |
|---|---|---|
| 안정성 | 오래됨, 검증됨 | 최신, MS 관리 |
| 속도 | 느린 편 | 빠름 (headless 최적화) |
| 대기 처리 | 수동 wait 관리 | auto-wait 내장 |
| 사내 환경 호환 | 어디서든 돌아감 | Python 3.8+ 필요 |
| 학습 자료 | 압도적으로 많음 | 상대적으로 적음 |

사내에서도 돌려야 하고, 비전공자 교육 과정과도 관련 있으니 Selenium이 무난. 다만 나중에 실제 구현할 때 결정해도 되는 부분.

**사용자:**
나 특정 사내 사이트 로긴 자동화를 playwright로 하나 돌려놓은게 있어

**AI:**
그러면 Playwright로 확정이네요. 이미 사내 사이트 로그인 자동화 경험이 있으니 regression 시스템도 같은 방식으로 확장하면 됩니다. 기술 스택 통일도 되고요.

---

## 10. 자동화 범위 결정 — Phase A / B 분리

> 날짜: 2026-04-18

**사용자:**
근데 내가 의견을 구하고 싶은건 그냥 처음 너와 얘기했듯이 사람이 특정 버전의 문제점까지 발견하고 필요한 파일 다운로드하고 그 뒤부터 자동화해서 문서화 하는 방식으로 할까 아니면 처음부터 끝까지 다 자동화할까 이런 갈등이 있어 왜냐하면 사람이 관심을 안가지면 안보게 될거 같고 내가 특정 주기로 한번씩 안보면 관심이 사라질 것 같고 그런 생각이 들거든. 너는 어떻게 생각해?

**AI:**
솔직하게 말씀드리면, 둘 다 하시는 게 맞습니다. 다만 순서와 역할이 다릅니다.

걱정하시는 포인트가 정확합니다. 완전 자동화의 함정:

> "자동으로 돌아가니까 안 봐도 되겠지" → 안 보게 됨 → 알림 와도 무시 → 결국 무용지물

이건 실제로 사내 모니터링 시스템에서 흔히 발생하는 문제. 대시보드 만들어놓고 아무도 안 보는 것과 같은 맥락.

단계적 접근 제안:

**Phase A (먼저): 반자동** — 사람이 판단, 뒤는 자동
```
[사람] 시스템 접속 → 버전 비교 → 문제 발견 → 파일 다운로드
        ↓
[자동] 파싱 → 비교 분석 → LLM 원인 추론 → 보고서 생성
```
이게 먼저인 이유:
- 지금 가장 시간 잡아먹는 건 분석·문서화 작업 (건당 2~4시간)
- 판단하고 파일 받는 건 10분이면 끝
- 투자 대비 효과가 가장 큰 구간을 먼저 자동화
- 사람이 매번 시스템에 들어가니까 관심도 유지됨

**Phase B (나중에): 완전 자동** — 알림 방식이 핵심
```
[자동] 새 버전 감지 → 다운로드 → 비교 → 이상 판별
        ↓
   이상 없으면 → 조용히 기록만
   이상 있으면 → 담당자에게 알림 + 요약 리포트
```
Phase A를 잘 만들어놓으면 Phase B는 그 앞에 Playwright를 붙이는 것일 뿐.

**사용자:**
그래 맞네. 단계를 나눠서 여유가 되면 Phase B도 해보면 되겠네. 그게 좋겠다

---

## 11. 실제 데이터 구조 확인 — zip 내부 및 파일 역할

> 날짜: 2026-04-18

**사용자:**
(regression 시스템 다운로드 화면 스크린샷 공유 — 버전별 RAM/ROM 파일 목록, 각각 zip과 png)
이게 덤프 화면이야

**AI:**
화면을 보니 구조가 파악됩니다:
```
Download
├── S948NKSU2AZDE (바이너리 버전)
│   ├── RAM
│   │   ├── *_ram_000_20260422_224025.png  (1.43 MB) ← 캡처 화면
│   │   ├── *_ram_000_20260422_224025.zip  (11.97 MB) ← dumpsys meminfo (1회차)
│   │   ├── *_ram_001_20260422_225149.png  (1.43 MB)
│   │   ├── *_ram_001_20260422_225149.zip  (11.75 MB) ← (2회차)
│   │   ├── *_ram_002_20260422_230313.png  (1.43 MB)
│   │   └── *_ram_002_20260422_230313.zip  (11.68 MB) ← (3회차)
│   └── ROM
│       └── *_rom_000_20260422_224004.zip  (426.69 KB)
├── S948NKSU2AZDG (다른 버전)
│   └── ...
```

ram_000, ram_001, ram_002 → 이게 3회 테스트. "Download all" 버튼도 있음.

**사용자:**
(zip 내부 파일 목록 스크린샷 — dump/, boot_stat, dumpsys_activity, dumpsys_meminfo_all, dumpsys_meminfo, features, property, system_floating_feature, vendor_floating_feature, proc_meminfo)
zip 파일 모습

**AI:**
깔끔하게 분리되어 있네요. parser 작업이 수월하겠습니다.

우리가 쓸 파일:

| 파일 | 용도 | 우선순위 |
|---|---|---|
| `dumpsys_meminfo` | SystemUI 메모리 분석 — 현재 parser가 처리하는 것 | 1순위 |
| `dumpsys_meminfo_all` | 전체 프로세스 비교 시 참고 | 2순위 |
| `proc_meminfo` | 시스템 전체 메모리 상태 | 참고용 |
| `dumpsys_activity` | Activity Leak 의심 시 확인 | LLM 분석 보조 |
| `dump/` | bugreport 상세 로그 | 심층 분석 시 |

(참고: 이 시점에서는 아직 dumpsys_meminfo와 dumpsys_meminfo_all의 역할을 혼동하고 있었음 — 다음 대화에서 정정됨)

**사용자:**
(meminfo systemui 상세 화면 스크린샷 — Pss Total, Private Dirty/Clean, SwapPss, Rss, Heap 테이블 + Dalvik Details + App Summary)
meminfo systemui

**AI:**
실제 데이터를 보여주셔서 좋습니다. 현재 parser의 샘플 데이터와 비교해보니 구조적으로 거의 동일. 현재 parser가 바로 처리 가능. 다만 실제 데이터에는 `TOTAL SWAP RSS`와 `Dalvik Details` 섹션이 있는데 현재 parser에 없으므로 나중에 보강 필요.

**사용자:**
혹시 dumpsys meminfo all 혹은 dumpsys meminfo에서 더 확인하고 싶은 내용이 있어?

**AI:**
몇 가지 확인 질문:
1. Objects 섹션에 삼성 전용 항목이 있나?
2. DATABASES 섹션에서 DB가 몇 개 보이는지?
3. dumpsys_meminfo_all은 모든 프로세스가 한 파일에 들어있는 건지?

**사용자:**
1. 없음
2. 뭘 물어보는지 모르겠음
3. dumpsys meminfo 파일은 진짜 dumpsys meminfo를 찍은거고 dumpsys meminfo all은 각 프로세스별 세부 PSS를 모아서 저장한 파일이야

**AI:**
2번은 잊어주세요, 중요하지 않습니다. 3번 정리:

| 파일 | 내용 |
|---|---|
| `dumpsys_meminfo` | 전체 프로세스 간략 PSS 목록 |
| `dumpsys_meminfo_all` | 각 프로세스별 상세 meminfo |

**사용자:**
(dumpsys_meminfo 전체 프로세스 간략 목록 스크린샷 — Total RSS by process, com.android.systemui 319,872K 등)
이게 dumpsys_meminfo 정보야 전체 프로세스 간략 정보 보이는거 있잖아. 내가 보여준 정보는 dumpsys meminfo all에서 systemui로 검색해서 해당 프로세스의 pss 정보만 보여준거야

**AI:**
아, 제가 헷갈렸네요. 정정합니다.

실제 구조:

| 파일 | 내용 |
|---|---|
| `dumpsys_meminfo` | 지금 스크린샷 — 전체 프로세스 간략 PSS 목록 |
| `dumpsys_meminfo_all` | 각 프로세스별 상세 meminfo (여기서 SystemUI를 찾아서 분석) |

즉 우리 parser가 처리해야 할 파일은 `dumpsys_meminfo_all`이었다. parser에 `dumpsys_meminfo_all`에서 특정 프로세스 섹션을 추출하는 기능이 추가로 필요.

분석 파이프라인:
```
dumpsys_meminfo_all → SystemUI 섹션 추출 → parser → comparator
dumpsys_meminfo     → 전체 순위에서 SystemUI 위치 확인 (보조 정보)
```

---

## 12. Phase A 핵심 파이프라인 구현

> 날짜: 2026-04-18

**사용자:**
(다운로드 폴더 스크린샷 — S948NKSU2AZDD_ram_000~002, S948NKSU2AZDE_ram_000~002 zip/png 파일들, .crdownload 파일 등)
내가 Download all을 선택해보니까 각 파일들이 다 다운로드 되거든 압축파일은 압축된 상태로 Phase A에서는 내가 여기까지 진행한다고 생각하고 너가 압축 파일 풀고 systemui pss 추출하고 뭐 이런 과정을 진행해주면 좋겠어

**AI:**
파일명 패턴 확인 후 바로 구현:

**새 모듈 `extractor.py` 생성:**
- `scan_download_folder()` — 다운로드 폴더 스캔, 파일명 패턴(`{버전}_ram_{회차}_{날짜}_{시간}.zip`)으로 버전/회차 자동 분류. png, rom, crdownload는 자동 무시.
- `extract_process_section()` — `dumpsys_meminfo_all`에서 특정 프로세스(SystemUI) 섹션만 추출
- `extract_meminfo_from_zip()` — zip 열기 → `dumpsys_meminfo_all` 찾기 → SystemUI 추출
- `process_version()` — 한 버전의 3회 zip 전체 처리 (추출→파싱→평균)
- `average_meminfo_results()` — 3회 MeminfoResult 평균 계산

**CLI에 `analyze` 명령 추가:**
```bash
# 버전 목록 확인
python -m systemui_analyzer analyze ./downloads --list

# 두 버전 비교 (축약 버전명 지원)
python -m systemui_analyzer analyze ./downloads --baseline AZDD --target AZDE

# 보고서 파일로 저장
python -m systemui_analyzer analyze ./downloads --baseline AZDD --target AZDE -o report.md
```

**테스트 6개 작성 (`test_extractor.py`), 전체 11개 통과.**

---

## 13. E2E 테스트 및 문서 파이프라인 연동

> 날짜: 2026-04-18

**사용자:**
너가 회사 다운로드 파일처럼 테스트 데이터를 똑같이 만들고 이를 테스트해서 그 결과가 md로 출력되면 나의 문서 파이프라인으로 올려주는 것까지 해보고 싶어 https://github.com/miniforce1119/Documents.git 여기가 나의 문서 시스템이야

**사용자:**
내가 이번 테스트만 이렇게 하고 나중에 분석 report는 별도로 저장소 만들고 진행할꺼야

**AI:**
테스트 데이터(2버전 × 3회차 zip) 생성 스크립트 `create_test_data.py` 작성. 정상 버전(S948NKSU2AZDD)과 regression 버전(S948NKSU2AZDE) 각각 3회차 zip 생성. 더미 파일(png, rom)도 포함.

analyze 명령 실행 결과:
```
=== 발견된 버전 (2개) ===
  S948NKSU2AZDD (3회 테스트: 0, 1, 2)
  S948NKSU2AZDE (3회 테스트: 0, 1, 2)

Baseline: S948NKSU2AZDD
Target:   S948NKSU2AZDE

[1/4] S948NKSU2AZDD 처리 중...
  → 3회 파싱 완료, 평균 PSS: 76,009 KB
[2/4] S948NKSU2AZDE 처리 중...
  → 3회 파싱 완료, 평균 PSS: 109,700 KB
[3/4] 비교 분석 중...
[4/4] AI 분석 건너뜀 (--llm 옵션으로 활성화)

보고서 저장: test_report.md
```

Documents 레포의 `agent-builder-automation/docs/analysis/` 에 보고서 추가 후 push 완료.

**사용자:**
여기에는 원인 분석 1차 의견이 없네?

**AI:**
LLM 분석 없이 실행했기 때문. `--llm claude --api-key YOUR_KEY` 옵션을 넣으면 AI 분석이 포함되고, 아니면 rule base로 1차 원인 추정 로직을 보고서에 넣는 방법도 있다.

**사용자:**
나는 형태를 보고 싶은거야 문서에 보여지는 형태 나중에 LLM으로 하면 비슷하게 나온다는 가정하에 그 결과를 미리 예측해보고 싶어. 그리고 좀 Graphical하게 하는건 오버헤드가 클까? 차트 같은거 한눈에 들어오게 하는 방식 말이야

**AI:**
오버헤드 거의 없습니다. mkdocs-material이 Mermaid 차트를 기본 지원하거든요. 코드블록만 넣으면 자동 렌더링.

보고서를 대폭 강화해서 다시 작성:
- **막대 차트 (xychart-beta):** Total PSS/RSS Baseline vs Regression 비교, 섹션별 비교
- **파이 차트:** 메모리 증가 기여도 비율 (Java Heap, Dalvik Heap, Native Heap, Graphics, GL mtrack)
- **AI 원인 분석 섹션 (시뮬레이션):**
  - 가설 1: Activity Leak (신뢰도: 높음) — Activities 0→2, Views 2배 증가 근거
  - 가설 2: Bitmap/Drawable 캐시 과다 (신뢰도: 중간) — Native Heap +10.8MB, GL mtrack +6.2MB 근거
  - 가설 3: 알림 채널/미디어 세션 누수 (신뢰도: 낮음)
  - 각 가설에 확인 방법(dumpsys 명령어 등) 포함
- **조치 권고 테이블:** 우선순위별 조치 + 담당자
- **조사 흐름 플로우차트:** Mermaid flowchart로 분석 절차 시각화
- **분석자 기록 영역 (Human-in-the-loop):** 실제 원인, 원인 코드, 해결 조치, 카테고리 태그 — 담당자가 직접 작성하는 영역

mkdocs.yml에 Mermaid 렌더링 설정(`pymdownx.superfences` custom_fences) 추가 후 push → GitHub Pages 배포.

모두 Mermaid 코드블록이라 별도 이미지 관리 없이 마크다운만으로 렌더링.

**사용자:**
아주 마음에 들어 고마워

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

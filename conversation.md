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

## 다음 단계 (예정)

- [ ] mkdocs 설정 및 GitHub Pages 배포
- [ ] 분석 보고서 템플릿 (자동 생성 + 분석자 기록 영역)
- [ ] dumpstate 파서 개발 (삼성 추가 로그 포함)
- [ ] LLM 분석 실제 실행 및 프롬프트 튜닝
- [ ] RAG / 벡터 DB 유사 사례 검색
- [ ] Agent Builder(Langflow) 연동용 컴포넌트 설계

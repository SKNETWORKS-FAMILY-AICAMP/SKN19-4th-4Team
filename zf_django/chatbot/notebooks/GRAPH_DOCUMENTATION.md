# LangGraph 기반 주택 공고 챗봇 (graph.py)

## 개요

`graph.py`는 LangGraph를 활용한 주택 공고 안내 챗봇의 핵심 로직입니다.

### 주요 특징
- **LLM 기반 의도 분류**: 사용자 질문을 5가지 의도로 분류
- **대화 맥락 유지**: 이전 검색 결과 및 선택된 공고 기억
- **조건부 라우팅**: 의도에 따라 다른 처리 흐름
- **Hybrid RAG**: FTS + 벡터 검색을 결합한 문서 검색
- **LLM 쿼리 확장**: 동의어를 활용한 검색 정확도 향상

---

## 아키텍처

### 전체 흐름도

```
사용자 질문
     │
     ▼
┌─────────────────┐
│ intent_classifier │  ← LLM으로 의도 분류
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼          ▼
new_search  reference  detail    general   clarification
    │        _prev    _question   _chat
    ▼         ▼          │          │          │
rdb_searcher reference   │          │          │
    │        _resolver   │          │          │
    ▼         │          │          │          │
search_    retriever ◄───┘          │          │
response      │                     │          │
    │         ▼                     │          │
    │    detail_response            │          │
    │         │                     │          │
    └─────────┴─────────┬───────────┴──────────┘
                        ▼
                       END
```

---

## 설정 (ChatbotConfig)

```python
class ChatbotConfig:
    REGIONS = ['서울특별시', '경기도']     # 검색 가능한 지역
    STATUSES = ['접수중', '공고중']        # 공고 상태
    LLM_MODEL = "gpt-4o-mini"             # 사용 LLM 모델
    EMBEDDING_MODEL = "text-embedding-3-small"  # 임베딩 모델
    MAX_HISTORY_TURNS = 10                # 최대 대화 기록 턴 수
    RAG_TOP_K = 10                        # RAG 검색 결과 수
```

> **확장 포인트**: DB나 환경변수에서 동적으로 로드하도록 수정 가능

---

## 의도(Intent) 분류

### 5가지 의도 유형

| 의도 | 설명 | 예시 질문 |
|------|------|----------|
| `new_search` | 새로운 공고 검색 요청 | "서울 청년 공고 보여줘", "접수중인 공고 알려줘" |
| `reference_prev` | 이전 결과에서 특정 공고 선택 | "1번 공고", "첫번째꺼 신청자격 알려줘" |
| `detail_question` | 선택된 공고에 대한 상세 질문 | "신청기간은 언제야?", "어떻게 신청해?" |
| `general_chat` | 일반 대화 | "안녕", "뭘 할 수 있어?" |
| `clarification` | 명확화 필요 | 이전 목록 없이 "1번", "그거" 등 |

### 의도 분류 우선순위
1. `reference_prev` - 번호가 언급되면 최우선
2. `detail_question` - 선택된 공고가 있고 번호 없이 질문
3. `new_search` - 검색 조건이 포함된 질문
4. `general_chat` - 인사, 도움말 등
5. `clarification` - 위 조건에 해당하지 않는 모호한 질문

---

## 노드 상세 설명

### 1. intent_classifier (의도 분류기)

**역할**: 사용자 질문의 의도를 분류하고 필요한 정보 추출

**입력**:
- `question`: 사용자 질문
- `chat_history`: 대화 기록
- `prev_anncs`: 이전에 보여준 공고 목록
- `selected_annc`: 현재 선택된 공고

**출력**:
- `intent`: 분류된 의도
- `intent_data`: 의도별 추가 데이터
- `search_filters`: 검색 조건 (new_search인 경우)

**특이사항**:
- LLM(gpt-4o-mini)을 사용하여 JSON 형식으로 응답
- 이전 목록/선택된 공고 유무에 따라 의도 검증 및 보정

---

### 2. reference_resolver (참조 해결기)

**역할**: "1번 공고", "첫번째" 등의 참조를 실제 공고로 변환

**입력**:
- `prev_anncs`: 이전 공고 목록
- `intent_data.reference_index`: 참조 인덱스 (1-based)

**출력**:
- `selected_annc`: 선택된 공고
- `candidate_anncs`: RAG 검색 대상

**특이사항**:
- `reference_index: -1`은 "마지막" 의미
- 유효하지 않은 인덱스는 에러 메시지 반환

---

### 3. rdb_searcher (DB 검색기)

**역할**: PostgreSQL에서 공고 검색

**입력**:
- `search_filters`: 검색 조건
  - `annc_region`: 지역 필터
  - `annc_status`: 상태 필터 (기본: ["접수중", "공고중"])
  - `keyword`: 제목 키워드

**출력**:
- `candidate_anncs`: 검색된 공고 목록
- `prev_anncs`: 다음 턴을 위해 저장

**사용 서비스**: `AnncAllService.search_announcements()`

---

### 4. retriever (RAG 검색기)

**역할**: 선택된 공고의 문서 청크에서 관련 정보 검색

**주요 기능**:

#### 4.1 쿼리 확장 (expand_query_with_llm)
LLM을 사용하여 검색 쿼리에 동의어 추가

```
"신청기간은 언제야?"
→ "신청기간 접수기간 청약기간 모집기간 청약신청 신청일정 일정"
```

#### 4.2 Hybrid 검색
- **FTS (Full-Text Search)**: 키워드 매칭
- **Vector Search**: 의미적 유사도
- **RRF (Reciprocal Rank Fusion)**: 두 결과 결합

**사용 서비스**: `DocChunkService.hybrid_search()`

---

### 5. 응답 생성기 (Response Generators)

#### generate_search_response
- 검색 결과 목록 포맷팅
- 결과 없음 / DB에 없는 지역 처리

#### generate_detail_response
- RAG 결과 기반 상세 답변 생성
- LLM으로 문서 내용 요약 및 답변

#### generate_general_response
- 일반 대화 처리 (인사, 도움말)
- 대화 기록 포함하여 자연스러운 응답

#### generate_clarification_response
- 모호한 질문에 대한 안내 메시지
- 사용 예시 제공

---

## 상태(State) 관리

### GraphState 구조

```python
class GraphState(TypedDict):
    # 입력
    question: str                    # 사용자 질문
    chat_history: List[dict]         # 대화 기록

    # 의도 분류 결과
    intent: str                      # 분류된 의도
    intent_data: dict                # 의도별 추가 데이터

    # 검색 관련
    search_filters: dict             # 검색 조건
    candidate_anncs: List[dict]      # 검색된 공고 목록
    retrieved_docs: List[dict]       # RAG 검색 결과

    # 대화 맥락
    prev_anncs: List[dict]           # 이전에 보여준 공고 목록
    selected_annc: Optional[dict]    # 현재 선택된 공고

    # 출력
    answer: str                      # 최종 응답
    debug_info: dict                 # 디버깅 정보
```

### 세션 상태 (session_state)

클라이언트가 유지해야 하는 상태:

```python
session_state = {
    "chat_history": [...],    # 대화 기록 (최대 10턴)
    "prev_anncs": [...],      # 이전 공고 목록
    "selected_annc": {...}    # 선택된 공고
}
```

---

## 사용 방법

### 기본 사용

```python
from chatbot.graph import chat

# 첫 질문
result = chat("접수중인 공고 알려줘")
print(result["answer"])
session = result["session_state"]

# 후속 질문 (세션 유지)
result = chat("1번 공고 신청자격 알려줘", session)
print(result["answer"])
session = result["session_state"]

# 추가 질문
result = chat("신청기간은 언제야?", session)
print(result["answer"])
```

### 반환값 구조

```python
{
    "answer": str,           # 챗봇 응답
    "session_state": {       # 다음 호출에 전달할 상태
        "chat_history": [...],
        "prev_anncs": [...],
        "selected_annc": {...}
    },
    "debug_info": {          # 디버깅용 (선택적)
        "intent_result": {...},
        "expanded_query": "...",
        ...
    }
}
```

---

## 의존성

### 외부 패키지
- `langgraph`: 그래프 기반 워크플로우
- `openai`: LLM 및 임베딩 API
- `python-decouple`: 환경변수 관리

### 내부 모듈
- `services.AnncAllService`: 공고 DB 검색
- `services.DocChunkService`: 문서 청크 검색 (Hybrid RAG)

### 환경변수
```
OPENAI_API_KEY=sk-...
```

---

## 확장 가이드

### 새로운 의도 추가

1. `Intent` 클래스에 새 의도 상수 추가
2. `intent_classifier`의 프롬프트에 의도 설명 추가
3. 새 응답 생성 함수 작성
4. `route_by_intent`에 라우팅 로직 추가
5. `create_chatbot_graph`에 노드 및 엣지 추가

### 검색 조건 추가

1. `ChatbotConfig`에 새 필터 옵션 추가
2. `intent_classifier` 프롬프트의 `search_filters` 스키마 수정
3. `rdb_searcher`에서 새 필터 처리
4. `AnncAllService.search_announcements` 수정 (필요시)

### 새 지역 추가

`ChatbotConfig.REGIONS`에 지역명 추가:
```python
REGIONS = ['서울특별시', '경기도', '부산광역시']  # 부산 추가
```

---

## 트러블슈팅

### Q: "신청기간" 질문에 엉뚱한 답변이 나와요
**A**: 문서에서 "신청기간" 대신 "접수기간", "청약기간" 등 다른 표현을 사용할 수 있습니다. `expand_query_with_llm`이 동의어를 추가하지만, 특정 도메인 용어가 누락될 수 있습니다.

### Q: "2번 공고 알려줘"가 작동하지 않아요
**A**: `prev_anncs`가 세션에 유지되고 있는지 확인하세요. 매 호출 시 이전 `session_state`를 전달해야 합니다.

### Q: DB에 없는 지역을 검색하면 전체 공고가 나와요
**A**: `intent_classifier`가 `invalid_region` 필드를 반환해야 합니다. LLM 프롬프트를 확인하세요.

---

## 버전 히스토리

| 버전 | 변경사항 |
|------|----------|
| V5 | LLM 기반 의도 분류, 대화 맥락 유지, 조건부 라우팅 |
| V4 | 참조 질문 처리 개선 |
| V3 | DB 실제 값 기반 검색, 키워드 검색 지원 |
| V2 | annc_status 기본값 처리 개선 |
| V1 | 초기 버전 |

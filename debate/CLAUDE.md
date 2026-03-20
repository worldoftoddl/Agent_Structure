# debate/ — CEDA 토론 시스템

## 역할

AI 에이전트들이 CEDA(Cross-Examination Debate Association) 형식으로 토론하는 독립 모듈. LangGraph StateGraph를 직접 구성하여 peer-to-peer 순차 토론을 구현한다. 기존 `build_agent()` 경로와는 별도의 조립점.

## 파일 구조

- `state.py` — `DebateState` TypedDict, `SpeechRecord`, `RoundConfig`, `CEDA_ROUNDS` 상수
- `prompts.py` — AFF/NEG/Judge 시스템 프롬프트 + 라운드별 지시사항 + transcript 포맷터
- `nodes.py` — `create_debate_node()`, `create_judge_node()`, `route_next()`, 도구 호출 루프
- `graph.py` — `build_debate_graph()` — 3개 LLM resolve + StateGraph 조립
- `runner.py` — `create_debate()`, `run_debate()`, `arun_debate()`, `stream_debate()`
- `__init__.py` — re-export

## CEDA 라운드 시퀀스

총 10개 토론 턴 + 1 심판 판정 = 11턴:

1. **1AC** (긍정측 입론) → 2. **CX_1AC_Q** (부정측 질문) → 3. **CX_1AC_A** (긍정측 답변)
4. **1NC** (부정측 입론) → 5. **CX_1NC_Q** (긍정측 질문) → 6. **CX_1NC_A** (부정측 답변)
7. **1AR** (긍정측 반박) → 8. **1NR** (부정측 반박)
9. **2NR** (부정측 최종반박) → 10. **2AR** (긍정측 최종반박)
11. **VERDICT** (심판 판정)

## 그래프 토폴로지

```
START → debate_node → route_next ─(continue)─→ debate_node (루프)
                                  ─(judge)────→ judge_node → END
```

## State 격리

`DebateState`에 `aff_private_notes`와 `neg_private_notes`가 있지만, `debate_node`가 LLM을 호출할 때 **자기 측의 메모만 주입**하고 상대측은 제외. 공개 transcript는 양측 모두에게 전달.

비공개 메모는 LLM 응답에서 `[PRIVATE_NOTES]...[/PRIVATE_NOTES]` 태그로 파싱.

## 사용법

```python
from Agent_Structure.debate import run_debate, stream_debate

# 기본 사용
result = run_debate("AI가 인간의 일자리를 대체하는 것은 긍정적이다")
print(result.format_transcript())
print(result.verdict)

# 모델 대결
result = run_debate(
    "논제",
    aff_provider_name="anthropic", aff_model_name="claude-sonnet-4-5-20250929",
    neg_provider_name="openai", neg_model_name="gpt-4o",
)

# 도구 포함
from Agent_Structure.tools import tool_registry
result = run_debate("논제", tools=tool_registry.get_by_tag("search"))

# 라운드별 스트리밍
for speech in stream_debate("논제"):
    print(f"[{speech['round_id']}] {speech['speaker']}: {speech['content'][:100]}...")
```

## 재사용 기존 컴포넌트

| 컴포넌트 | 사용 |
|----------|------|
| `core/model_provider.py` → `get_provider()` | 측별 LLM 인스턴스 생성 |
| `config/settings.py` → `settings` | default_provider/model |
| `tools/base.py` → `tool_registry` | 선택적 도구 주입 |

## 수정 시 주의사항

- `CEDA_ROUNDS`를 변경하면 토론 흐름 전체에 영향. `round_id`는 고유해야 한다.
- `prompts.py`의 비공개 메모 태그 형식(`[PRIVATE_NOTES]`)을 변경하면 `nodes.py`의 파싱 로직도 수정 필요.
- `build_debate_graph()`는 `build_agent()`와 독립적인 조립점이므로, 도구 상속이나 서브에이전트 기능은 적용되지 않음.

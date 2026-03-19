# tools/ — 도구 레지스트리 및 개별 도구

## 역할

에이전트가 사용할 도구(Tool)를 정의하고 레지스트리에 등록한다. `build_agent()`가 레지스트리에서 도구를 수집하여 에이전트에 주입한다.

## 파일 구조

- `base.py` — `ToolRegistry` 클래스 + `register_tool` 데코레이터 + 글로벌 싱글톤 `tool_registry`
- `_template.py` — 새 도구 작성용 템플릿 (복사해서 사용)
- `__init__.py` — `tool_registry`, `register_tool` re-export + 개별 도구 import (import 시 자동 등록)
- `web_search.py` — Tavily 웹 검색 도구 (태그: `search`, `web`)
- `think.py` — 전략적 사고 도구 (태그: `reasoning`)

## ToolRegistry 핵심 API

```python
# 등록
tool_registry.register(func, name="...", tags=["search"], description="...")

# 조회
tool_registry.get("web_search")          # 이름으로 단일 조회
tool_registry.get_all()                   # 전체
tool_registry.get_by_tag("search")        # 태그 필터
tool_registry.list_names()                # 이름 목록
tool_registry.summary()                   # 디버깅용 요약
```

## 새 도구 추가 방법

1. `_template.py`를 복사하여 새 파일 생성 (예: `tools/my_retriever.py`)
2. `@register_tool(tags=["my_tag"])` 데코레이터 사용
3. `tools/__init__.py`에 `from . import my_retriever` 추가

```python
# tools/my_retriever.py
from .base import register_tool

@register_tool(tags=["rag", "search"])
def my_retriever(query: str) -> str:
    """이 docstring이 LLM에게 보이는 도구 설명이 됩니다."""
    # 구현
    return result
```

**중요**: `__init__.py`에 import를 추가해야 모듈 로드 시 `@register_tool`이 실행되어 레지스트리에 등록된다.

## 태그 컨벤션

| 태그 | 용도 |
|------|------|
| `search` | 검색 계열 (웹, RAG 등) |
| `web` | 웹 관련 |
| `rag` | RAG/retriever |
| `reasoning` | 추론/사고 |
| `example` | 템플릿/예시 (build_agent에서 자동 제외) |

## 도구 사용 추적

`build_agent(track_tool_usage=True)`로 활성화하면, 도구 호출이 자동으로 기록된다.

```python
# 추적 활성화된 에이전트 생성
agent = build_agent(track_tool_usage=True)

# ... 에이전트 실행 ...

# 사용 통계 조회
stats = tool_registry.get_usage_stats()
# → {"total_calls": 5, "calls_by_tool": {"web_search": 3, "think_tool": 2}, ...}

# 개별 호출 기록
for record in tool_registry.get_call_log():
    print(f"{record.tool_name}: {record.duration_ms}ms, success={record.success}")

# 레지스트리에서 직접 추적 도구 가져오기 (build_agent 없이)
tracked_tools = tool_registry.get_all_tracked()
tracked_search = tool_registry.get_by_tag_tracked("search")

# 호출 기록 초기화
tool_registry.clear_call_log()
```

## 수정 시 주의사항

- `_template.py`의 `example_tool`은 `build_agent()`에서 `__name__` 체크로 자동 제외된다. 함수명을 바꾸면 제외 로직도 확인할 것.
- 도구 함수의 docstring이 LLM에게 도구 설명으로 노출된다. 영어로 작성하는 것을 권장.
- `tool_registry`는 싱글톤이므로, 테스트 시 `tool_registry.clear()`로 초기화 가능.

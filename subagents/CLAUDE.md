# subagents/ — 서브에이전트 레지스트리 및 정의

## 역할

메인 에이전트가 위임할 서브에이전트를 정의하고 레지스트리에 등록한다. 서브에이전트는 독립된 컨텍스트에서 실행되어 메인 에이전트의 컨텍스트 윈도우를 오염시키지 않는다.

## 파일 구조

- `registry.py` — `SubagentRegistry` 클래스 + 글로벌 싱글톤 `subagent_registry`
- `research_agent.py` — 리서치 서브에이전트 예시
- `__init__.py` — `subagent_registry` re-export + 개별 서브에이전트 import (import 시 자동 등록)

## 서브에이전트 설정 형식

DeepAgents의 서브에이전트는 dict로 정의:

```python
config = {
    "name": "research-agent",          # 필수: 고유 이름
    "description": "심층 리서치 담당",    # 필수: LLM이 위임 판단에 사용
    "system_prompt": "당신은 전문 리서처입니다...",
    "tools": [],                        # 서브에이전트 전용 도구 (빈 리스트 가능)
    "model": "openai:gpt-4o",           # 생략 시 메인 에이전트 모델 상속
}
```

## SubagentRegistry 핵심 API

```python
subagent_registry.register(config)           # 등록
subagent_registry.get("research-agent")      # 이름으로 조회
subagent_registry.get_all()                  # 전체
subagent_registry.get_by_names(["a", "b"])   # 이름 목록으로 선택 조회
subagent_registry.list_names()               # 등록된 이름 목록
```

## 새 서브에이전트 추가 방법

1. `research_agent.py`를 참고하여 새 파일 생성 (예: `subagents/tax_agent.py`)
2. config dict 작성 후 `subagent_registry.register(config)` 호출
3. `subagents/__init__.py`에 `from . import tax_agent` 추가

```python
# subagents/tax_agent.py
from .registry import subagent_registry

tax_agent_config = {
    "name": "tax-agent",
    "description": "세법 관련 질문에 전문적으로 답변합니다.",
    "system_prompt": "당신은 한국 세법 전문가입니다...",
    "tools": [],
}

subagent_registry.register(tax_agent_config)
```

## build_agent에서의 사용

```python
# 특정 서브에이전트만
build_agent(subagent_names=["research-agent"])

# 등록된 모든 서브에이전트
build_agent(include_all_subagents=True)
```

## 수정 시 주의사항

- `"name"` 키는 필수. 없으면 `ValueError` 발생.
- `"tools"` 필드에 도구를 직접 넣을 수도 있고, `build_agent()`에서 별도로 주입할 수도 있다.
- `subagent_registry`는 싱글톤. `__init__.py`의 import 순서에 주의.

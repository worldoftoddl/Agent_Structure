# core/ — 에이전트 조립 및 모델 프로바이더

## 역할

프로젝트의 **단일 조립점(Single Assembly Point)**. 모든 구성 요소(모델, 도구, 서브에이전트)를 받아서 하나의 DeepAgent로 조립한다.

## 파일 구조

- `agent_factory.py` — `build_agent()` 함수. 유일한 조립 지점.
- `model_provider.py` — `ModelProvider` ABC + 프로바이더 구현체들 + 팩토리 함수.
- `__init__.py` — re-export (`ModelProvider`, `get_provider`, `register_provider`, `build_agent`)

## agent_factory.py

`build_agent()` — 6단계 조립 파이프라인:

1. **모델 준비**: `provider` 직접 주입 또는 `provider_name`/`model_name` 문자열로 생성
2. **도구 수집**: `tool_tags`로 필터 또는 전체 수집 → `exclude_tools`로 제외 → `tools`로 직접 추가
3. **서브에이전트 수집**: `subagent_names` 지정 또는 `include_all_subagents=True`
3.5. **서브에이전트 도구 상속**: `inherit_tools=True`면 메인 도구를 서브에이전트에 자동 주입
4. **도구 사용 추적**: `track_tool_usage=True`면 호출 기록을 `tool_registry`에 저장
5. **체크포인터**: HITL/메모리 필요 시 자동 `MemorySaver` 생성
6. **조립**: `create_deep_agent(**kwargs)` 호출 → `CompiledStateGraph` 반환

주요 파라미터:
```python
build_agent(
    provider_name="anthropic",      # 프로바이더 키
    model_name="claude-sonnet-4-5-20250929",  # 모델명
    tools=[my_tool],                # 직접 도구 추가
    tool_tags=["search"],           # 태그 필터
    exclude_tools=["example_tool"], # 제외
    subagent_names=["research-agent"],
    inherit_tools=True,             # 서브에이전트에 도구 상속 (기본 True)
    system_prompt="...",
    enable_memory=True,
    track_tool_usage=False,         # 도구 사용 추적 (기본 False)
    checkpointer=None,              # None이면 자동 생성
)
```

### 서브에이전트 도구 상속

`inherit_tools=True`(기본값)이면, 서브에이전트의 `tools`가 비어있을 때 메인 에이전트의 수집된 도구를 자동 상속한다.
- 서브에이전트 config에 `"inherit_tools": False`를 설정하면 해당 에이전트는 상속 제외
- 서브에이전트가 자체 `tools`를 가지고 있으면 상속하지 않음 (덮어쓰지 않음)
- 원본 레지스트리 config를 변경하지 않도록 복사본을 사용

### 도구 사용 추적

`track_tool_usage=True`면 도구 함수를 래핑하여 호출 시간, 성공/실패를 기록한다.
```python
agent = build_agent(track_tool_usage=True)
# ... 에이전트 실행 후 ...
from Agent_Structure.tools import tool_registry
print(tool_registry.get_usage_stats())
# → {"total_calls": 3, "calls_by_tool": {"web_search": 2, "think_tool": 1}, ...}
```

## model_provider.py

### ModelProvider ABC
```python
class ModelProvider(ABC):
    def __init__(self, model_name: str, **kwargs): ...
    def get_llm(self) -> BaseChatModel: ...  # 추상 메서드
```

### 기본 제공 프로바이더

| 클래스 | 키 | 기본 모델 | LangChain 클래스 |
|--------|-----|-----------|-----------------|
| `AnthropicProvider` | `"anthropic"` | `claude-sonnet-4-5-20250929` | `ChatAnthropic` |
| `OpenAIProvider` | `"openai"` | `gpt-4o` | `ChatOpenAI` |
| `UpstageProvider` | `"upstage"` | `solar-pro` | `ChatUpstage` |

### 새 프로바이더 추가 방법

1. `ModelProvider`를 상속하여 `get_llm()` 구현
2. `register_provider("my_key", MyProviderClass)` 호출
3. 이후 `build_agent(provider_name="my_key")`로 사용 가능

```python
class GeminiProvider(ModelProvider):
    def get_llm(self) -> BaseChatModel:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=self.model_name, **self.kwargs)

register_provider("gemini", GeminiProvider)
```

### 팩토리 함수

- `get_provider(name, model_name=None, **kwargs)` — 문자열 키 → `ModelProvider` 인스턴스
- `register_provider(name, cls)` — 런타임에 커스텀 프로바이더 등록

## 수정 시 주의사항

- `build_agent()`의 파라미터를 변경하면 `run_notebook.py`와 `main.py` 양쪽에 영향을 준다.
- `_PROVIDER_MAP`에 직접 추가하는 것보다 `register_provider()`를 사용하는 것이 안전하다.

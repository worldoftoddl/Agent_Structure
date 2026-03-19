# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DeepAgents + LangGraph + LangChain 기반의 확장 가능한 AI 에이전트 프레임워크. 교체 가능한 LLM 프로바이더, 도구 레지스트리 시스템, 서브에이전트 위임을 지원한다.

## Architecture

핵심 설계: **단일 조립점(Single Assembly Point)** 패턴. 모든 구성 요소는 독립적으로 정의되고, `core/agent_factory.py`의 `build_agent()`에서만 조합된다.

```
Settings (config/settings.py)
    ↓
ModelProvider (core/model_provider.py) → get_llm() → BaseChatModel
ToolRegistry (tools/base.py)           → 태그/이름 기반 도구 수집
SubagentRegistry (subagents/registry.py) → 서브에이전트 구성
    ↓
build_agent() → create_deep_agent() (deepagents 라이브러리)
    ↓
CompiledStateGraph (LangGraph 에이전트)
```

**진입점 두 가지:**
- `run_notebook.py`: Jupyter 노트북용 (`create_agent`, `run`, `arun`, `stream`)
- `main.py`: FastAPI 서버 (`POST /chat`, `GET /health`)

## Key Patterns

- **도구 등록**: `@register_tool(tags=["tag1"])` 데코레이터 → 싱글톤 `tool_registry`에 자동 등록. 새 도구는 `tools/_template.py` 복사 후 `tools/__init__.py`에 import 추가.
- **모델 프로바이더**: `ModelProvider` ABC 상속 → `get_llm()` 구현 → `register_provider()`로 런타임 등록. 기본 제공: Anthropic, OpenAI, Upstage.
- **서브에이전트**: `{"name", "description", "system_prompt", "tools", "model"}` 딕셔너리로 정의 → `subagent_registry.register()`로 등록.
- **싱글톤 레지스트리**: `ToolRegistry`, `SubagentRegistry` 모두 싱글톤.

## Commands

```bash
# 의존성 설치
pip install -r requirements.txt

# API 서버 실행
uvicorn Agent_Structure.main:app --reload

# 노트북에서 에이전트 실행
from Agent_Structure.run_notebook import create_agent, run
agent = create_agent()
result = run(agent, "질문")
```

## Import 주의사항

- 패키지 내부에서 상대 import(`from ..config import settings`)를 사용하므로, **반드시 상위 디렉토리에서** `Agent_Structure.모듈명`으로 import해야 한다.
- `load_dotenv()`는 CWD 기준으로 `.env`를 찾는다. 상위 디렉토리에서 실행 시 `.env`를 못 찾을 수 있으므로 주의.

## Environment Variables

`.env` 파일 또는 시스템 환경변수로 설정:
- `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `TAVILY_API_KEY`: 프로바이더/도구별 API 키
- `DART_API_KEY`, `PINECONE_API_KEY`, `COHERE_API_KEY`, `GOOGLE_API_KEY`: 추가 도구용
- `DEFAULT_PROVIDER`: anthropic | openai | upstage (기본: anthropic)
- `DEFAULT_MODEL`: 모델 식별자 (기본: claude-sonnet-4-5-20250929)
- `DATABASE_DIR`: 외부 데이터 경로 (RAG/검색 도구용)

## Language

이 프로젝트는 한국어 도메인(K-IFRS 회계기준 등)을 주요 대상으로 하며, `skills/writing_rules.md`에 한국어 작문 가이드라인이 포함되어 있다. Upstage Solar 모델은 한국어 특화 프로바이더로 제공된다.

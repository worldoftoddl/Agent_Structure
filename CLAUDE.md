# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DeepAgents + LangGraph + LangChain 기반의 확장 가능한 AI 에이전트 프레임워크. 교체 가능한 LLM 프로바이더, 도구 레지스트리 시스템, 서브에이전트 위임을 지원한다.

## Architecture

핵심 설계: **단일 조립점(Single Assembly Point)** 패턴. 모든 구성 요소는 독립적으로 정의되고, `core/agent_factory.py`의 `build_agent()`에서만 조합된다.

```
Settings (config/)            → 환경변수, API 키 관리
ModelProvider (core/)         → get_llm() → BaseChatModel
ToolRegistry (tools/)         → 태그/이름 기반 도구 수집 + 사용 추적
SubagentRegistry (subagents/) → 서브에이전트 구성
    ↓
build_agent() (core/)         → 도구 상속 · 추적 래핑 → create_deep_agent()
    ↓
CompiledStateGraph (LangGraph 에이전트)
```

### build_agent() 주요 기능

- **서브에이전트 도구 상속** (`inherit_tools=True`, 기본값): 서브에이전트의 `tools`가 비어있으면 메인 에이전트 도구를 자동 주입. 서브에이전트 config에 `"inherit_tools": False`로 개별 제외 가능.
- **도구 사용 추적** (`track_tool_usage=True`): 도구 호출 시간·성공/실패를 `tool_registry`에 기록. `tool_registry.get_usage_stats()`로 통계 조회.

## Component Map

각 디렉토리의 `CLAUDE.md`에 해당 컴포넌트의 상세 설계, 확장 방법, 주의사항이 기술되어 있다.

| 디렉토리 | 역할 | 핵심 파일 |
|-----------|------|-----------|
| `config/` | 환경변수·설정 관리 | `settings.py` |
| `core/` | 에이전트 조립, 모델 프로바이더 | `agent_factory.py`, `model_provider.py` |
| `tools/` | 도구 레지스트리, 개별 도구 | `base.py`, `_template.py` |
| `subagents/` | 서브에이전트 레지스트리·정의 | `registry.py` |
| `skills/` | 스킬 파일 (프롬프트·가이드라인) | `writing_rules.md` |

**진입점 두 가지:**
- `run_notebook.py`: Jupyter 노트북용 (`create_agent`, `run`, `arun`, `stream`)
- `main.py`: FastAPI 서버 (`POST /chat`, `GET /health`)

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

이 프로젝트는 한국어 도메인(K-IFRS 회계기준 등)을 주요 대상으로 하며, `skills/writing_rules.md`에 한국어 작문 가이드라인이 포함되어 있다.

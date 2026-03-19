# config/ — 환경변수 및 설정 관리

## 역할

`.env` 파일 또는 시스템 환경변수에서 API 키와 기본 설정을 로드하여 프로젝트 전역에서 사용할 수 있게 한다.

## 파일 구조

- `settings.py` — `Settings` dataclass + 글로벌 싱글톤 `settings`
- `__init__.py` — `settings` re-export

## Settings 클래스

```python
@dataclass
class Settings:
    # LLM API Keys
    anthropic_api_key: str | None    # ANTHROPIC_API_KEY
    openai_api_key: str | None       # OPENAI_API_KEY

    # Tool API Keys
    tavily_api_key: str | None       # TAVILY_API_KEY

    # External Data
    database_dir: str | None         # DATABASE_DIR

    # Agent Defaults
    default_provider: str            # DEFAULT_PROVIDER (기본: "anthropic")
    default_model: str               # DEFAULT_MODEL (기본: "claude-sonnet-4-5-20250929")

    # DeepAgent 설정
    max_iterations: int = 25         # 에이전트 최대 반복 횟수
```

## 사용 패턴

```python
from ..config import settings

# 어디서든 싱글톤으로 접근
api_key = settings.tavily_api_key
provider = settings.default_provider

# 필수 키 검증
missing = settings.validate()
if missing:
    raise RuntimeError(f"누락된 환경변수: {missing}")
```

## 새 환경변수 추가 방법

1. `Settings` dataclass에 필드 추가 (`default_factory=lambda: os.getenv("KEY_NAME")`)
2. `.env` 파일에 실제 값 추가
3. 루트 `CLAUDE.md`의 Environment Variables 섹션에 문서화

## 수정 시 주의사항

- `load_dotenv()`는 CWD 기준으로 `.env`를 찾는다. 상위 디렉토리에서 실행하면 `.env`를 못 찾을 수 있다.
- `dotenv` 미설치 시에도 동작하도록 `try/except ImportError`로 감싸져 있다.
- `settings`는 모듈 로드 시 즉시 생성되는 싱글톤이다. 테스트 시 필드를 직접 덮어쓸 수 있다.

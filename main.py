"""
FastAPI 서버 — 추후 확장용.

현재는 최소한의 엔드포인트만 제공합니다.
ipynb에서 충분히 검증한 뒤 이쪽으로 옮기세요.

실행:
    uvicorn agent_skeleton.main:app --reload

NOTE: 단일 워커(--workers 1)로 실행해야 합니다.
      _agent_cache는 프로세스 내 dict이므로 멀티 워커 시 각 프로세스가
      별도 에이전트를 빌드하여 메모리를 낭비합니다.
"""
from __future__ import annotations

import re
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from .config import settings
from .core.agent_factory import build_agent
from .run_notebook import arun


# ── 앱 상태 (에이전트 인스턴스 캐싱) ──
# 단일 워커 전제. asyncio 이벤트 루프 내에서는 dict 접근이 원자적.
_agent_cache: dict[str, Any] = {}

_THREAD_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작 시 기본 에이전트를 미리 빌드합니다."""
    missing = settings.validate()
    if missing:
        raise RuntimeError(f"필수 환경변수 누락: {missing}")

    _agent_cache["default"] = build_agent(
        system_prompt="당신은 도움이 되는 AI 어시스턴트입니다."
    )
    yield
    _agent_cache.clear()


app = FastAPI(
    title="DeepAgent API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8888"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10_000)
    thread_id: str = Field("api-default", min_length=1, max_length=128)

    @field_validator("thread_id")
    @classmethod
    def validate_thread_id(cls, v: str) -> str:
        if not _THREAD_ID_PATTERN.match(v):
            raise ValueError("thread_id는 영문, 숫자, _, - 만 허용됩니다 (최대 128자)")
        return v


class ChatResponse(BaseModel):
    response: str
    thread_id: str


async def _verify_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> None:
    """API 키 헤더 검증. 환경변수 DEEPAGENT_API_KEY가 설정된 경우에만 활성화."""
    import os
    expected = os.getenv("DEEPAGENT_API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="유효하지 않은 API 키")


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """에이전트에 메시지를 보내고 응답을 받습니다."""
    await _verify_api_key()
    agent = _agent_cache["default"]
    response_text = await arun(agent, req.message, thread_id=req.thread_id)
    return ChatResponse(response=response_text, thread_id=req.thread_id)


@app.get("/health")
async def health():
    return {"status": "ok"}

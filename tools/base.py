"""
도구(Tool) 레지스트리.

도구를 등록하고, 이름으로 조회하고, 한꺼번에 꺼내서
create_deep_agent(tools=...)에 넘길 수 있습니다.

설계 의도:
    - 다른 폴더(예: Study/_database/)에서 만든 retriever 함수를
      여기에 등록하면 에이전트가 바로 사용 가능
    - @register_tool 데코레이터로 함수 정의와 동시에 등록 가능
    - 태그 기반 필터링으로 용도별 도구 세트 구성 가능

사용 예시:
    # 방법 1: 데코레이터
    @register_tool(tags=["search"])
    def web_search(query: str) -> str:
        ...

    # 방법 2: 수동 등록
    tool_registry.register(my_retriever_func, tags=["rag"])

    # 도구 꺼내기
    all_tools = tool_registry.get_all()
    search_tools = tool_registry.get_by_tag("search")
"""
from __future__ import annotations

import functools
import logging
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class ToolEntry:
    """레지스트리에 저장되는 도구 메타데이터."""
    func: Callable
    name: str
    tags: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ToolCallRecord:
    """도구 호출 기록."""
    tool_name: str
    timestamp: datetime
    duration_ms: float
    success: bool
    error: str | None = None


class ToolRegistry:
    """도구 저장소. 싱글턴으로 사용."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolEntry] = {}
        self._call_log: list[ToolCallRecord] = []

    def register(
        self,
        func: Callable,
        *,
        name: str | None = None,
        tags: list[str] | None = None,
        description: str = "",
    ) -> Callable:
        """
        도구를 레지스트리에 등록합니다.

        Args:
            func: @tool 데코레이터가 붙은 함수 또는 일반 함수
            name: 등록 이름 (기본: 함수 이름)
            tags: 분류 태그 (예: ["search"], ["rag", "tax"])
            description: 설명 (기본: docstring)

        Returns:
            원래 함수 (데코레이터 체이닝 가능)
        """
        tool_name = name or getattr(func, "name", func.__name__)
        desc = description or (func.__doc__ or "").strip()
        entry = ToolEntry(func=func, name=tool_name, tags=tags or [], description=desc)
        self._tools[tool_name] = entry
        logger.info("도구 등록: '%s' (tags=%s)", tool_name, tags or [])
        return func

    def get(self, name: str) -> Callable:
        """이름으로 도구를 가져옵니다."""
        entry = self._tools.get(name)
        if entry is None:
            available = ", ".join(self._tools.keys())
            raise KeyError(f"도구 '{name}'을 찾을 수 없습니다. 등록된 도구: {available}")
        return entry.func

    def get_all(self) -> list[Callable]:
        """등록된 모든 도구를 리스트로 반환합니다."""
        return [e.func for e in self._tools.values()]

    def get_by_tag(self, tag: str) -> list[Callable]:
        """특정 태그가 달린 도구만 반환합니다."""
        return [e.func for e in self._tools.values() if tag in e.tags]

    def list_names(self) -> list[str]:
        """등록된 도구 이름 목록."""
        return list(self._tools.keys())

    def summary(self) -> str:
        """등록된 도구 요약 (디버깅용)."""
        lines = [f"=== ToolRegistry ({len(self._tools)} tools) ==="]
        for name, entry in self._tools.items():
            tags_str = ", ".join(entry.tags) if entry.tags else "-"
            lines.append(f"  [{tags_str}] {name}: {entry.description[:60]}")
        return "\n".join(lines)

    # ── 도구 사용 추적 ──

    def wrap_with_tracking(self, func: Callable) -> Callable:
        """도구 함수를 래핑하여 호출을 추적합니다."""
        tool_name = getattr(func, "__name__", getattr(func, "name", "unknown"))

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = (time.perf_counter() - start) * 1000
                self._call_log.append(ToolCallRecord(
                    tool_name=tool_name,
                    timestamp=datetime.now(),
                    duration_ms=round(duration, 2),
                    success=True,
                ))
                logger.info("도구 호출 완료: '%s' (%.1fms)", tool_name, duration)
                return result
            except Exception as e:
                duration = (time.perf_counter() - start) * 1000
                self._call_log.append(ToolCallRecord(
                    tool_name=tool_name,
                    timestamp=datetime.now(),
                    duration_ms=round(duration, 2),
                    success=False,
                    error=str(e),
                ))
                logger.error("도구 호출 실패: '%s' — %s", tool_name, e)
                raise

        # LangChain/DeepAgents 도구 속성 보존
        for attr in ("name", "description", "args_schema", "return_direct"):
            if hasattr(func, attr):
                setattr(wrapper, attr, getattr(func, attr))

        return wrapper

    def get_all_tracked(self) -> list[Callable]:
        """추적 래핑된 모든 도구를 반환합니다."""
        return [self.wrap_with_tracking(e.func) for e in self._tools.values()]

    def get_by_tag_tracked(self, tag: str) -> list[Callable]:
        """추적 래핑된 특정 태그 도구를 반환합니다."""
        return [
            self.wrap_with_tracking(e.func)
            for e in self._tools.values()
            if tag in e.tags
        ]

    def get_call_log(self) -> list[ToolCallRecord]:
        """도구 호출 기록을 반환합니다."""
        return list(self._call_log)

    def get_usage_stats(self) -> dict[str, Any]:
        """도구 사용 통계를 반환합니다."""
        calls = Counter(r.tool_name for r in self._call_log)
        errors = Counter(r.tool_name for r in self._call_log if not r.success)
        avg_duration: dict[str, float] = {}
        for name in calls:
            durations = [r.duration_ms for r in self._call_log if r.tool_name == name]
            avg_duration[name] = round(sum(durations) / len(durations), 2)

        return {
            "total_calls": len(self._call_log),
            "calls_by_tool": dict(calls),
            "errors_by_tool": dict(errors),
            "avg_duration_ms": avg_duration,
        }

    def clear_call_log(self) -> None:
        """호출 기록 초기화."""
        self._call_log.clear()

    def clear(self) -> None:
        """모든 도구 및 호출 기록 제거 (테스트용)."""
        self._tools.clear()
        self._call_log.clear()


# 글로벌 싱글턴
tool_registry = ToolRegistry()


def register_tool(
    func: Callable | None = None,
    *,
    tags: list[str] | None = None,
    name: str | None = None,
    description: str = "",
) -> Any:
    """
    데코레이터로 도구를 등록합니다.

    사용법:
        @register_tool(tags=["search"])
        def web_search(query: str) -> str:
            '''웹 검색'''
            ...

        # 또는 인자 없이
        @register_tool
        def simple_tool(x: str) -> str:
            ...
    """
    def decorator(f: Callable) -> Callable:
        tool_registry.register(f, name=name, tags=tags, description=description)
        return f

    # @register_tool (괄호 없이) 호출된 경우
    if func is not None:
        return decorator(func)

    # @register_tool(tags=["search"]) 형태
    return decorator

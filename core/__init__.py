from __future__ import annotations

from typing import Any

from .model_provider import ModelProvider, get_provider, register_provider


def build_agent(**kwargs: Any) -> Any:
    """에이전트를 조립하여 반환한다. CompiledStateGraph를 반환."""
    from .agent_factory import build_agent as _build
    return _build(**kwargs)

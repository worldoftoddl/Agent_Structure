"""
CEDA 토론 그래프 조립.

LangGraph StateGraph를 구성하여 CEDA 토론 흐름을 구현한다.

토폴로지:
    START → debate_node → route_next ─(continue)─→ debate_node
                                      ─(judge)────→ judge_node → END
"""
from __future__ import annotations

import logging
from typing import Any, Callable

from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ..config import settings
from ..core.model_provider import get_provider
from .nodes import create_debate_node, create_judge_node, route_next
from .state import DebateState

logger = logging.getLogger(__name__)


def _resolve_llm(
    provider_name: str | None,
    model_name: str | None,
    fallback_llm: BaseChatModel | None = None,
) -> BaseChatModel:
    """프로바이더/모델명으로 LLM을 resolve한다. 미지정 시 fallback 사용."""
    if provider_name or model_name:
        prov = provider_name or settings.default_provider
        model = model_name or settings.default_model
        return get_provider(prov, model_name=model).get_llm()
    if fallback_llm is not None:
        return fallback_llm
    return get_provider(
        settings.default_provider, model_name=settings.default_model
    ).get_llm()


def build_debate_graph(
    *,
    # 기본 모델 (미지정 측에 적용)
    provider_name: str | None = None,
    model_name: str | None = None,
    # 측별 모델 오버라이드
    aff_provider_name: str | None = None,
    aff_model_name: str | None = None,
    neg_provider_name: str | None = None,
    neg_model_name: str | None = None,
    judge_provider_name: str | None = None,
    judge_model_name: str | None = None,
    # 도구 (선택)
    tools: list[Callable] | None = None,
    # 체크포인터
    checkpointer: Any | None = None,
) -> CompiledStateGraph:
    """CEDA 토론 StateGraph를 조립하여 컴파일된 그래프를 반환한다.

    Args:
        provider_name: 기본 프로바이더 ("anthropic", "openai" 등)
        model_name: 기본 모델명
        aff_provider_name: 긍정측 전용 프로바이더
        aff_model_name: 긍정측 전용 모델명
        neg_provider_name: 부정측 전용 프로바이더
        neg_model_name: 부정측 전용 모델명
        judge_provider_name: 심판 전용 프로바이더
        judge_model_name: 심판 전용 모델명
        tools: 토론 에이전트에 제공할 도구 리스트
        checkpointer: LangGraph 체크포인터 (None이면 MemorySaver 자동 생성)

    Returns:
        CompiledStateGraph
    """
    # ── 1. LLM 3개 resolve ──
    default_llm = _resolve_llm(provider_name, model_name)

    aff_llm = _resolve_llm(aff_provider_name, aff_model_name, default_llm)
    neg_llm = _resolve_llm(neg_provider_name, neg_model_name, default_llm)
    judge_llm = _resolve_llm(judge_provider_name, judge_model_name, default_llm)

    logger.info(
        "토론 LLM 구성: aff=%s, neg=%s, judge=%s",
        getattr(aff_llm, "model", "?"),
        getattr(neg_llm, "model", "?"),
        getattr(judge_llm, "model", "?"),
    )

    # ── 2. 노드 함수 생성 (클로저) ──
    debate_node = create_debate_node(aff_llm, neg_llm, tools)
    judge_node = create_judge_node(judge_llm)

    # ── 3. StateGraph 조립 ──
    graph = StateGraph(DebateState)

    graph.add_node("debate_node", debate_node)
    graph.add_node("judge_node", judge_node)

    graph.add_edge(START, "debate_node")
    graph.add_conditional_edges(
        "debate_node",
        route_next,
        {"continue": "debate_node", "judge": "judge_node"},
    )
    graph.add_edge("judge_node", END)

    # ── 4. 컴파일 ──
    if checkpointer is None:
        checkpointer = MemorySaver()

    compiled = graph.compile(checkpointer=checkpointer)
    logger.info("토론 그래프 컴파일 완료")

    return compiled

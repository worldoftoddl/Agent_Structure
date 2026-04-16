"""
CEDA 토론 고수준 API.

노트북이나 FastAPI에서 간단하게 토론을 실행할 수 있는 헬퍼 함수들.

사용 예시:
    from Agent_Structure.debate import run_debate

    result = run_debate("AI가 인간의 일자리를 대체하는 것은 긍정적이다")
    print(result.format_transcript())
    print(result.verdict)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generator

from langgraph.graph.state import CompiledStateGraph

from .graph import build_debate_graph
from .nodes import DEFAULT_CONTEXT_WINDOW, DEFAULT_MAX_SPEECH_CHARS
from .prompts import format_transcript_for_llm
from .state import CEDA_ROUNDS, DebateState, SpeechRecord


@dataclass
class DebateConfig:
    """토론 실행 설정. 중복 파라미터를 하나로 통합."""
    provider_name: str | None = None
    model_name: str | None = None
    aff_provider_name: str | None = None
    aff_model_name: str | None = None
    neg_provider_name: str | None = None
    neg_model_name: str | None = None
    judge_provider_name: str | None = None
    judge_model_name: str | None = None
    tools: list[Callable] | None = None
    max_speech_chars: int = DEFAULT_MAX_SPEECH_CHARS
    context_window: int = DEFAULT_CONTEXT_WINDOW
    aff_initial_notes: str = ""
    neg_initial_notes: str = ""


@dataclass
class DebateResult:
    """토론 결과."""
    proposition: str
    transcript: list[SpeechRecord]
    verdict: str

    def format_transcript(self) -> str:
        """사람이 읽을 수 있는 토론 기록을 반환한다."""
        return format_transcript_for_llm(self.transcript)


def _build_initial_state(
    proposition: str,
    *,
    aff_initial_notes: str = "",
    neg_initial_notes: str = "",
) -> DebateState:
    """토론 초기 상태를 생성한다.

    Args:
        proposition: 토론 논제
        aff_initial_notes: 긍정측 비공개 메모 초기값 (전략 문서 등)
        neg_initial_notes: 부정측 비공개 메모 초기값
    """
    state: DebateState = DebateState(
        proposition=proposition,
        round_sequence=list(CEDA_ROUNDS),
        transcript=[],
        current_round_index=0,
    )
    if aff_initial_notes:
        state["aff_private_notes"] = aff_initial_notes
    if neg_initial_notes:
        state["neg_private_notes"] = neg_initial_notes
    return state


def create_debate(
    proposition: str,
    *,
    config: DebateConfig | None = None,
    provider_name: str | None = None,
    model_name: str | None = None,
    aff_provider_name: str | None = None,
    aff_model_name: str | None = None,
    neg_provider_name: str | None = None,
    neg_model_name: str | None = None,
    judge_provider_name: str | None = None,
    judge_model_name: str | None = None,
    tools: list[Callable] | None = None,
    max_speech_chars: int | None = None,
    context_window: int | None = None,
    aff_initial_notes: str | None = None,
    neg_initial_notes: str | None = None,
    checkpointer: Any | None = None,
) -> tuple[CompiledStateGraph, DebateState]:
    """토론 그래프와 초기 상태를 생성한다.

    Args:
        config: DebateConfig 인스턴스. 개별 파라미터가 None이 아닌 값이면 config보다 우선.
        aff_initial_notes: 긍정측 비공개 메모 초기값 (전략 문서 주입용)
        neg_initial_notes: 부정측 비공개 메모 초기값

    Returns:
        (compiled_graph, initial_state)
    """
    cfg = config or DebateConfig()
    graph = build_debate_graph(
        provider_name=provider_name or cfg.provider_name,
        model_name=model_name or cfg.model_name,
        aff_provider_name=aff_provider_name or cfg.aff_provider_name,
        aff_model_name=aff_model_name or cfg.aff_model_name,
        neg_provider_name=neg_provider_name or cfg.neg_provider_name,
        neg_model_name=neg_model_name or cfg.neg_model_name,
        judge_provider_name=judge_provider_name or cfg.judge_provider_name,
        judge_model_name=judge_model_name or cfg.judge_model_name,
        tools=tools or cfg.tools,
        max_speech_chars=max_speech_chars if max_speech_chars is not None else cfg.max_speech_chars,
        context_window=context_window if context_window is not None else cfg.context_window,
        checkpointer=checkpointer,
    )
    initial_state = _build_initial_state(
        proposition,
        aff_initial_notes=aff_initial_notes if aff_initial_notes is not None else cfg.aff_initial_notes,
        neg_initial_notes=neg_initial_notes if neg_initial_notes is not None else cfg.neg_initial_notes,
    )
    return graph, initial_state


def run_debate(
    proposition: str,
    *,
    config: DebateConfig | None = None,
    provider_name: str | None = None,
    model_name: str | None = None,
    aff_provider_name: str | None = None,
    aff_model_name: str | None = None,
    neg_provider_name: str | None = None,
    neg_model_name: str | None = None,
    judge_provider_name: str | None = None,
    judge_model_name: str | None = None,
    tools: list[Callable] | None = None,
    max_speech_chars: int | None = None,
    context_window: int | None = None,
    aff_initial_notes: str | None = None,
    neg_initial_notes: str | None = None,
    thread_id: str = "debate-default",
) -> DebateResult:
    """CEDA 토론을 동기 실행하고 결과를 반환한다."""
    graph, initial_state = create_debate(
        proposition,
        config=config,
        provider_name=provider_name,
        model_name=model_name,
        aff_provider_name=aff_provider_name,
        aff_model_name=aff_model_name,
        neg_provider_name=neg_provider_name,
        neg_model_name=neg_model_name,
        judge_provider_name=judge_provider_name,
        judge_model_name=judge_model_name,
        tools=tools,
        max_speech_chars=max_speech_chars,
        context_window=context_window,
        aff_initial_notes=aff_initial_notes,
        neg_initial_notes=neg_initial_notes,
    )

    result = graph.invoke(
        initial_state,
        config={"configurable": {"thread_id": thread_id}},
    )

    return DebateResult(
        proposition=proposition,
        transcript=result.get("transcript", []),
        verdict=result.get("verdict", ""),
    )


async def arun_debate(
    proposition: str,
    *,
    config: DebateConfig | None = None,
    provider_name: str | None = None,
    model_name: str | None = None,
    aff_provider_name: str | None = None,
    aff_model_name: str | None = None,
    neg_provider_name: str | None = None,
    neg_model_name: str | None = None,
    judge_provider_name: str | None = None,
    judge_model_name: str | None = None,
    tools: list[Callable] | None = None,
    max_speech_chars: int | None = None,
    context_window: int | None = None,
    aff_initial_notes: str | None = None,
    neg_initial_notes: str | None = None,
    thread_id: str = "debate-default",
) -> DebateResult:
    """CEDA 토론을 비동기 실행하고 결과를 반환한다."""
    graph, initial_state = create_debate(
        proposition,
        config=config,
        provider_name=provider_name,
        model_name=model_name,
        aff_provider_name=aff_provider_name,
        aff_model_name=aff_model_name,
        neg_provider_name=neg_provider_name,
        neg_model_name=neg_model_name,
        judge_provider_name=judge_provider_name,
        judge_model_name=judge_model_name,
        tools=tools,
        max_speech_chars=max_speech_chars,
        context_window=context_window,
        aff_initial_notes=aff_initial_notes,
        neg_initial_notes=neg_initial_notes,
    )

    result = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": thread_id}},
    )

    return DebateResult(
        proposition=proposition,
        transcript=result.get("transcript", []),
        verdict=result.get("verdict", ""),
    )


def stream_debate(
    proposition: str,
    *,
    config: DebateConfig | None = None,
    provider_name: str | None = None,
    model_name: str | None = None,
    aff_provider_name: str | None = None,
    aff_model_name: str | None = None,
    neg_provider_name: str | None = None,
    neg_model_name: str | None = None,
    judge_provider_name: str | None = None,
    judge_model_name: str | None = None,
    tools: list[Callable] | None = None,
    max_speech_chars: int | None = None,
    context_window: int | None = None,
    aff_initial_notes: str | None = None,
    neg_initial_notes: str | None = None,
    thread_id: str = "debate-default",
) -> Generator[SpeechRecord, None, None]:
    """CEDA 토론을 라운드별로 스트리밍한다.

    각 라운드가 완료될 때마다 SpeechRecord를 yield한다.

    사용법:
        for speech in stream_debate("논제"):
            print(f"[{speech['round_id']}] {speech['speaker']}: ...")
    """
    graph, initial_state = create_debate(
        proposition,
        config=config,
        provider_name=provider_name,
        model_name=model_name,
        aff_provider_name=aff_provider_name,
        aff_model_name=aff_model_name,
        neg_provider_name=neg_provider_name,
        neg_model_name=neg_model_name,
        judge_provider_name=judge_provider_name,
        judge_model_name=judge_model_name,
        tools=tools,
        max_speech_chars=max_speech_chars,
        context_window=context_window,
        aff_initial_notes=aff_initial_notes,
        neg_initial_notes=neg_initial_notes,
    )

    for event in graph.stream(
        initial_state,
        config={"configurable": {"thread_id": thread_id}},
        stream_mode="updates",
    ):
        # event: {node_name: {state_updates}}
        for _node_name, updates in event.items():
            for speech in updates.get("transcript", []):
                yield speech

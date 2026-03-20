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

from dataclasses import dataclass
from typing import Any, Generator

from .graph import build_debate_graph
from .prompts import format_transcript_for_llm
from .state import CEDA_ROUNDS, DebateState, SpeechRecord


@dataclass
class DebateResult:
    """토론 결과."""
    proposition: str
    transcript: list[SpeechRecord]
    verdict: str

    def format_transcript(self) -> str:
        """사람이 읽을 수 있는 토론 기록을 반환한다."""
        return format_transcript_for_llm(self.transcript)


def _build_initial_state(proposition: str) -> DebateState:
    """토론 초기 상태를 생성한다."""
    return DebateState(
        proposition=proposition,
        round_sequence=list(CEDA_ROUNDS),
        transcript=[],
        current_round_index=0,
        aff_private_notes="",
        neg_private_notes="",
        verdict="",
    )


def create_debate(
    proposition: str,
    *,
    provider_name: str | None = None,
    model_name: str | None = None,
    aff_provider_name: str | None = None,
    aff_model_name: str | None = None,
    neg_provider_name: str | None = None,
    neg_model_name: str | None = None,
    judge_provider_name: str | None = None,
    judge_model_name: str | None = None,
    tools: list | None = None,
    checkpointer: Any | None = None,
) -> tuple[Any, DebateState]:
    """토론 그래프와 초기 상태를 생성한다.

    Returns:
        (compiled_graph, initial_state)
    """
    graph = build_debate_graph(
        provider_name=provider_name,
        model_name=model_name,
        aff_provider_name=aff_provider_name,
        aff_model_name=aff_model_name,
        neg_provider_name=neg_provider_name,
        neg_model_name=neg_model_name,
        judge_provider_name=judge_provider_name,
        judge_model_name=judge_model_name,
        tools=tools,
        checkpointer=checkpointer,
    )
    initial_state = _build_initial_state(proposition)
    return graph, initial_state


def run_debate(
    proposition: str,
    *,
    provider_name: str | None = None,
    model_name: str | None = None,
    aff_provider_name: str | None = None,
    aff_model_name: str | None = None,
    neg_provider_name: str | None = None,
    neg_model_name: str | None = None,
    judge_provider_name: str | None = None,
    judge_model_name: str | None = None,
    tools: list | None = None,
    thread_id: str = "debate-default",
) -> DebateResult:
    """CEDA 토론을 동기 실행하고 결과를 반환한다."""
    graph, initial_state = create_debate(
        proposition,
        provider_name=provider_name,
        model_name=model_name,
        aff_provider_name=aff_provider_name,
        aff_model_name=aff_model_name,
        neg_provider_name=neg_provider_name,
        neg_model_name=neg_model_name,
        judge_provider_name=judge_provider_name,
        judge_model_name=judge_model_name,
        tools=tools,
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
    provider_name: str | None = None,
    model_name: str | None = None,
    aff_provider_name: str | None = None,
    aff_model_name: str | None = None,
    neg_provider_name: str | None = None,
    neg_model_name: str | None = None,
    judge_provider_name: str | None = None,
    judge_model_name: str | None = None,
    tools: list | None = None,
    thread_id: str = "debate-default",
) -> DebateResult:
    """CEDA 토론을 비동기 실행하고 결과를 반환한다."""
    graph, initial_state = create_debate(
        proposition,
        provider_name=provider_name,
        model_name=model_name,
        aff_provider_name=aff_provider_name,
        aff_model_name=aff_model_name,
        neg_provider_name=neg_provider_name,
        neg_model_name=neg_model_name,
        judge_provider_name=judge_provider_name,
        judge_model_name=judge_model_name,
        tools=tools,
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
    provider_name: str | None = None,
    model_name: str | None = None,
    aff_provider_name: str | None = None,
    aff_model_name: str | None = None,
    neg_provider_name: str | None = None,
    neg_model_name: str | None = None,
    judge_provider_name: str | None = None,
    judge_model_name: str | None = None,
    tools: list | None = None,
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
        provider_name=provider_name,
        model_name=model_name,
        aff_provider_name=aff_provider_name,
        aff_model_name=aff_model_name,
        neg_provider_name=neg_provider_name,
        neg_model_name=neg_model_name,
        judge_provider_name=judge_provider_name,
        judge_model_name=judge_model_name,
        tools=tools,
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

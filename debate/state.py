"""
CEDA 토론 상태 정의.

DebateState는 LangGraph StateGraph의 상태 스키마로,
공개 transcript와 측별 비공개 메모를 분리 관리한다.
"""
from __future__ import annotations

import operator
from typing import Annotated, Literal
from typing_extensions import TypedDict


class SpeechRecord(TypedDict):
    """토론 발언 기록."""
    round_id: str       # "1AC", "CX_1AC_Q" 등
    speaker: str        # "affirmative" | "negative" | "judge"
    speech_type: str    # "constructive" | "cx_question" | "cx_answer" | "rebuttal" | "verdict"
    content: str


class RoundConfig(TypedDict):
    """라운드 설정."""
    round_id: str
    speaker: Literal["affirmative", "negative"]
    speech_type: str


class DebateState(TypedDict):
    """CEDA 토론 전체 상태.

    - transcript: append-only reducer로 각 노드가 발언을 추가
    - aff/neg_private_notes: 각 측의 비공개 전략 메모 (LastValue)
    """
    # 불변 설정
    proposition: str
    round_sequence: list[RoundConfig]

    # 공개 상태
    transcript: Annotated[list[SpeechRecord], operator.add]
    current_round_index: int

    # 비공개 상태 (측별 격리)
    aff_private_notes: str
    neg_private_notes: str

    # 최종 결과
    verdict: str


# ── CEDA 표준 라운드 시퀀스 (CX 질문/답변 분리) ──

CEDA_ROUNDS: list[RoundConfig] = [
    {"round_id": "1AC",      "speaker": "affirmative", "speech_type": "constructive"},
    {"round_id": "CX_1AC_Q", "speaker": "negative",    "speech_type": "cx_question"},
    {"round_id": "CX_1AC_A", "speaker": "affirmative", "speech_type": "cx_answer"},
    {"round_id": "1NC",      "speaker": "negative",    "speech_type": "constructive"},
    {"round_id": "CX_1NC_Q", "speaker": "affirmative", "speech_type": "cx_question"},
    {"round_id": "CX_1NC_A", "speaker": "negative",    "speech_type": "cx_answer"},
    {"round_id": "1AR",      "speaker": "affirmative", "speech_type": "rebuttal"},
    {"round_id": "1NR",      "speaker": "negative",    "speech_type": "rebuttal"},
    {"round_id": "2NR",      "speaker": "negative",    "speech_type": "rebuttal"},
    {"round_id": "2AR",      "speaker": "affirmative", "speech_type": "rebuttal"},
]

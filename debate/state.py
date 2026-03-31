"""
CEDA 토론 상태 정의.

DebateState는 LangGraph StateGraph의 상태 스키마로,
공개 transcript와 측별 비공개 메모를 분리 관리한다.
"""
from __future__ import annotations

import operator
from typing import Annotated, Literal
from typing_extensions import NotRequired, TypedDict


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

    # 비공개 상태 (측별 격리) — 초기 상태에서 없을 수 있음
    aff_private_notes: NotRequired[str]
    neg_private_notes: NotRequired[str]

    # 최종 결과 — 심판 판정 전까지 없음
    verdict: NotRequired[str]


class DebateNodeUpdate(TypedDict, total=False):
    """노드 함수가 반환하는 부분 상태 업데이트.

    total=False이므로 모든 필드가 optional — 노드가 필요한 필드만 반환 가능.
    """
    transcript: list[SpeechRecord]
    current_round_index: int
    aff_private_notes: str
    neg_private_notes: str
    verdict: str


# ── CEDA 표준 라운드 시퀀스 (CX 질문/답변 분리) ──

FINAL_REBUTTAL_ROUND_IDS: frozenset[str] = frozenset({"1AR", "1NR"})

CEDA_ROUNDS: list[RoundConfig] = [
    {"round_id": "1AC",      "speaker": "affirmative", "speech_type": "constructive"},
    {"round_id": "CX_1AC_Q", "speaker": "negative",    "speech_type": "cx_question"},
    {"round_id": "CX_1AC_A", "speaker": "affirmative", "speech_type": "cx_answer"},
    {"round_id": "1NC",      "speaker": "negative",    "speech_type": "constructive"},
    {"round_id": "CX_1NC_Q", "speaker": "affirmative", "speech_type": "cx_question"},
    {"round_id": "CX_1NC_A", "speaker": "negative",    "speech_type": "cx_answer"},
    {"round_id": "1AR",      "speaker": "affirmative", "speech_type": "rebuttal"},
    {"round_id": "1NR",      "speaker": "negative",    "speech_type": "rebuttal"},
]

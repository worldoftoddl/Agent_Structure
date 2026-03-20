"""
CEDA 토론 노드 함수.

LangGraph StateGraph의 각 노드에서 실행되는 함수들.
- debate_node: 토론 발언 생성 (입론, 교차조사, 반박)
- judge_node: 심판 판정
- route_next: 다음 라운드 라우팅
"""
from __future__ import annotations

import logging
import re
from typing import Any, Callable

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from .prompts import (
    format_transcript_for_llm,
    get_affirmative_system_prompt,
    get_judge_system_prompt,
    get_negative_system_prompt,
    get_round_instructions,
)
from .state import DebateState, SpeechRecord

logger = logging.getLogger(__name__)

# ── 비공개 메모 파싱 ──

_NOTES_PATTERN = re.compile(
    r"\[PRIVATE_NOTES\]\s*(.*?)\s*\[/PRIVATE_NOTES\]",
    re.DOTALL,
)


def _parse_speech_and_notes(raw: str) -> tuple[str, str]:
    """LLM 응답에서 공개 발언과 비공개 메모를 분리한다."""
    match = _NOTES_PATTERN.search(raw)
    if match:
        notes = match.group(1).strip()
        speech = _NOTES_PATTERN.sub("", raw).strip()
        return speech, notes
    return raw.strip(), ""


# ── 도구 호출 루프 ──

def _invoke_with_tools(
    llm: BaseChatModel,
    messages: list,
    tools: list,
    max_iterations: int = 5,
) -> str:
    """도구가 바인딩된 LLM을 호출하고, 도구 호출 루프를 실행한다."""
    llm_with_tools = llm.bind_tools(tools)

    # 도구를 이름으로 매핑
    tool_map: dict[str, Callable] = {}
    for t in tools:
        name = getattr(t, "name", getattr(t, "__name__", str(t)))
        tool_map[name] = t

    for _ in range(max_iterations):
        response: AIMessage = llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            return response.content or ""

        for tc in response.tool_calls:
            tool_fn = tool_map.get(tc["name"])
            if tool_fn is None:
                result = f"Error: tool '{tc['name']}' not found"
            else:
                try:
                    result = tool_fn.invoke(tc["args"])
                except Exception as e:
                    result = f"Error: {e}"

            messages.append(
                ToolMessage(content=str(result), tool_call_id=tc["id"])
            )

    # max_iterations 도달 시 마지막 응답 반환
    final = llm_with_tools.invoke(messages)
    return final.content or ""


# ── 노드 함수 팩토리 ──

def create_debate_node(
    aff_llm: BaseChatModel,
    neg_llm: BaseChatModel,
    tools: list | None = None,
) -> Callable[[DebateState], dict]:
    """토론 발언 노드 함수를 생성한다.

    클로저로 LLM 인스턴스와 도구를 캡처한다.
    """

    def debate_node(state: DebateState) -> dict:
        idx = state["current_round_index"]
        round_cfg = state["round_sequence"][idx]
        speaker = round_cfg["speaker"]
        round_id = round_cfg["round_id"]

        logger.info("토론 라운드 시작: %s (%s)", round_id, speaker)

        # 발언자에 따라 LLM과 비공개 메모 선택
        if speaker == "affirmative":
            llm = aff_llm
            system_prompt = get_affirmative_system_prompt(state["proposition"])
            my_notes = state.get("aff_private_notes", "")
        else:
            llm = neg_llm
            system_prompt = get_negative_system_prompt(state["proposition"])
            my_notes = state.get("neg_private_notes", "")

        # 메시지 구성
        messages: list = [SystemMessage(content=system_prompt)]

        # 공개 transcript
        transcript_text = format_transcript_for_llm(state.get("transcript", []))
        messages.append(
            HumanMessage(content=f"## 지금까지의 토론 기록\n\n{transcript_text}")
        )

        # 자기 측 비공개 메모만 주입 (상대측은 제외)
        if my_notes:
            messages.append(
                HumanMessage(
                    content=f"## 당신의 비공개 전략 메모 (상대측에게 보이지 않음)\n\n{my_notes}"
                )
            )

        # 라운드 지시사항
        round_instructions = get_round_instructions(round_cfg)
        messages.append(HumanMessage(content=round_instructions))

        # LLM 호출
        if tools:
            raw_response = _invoke_with_tools(llm, messages, tools)
        else:
            response = llm.invoke(messages)
            raw_response = response.content or ""

        # 공개 발언과 비공개 메모 분리
        speech_content, updated_notes = _parse_speech_and_notes(raw_response)

        logger.info("토론 라운드 완료: %s (%d자)", round_id, len(speech_content))

        # 상태 업데이트
        update: dict[str, Any] = {
            "transcript": [
                SpeechRecord(
                    round_id=round_id,
                    speaker=speaker,
                    speech_type=round_cfg["speech_type"],
                    content=speech_content,
                )
            ],
            "current_round_index": idx + 1,
        }

        if speaker == "affirmative":
            update["aff_private_notes"] = updated_notes
        else:
            update["neg_private_notes"] = updated_notes

        return update

    return debate_node


def create_judge_node(
    judge_llm: BaseChatModel,
) -> Callable[[DebateState], dict]:
    """심판 판정 노드 함수를 생성한다."""

    def judge_node(state: DebateState) -> dict:
        logger.info("심판 판정 시작")

        system_prompt = get_judge_system_prompt(state["proposition"])
        transcript_text = format_transcript_for_llm(state.get("transcript", []))

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=(
                    f"## 전체 토론 기록\n\n{transcript_text}\n\n"
                    "위 토론을 평가하고 판정을 내려주세요."
                )
            ),
        ]

        response = judge_llm.invoke(messages)
        verdict = response.content or ""

        logger.info("심판 판정 완료 (%d자)", len(verdict))

        return {
            "transcript": [
                SpeechRecord(
                    round_id="VERDICT",
                    speaker="judge",
                    speech_type="verdict",
                    content=verdict,
                )
            ],
            "verdict": verdict,
        }

    return judge_node


def route_next(state: DebateState) -> str:
    """다음 노드를 결정하는 라우팅 함수.

    라운드가 남아있으면 'continue', 모두 완료면 'judge'.
    """
    idx = state["current_round_index"]
    total = len(state["round_sequence"])

    if idx < total:
        return "continue"
    return "judge"

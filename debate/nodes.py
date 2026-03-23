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
    BaseMessage,
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

DEFAULT_MAX_SPEECH_CHARS: int = 1200
DEFAULT_CONTEXT_WINDOW: int = 3

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


def _truncate_speech(speech: str, max_chars: int) -> str:
    """공개 발언을 max_chars 이내로 문장 단위 절단한다."""
    if len(speech) <= max_chars:
        return speech

    truncated = speech[:max_chars]
    # 마지막 문장 종결자를 역순 탐색
    last_end = -1
    for i in range(len(truncated) - 1, -1, -1):
        if truncated[i] in ".!?\n":
            last_end = i + 1
            break

    if last_end > max_chars * 0.5:
        return truncated[:last_end].rstrip()

    return truncated.rstrip() + "..."


def _condense_speech(
    llm: BaseChatModel,
    speech: str,
    max_chars: int,
) -> str:
    """LLM을 사용하여 발언을 max_chars 이내로 요약 압축한다.

    요약 결과도 초과하면 _truncate_speech로 폴백한다.
    """
    if len(speech) <= max_chars:
        return speech

    # 목표 글자 수를 80%로 설정하여 초과 방지 여유 확보
    target = int(max_chars * 0.8)
    prompt = (
        f"다음 토론 발언을 반드시 {target}자 이내로 압축하세요.\n"
        f"현재 {len(speech)}자이며, {target}자 이하로 줄여야 합니다.\n"
        "규칙:\n"
        "- 핵심 논점과 근거만 남기고 수식어·반복·예시를 과감히 삭제\n"
        "- 요약문만 출력. 서두·설명·메타 코멘트 금지\n\n"
        f"--- 원문 ---\n{speech}"
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    condensed = (response.content or "").strip()

    if len(condensed) > max_chars:
        logger.warning("LLM 요약도 %d자 초과 → 강제 절단", len(condensed))
        return _truncate_speech(condensed, max_chars)
    return condensed


# ── 도구 호출 루프 ──

def _invoke_with_tools(
    llm: BaseChatModel,
    messages: list[Any],
    tools: list[Callable],
    max_iterations: int = 5,
) -> str:
    """도구가 바인딩된 LLM을 호출하고, 도구 호출 루프를 실행한다."""
    messages = list(messages)  # 방어적 복사 — 호출자의 리스트를 변형하지 않음
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
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception as e:
                    logger.warning(
                        "도구 '%s' 호출 실패 (%s): %s", tc["name"], type(e).__name__, e
                    )
                    result = f"Error: {e}"

            messages.append(
                ToolMessage(content=str(result), tool_call_id=tc["id"])
            )

    # max_iterations 도달 시 도구 미바인딩 LLM으로 최종 텍스트 응답 유도
    final = llm.invoke(messages)
    return final.content or ""


# ── 노드 함수 팩토리 ──

def create_debate_node(
    aff_llm: BaseChatModel,
    neg_llm: BaseChatModel,
    tools: list[Callable] | None = None,
    max_speech_chars: int = DEFAULT_MAX_SPEECH_CHARS,
    context_window: int = DEFAULT_CONTEXT_WINDOW,
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
        messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]

        # 공개 transcript (윈도우 적용)
        transcript_text = format_transcript_for_llm(
            state.get("transcript", []),
            context_window=context_window,
        )
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
        round_instructions = get_round_instructions(round_cfg, max_speech_chars=max_speech_chars)
        messages.append(HumanMessage(content=round_instructions))

        # LLM 호출
        if tools:
            raw_response = _invoke_with_tools(llm, messages, tools)
        else:
            response = llm.invoke(messages)
            raw_response = response.content or ""

        # 공개 발언과 비공개 메모 분리
        speech_content, updated_notes = _parse_speech_and_notes(raw_response)

        # 공개 발언 길이 제한 적용 (LLM 요약 → 폴백 절단)
        if max_speech_chars > 0 and len(speech_content) > max_speech_chars:
            original_len = len(speech_content)
            speech_content = _condense_speech(llm, speech_content, max_speech_chars)
            logger.info(
                "발언 요약 압축: %s (%d → %d자)",
                round_id, original_len, len(speech_content),
            )

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

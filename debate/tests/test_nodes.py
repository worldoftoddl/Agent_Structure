"""
Phase 1 테스트: nodes.py 수정사항에 대한 TDD 테스트.

대상 이슈:
  HIGH-1/2: _extract_content 헬퍼 (response.content 타입 안전성)
  HIGH-3: _invoke_with_tools 도구 디스패치 (BaseTool vs plain callable)
  HIGH-6: 노드 반환 타입 DebateNodeUpdate
  M-5: 매직 넘버 상수화
  M-6: _condense_speech 폴백
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ── HIGH-1/2: _extract_content 테스트 ──


class TestExtractContent:
    """LLM response.content의 다양한 형태를 str로 안전하게 변환."""

    def _fn(self, content):
        from Agent_Structure.debate.nodes import _extract_content
        return _extract_content(content)

    def test_str_passthrough(self):
        """일반 문자열은 그대로 반환."""
        assert self._fn("hello world") == "hello world"

    def test_empty_str(self):
        """빈 문자열은 빈 문자열 반환."""
        assert self._fn("") == ""

    def test_none_returns_empty(self):
        """None이면 빈 문자열 반환."""
        assert self._fn(None) == ""

    def test_list_of_str(self):
        """문자열 리스트는 결합."""
        result = self._fn(["hello", " world"])
        assert result == "hello world"

    def test_list_of_dict_with_text(self):
        """dict 리스트에서 text 필드 추출."""
        content = [{"type": "text", "text": "hello"}, {"type": "text", "text": " world"}]
        result = self._fn(content)
        assert result == "hello world"

    def test_mixed_list(self):
        """str과 dict이 혼합된 리스트."""
        content = ["prefix ", {"type": "text", "text": "body"}]
        result = self._fn(content)
        assert "prefix" in result
        assert "body" in result

    def test_empty_list(self):
        """빈 리스트는 빈 문자열."""
        assert self._fn([]) == ""

    def test_dict_without_text_key(self):
        """text 키가 없는 dict은 무시."""
        content = [{"type": "image", "url": "..."}]
        result = self._fn(content)
        assert result == ""


# ── HIGH-3: 도구 디스패치 테스트 ──


class TestInvokeWithToolsDispatch:
    """_invoke_with_tools가 BaseTool과 plain callable을 모두 안전하게 처리."""

    def test_plain_callable_dispatched(self):
        """일반 함수에 .invoke() 대신 직접 호출."""
        from langchain_core.messages import AIMessage, HumanMessage

        def my_tool(query: str) -> str:
            return f"result: {query}"
        my_tool.__name__ = "my_tool"

        # LLM 모킹: 첫 호출에서 tool_call, 두 번째에서 텍스트 응답
        mock_llm = MagicMock()

        # 도구 호출 응답
        tool_call_response = AIMessage(
            content="",
            tool_calls=[{"id": "tc1", "name": "my_tool", "args": {"query": "test"}}],
        )
        # 최종 텍스트 응답
        final_response = AIMessage(content="done")

        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.side_effect = [tool_call_response, final_response]

        from Agent_Structure.debate.nodes import _invoke_with_tools
        result = _invoke_with_tools(mock_llm, [HumanMessage(content="hi")], [my_tool])

        assert result == "done"

    def test_basetool_dispatched(self):
        """BaseTool은 .invoke()로 호출."""
        from langchain_core.messages import AIMessage, HumanMessage
        from langchain_core.tools import BaseTool

        mock_tool = MagicMock(spec=BaseTool)
        mock_tool.name = "search"
        mock_tool.invoke.return_value = "search result"

        mock_llm = MagicMock()
        tool_call_response = AIMessage(
            content="",
            tool_calls=[{"id": "tc1", "name": "search", "args": {"q": "test"}}],
        )
        final_response = AIMessage(content="found it")

        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.side_effect = [tool_call_response, final_response]

        from Agent_Structure.debate.nodes import _invoke_with_tools
        result = _invoke_with_tools(mock_llm, [HumanMessage(content="hi")], [mock_tool])

        assert result == "found it"
        mock_tool.invoke.assert_called_once()


# ── M-5: 매직 넘버 상수 테스트 ──


class TestConstants:
    """매직 넘버가 명명 상수로 존재하는지 확인."""

    def test_min_sentence_ratio_exists(self):
        from Agent_Structure.debate.nodes import _MIN_SENTENCE_RATIO
        assert isinstance(_MIN_SENTENCE_RATIO, float)
        assert 0 < _MIN_SENTENCE_RATIO < 1


# ── M-6: _condense_speech 폴백 테스트 ──


class TestCondenseSpeechFallback:
    """LLM 요약 실패 시 _truncate_speech로 안전하게 폴백."""

    def test_llm_failure_falls_back_to_truncate(self):
        """LLM 호출이 실패하면 강제 절단으로 폴백."""
        from Agent_Structure.debate.nodes import _condense_speech

        long_speech = "가" * 1000  # 800자 초과
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = RuntimeError("API Error")

        result = _condense_speech(mock_llm, long_speech, 800)

        # 폴백으로 절단됨 (문장 종결자 없으면 "..." 3자 추가 가능)
        assert len(result) <= 800 + 3
        assert len(result) < len(long_speech)
        # 예외가 전파되지 않았음
        assert isinstance(result, str)

    def test_normal_operation_unchanged(self):
        """LLM이 정상 응답하면 요약 결과 반환."""
        from unittest.mock import MagicMock
        from Agent_Structure.debate.nodes import _condense_speech

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "짧은 요약"
        mock_llm.invoke.return_value = mock_response

        long_speech = "가" * 1000
        result = _condense_speech(mock_llm, long_speech, 800)

        assert result == "짧은 요약"


# ── HIGH-6: DebateNodeUpdate TypedDict 테스트 ──


class TestDebateNodeUpdate:
    """DebateNodeUpdate TypedDict가 올바르게 정의되어 있는지 확인."""

    def test_typeddict_exists(self):
        from Agent_Structure.debate.state import DebateNodeUpdate
        assert hasattr(DebateNodeUpdate, "__annotations__")

    def test_required_fields(self):
        from Agent_Structure.debate.state import DebateNodeUpdate
        annotations = DebateNodeUpdate.__annotations__
        assert "transcript" in annotations
        assert "current_round_index" in annotations

    def test_optional_fields(self):
        """비공개 메모와 verdict는 optional."""
        from Agent_Structure.debate.state import DebateNodeUpdate
        # total=False이므로 모든 필드가 optional이거나,
        # NotRequired로 표시된 필드가 있어야 함
        annotations = DebateNodeUpdate.__annotations__
        assert "aff_private_notes" in annotations
        assert "neg_private_notes" in annotations
        assert "verdict" in annotations

    def test_is_dict_compatible(self):
        """TypedDict는 dict와 호환."""
        from Agent_Structure.debate.state import DebateNodeUpdate, SpeechRecord

        update: DebateNodeUpdate = {
            "transcript": [
                SpeechRecord(
                    round_id="1AC",
                    speaker="affirmative",
                    speech_type="constructive",
                    content="test",
                )
            ],
            "current_round_index": 1,
        }
        assert isinstance(update, dict)

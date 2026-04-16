"""
TDD 테스트: 비공개 메모 초기값 주입 기능.

요구사항:
- 사용자가 미리 준비한 전략 문서를 각 측 비공개 메모에 주입할 수 있어야 함
- aff_initial_notes는 aff_private_notes로, neg_initial_notes는 neg_private_notes로 주입됨
- DebateConfig로도, 개별 파라미터로도 전달 가능해야 함
- 개별 파라미터가 config보다 우선함
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ── 1. _build_initial_state 테스트 ──


class TestBuildInitialStateWithNotes:
    """_build_initial_state가 초기 비공개 메모를 주입하는지 확인."""

    def test_no_notes_returns_state_without_notes(self):
        """파라미터 없이 호출하면 비공개 메모 필드는 비어있거나 없음."""
        from Agent_Structure.debate.runner import _build_initial_state

        state = _build_initial_state("논제")
        # 필드가 없거나 빈 문자열이어야 함 (둘 다 허용)
        assert not state.get("aff_private_notes", "")
        assert not state.get("neg_private_notes", "")

    def test_aff_initial_notes_injected(self):
        """aff_initial_notes가 aff_private_notes로 주입되어야 함."""
        from Agent_Structure.debate.runner import _build_initial_state

        strategy = "긍정측 전략: 세 가지 논점으로 접근"
        state = _build_initial_state("논제", aff_initial_notes=strategy)

        assert state.get("aff_private_notes") == strategy
        # neg에는 주입되지 않아야 함 (격리 원칙)
        assert not state.get("neg_private_notes", "")

    def test_neg_initial_notes_injected(self):
        """neg_initial_notes가 neg_private_notes로 주입되어야 함."""
        from Agent_Structure.debate.runner import _build_initial_state

        strategy = "부정측 전략: 반박 중심 접근"
        state = _build_initial_state("논제", neg_initial_notes=strategy)

        assert state.get("neg_private_notes") == strategy
        assert not state.get("aff_private_notes", "")

    def test_both_notes_injected(self):
        """양측 메모를 동시에 주입할 수 있어야 함."""
        from Agent_Structure.debate.runner import _build_initial_state

        aff_strategy = "긍정측 전략"
        neg_strategy = "부정측 전략"
        state = _build_initial_state(
            "논제",
            aff_initial_notes=aff_strategy,
            neg_initial_notes=neg_strategy,
        )

        assert state.get("aff_private_notes") == aff_strategy
        assert state.get("neg_private_notes") == neg_strategy

    def test_state_structure_preserved(self):
        """초기 메모 주입이 다른 필드를 깨뜨리지 않아야 함."""
        from Agent_Structure.debate.runner import _build_initial_state

        state = _build_initial_state(
            "논제",
            aff_initial_notes="aff",
            neg_initial_notes="neg",
        )

        assert state["proposition"] == "논제"
        assert state["current_round_index"] == 0
        assert state["transcript"] == []
        assert len(state["round_sequence"]) > 0


# ── 2. DebateConfig 필드 테스트 ──


class TestDebateConfigInitialNotes:
    """DebateConfig에 초기 메모 필드가 추가되어야 함."""

    def test_default_empty_string(self):
        """기본값은 빈 문자열."""
        from Agent_Structure.debate.runner import DebateConfig

        cfg = DebateConfig()
        assert cfg.aff_initial_notes == ""
        assert cfg.neg_initial_notes == ""

    def test_can_set_in_constructor(self):
        """생성자에서 설정 가능."""
        from Agent_Structure.debate.runner import DebateConfig

        cfg = DebateConfig(
            aff_initial_notes="aff 전략",
            neg_initial_notes="neg 전략",
        )
        assert cfg.aff_initial_notes == "aff 전략"
        assert cfg.neg_initial_notes == "neg 전략"


# ── 3. create_debate 통합 테스트 ──


class TestCreateDebateInitialNotes:
    """create_debate가 초기 메모를 초기 상태에 전달해야 함."""

    @patch("Agent_Structure.debate.runner.build_debate_graph")
    def test_individual_params_injected(self, mock_build):
        """개별 파라미터로 전달한 메모가 초기 상태에 반영됨."""
        from Agent_Structure.debate.runner import create_debate

        mock_build.return_value = MagicMock()

        graph, state = create_debate(
            "논제",
            aff_initial_notes="긍정 전략",
            neg_initial_notes="부정 전략",
        )

        assert state.get("aff_private_notes") == "긍정 전략"
        assert state.get("neg_private_notes") == "부정 전략"

    @patch("Agent_Structure.debate.runner.build_debate_graph")
    def test_config_params_injected(self, mock_build):
        """DebateConfig로 전달한 메모가 초기 상태에 반영됨."""
        from Agent_Structure.debate.runner import DebateConfig, create_debate

        mock_build.return_value = MagicMock()

        cfg = DebateConfig(
            aff_initial_notes="config 긍정",
            neg_initial_notes="config 부정",
        )
        graph, state = create_debate("논제", config=cfg)

        assert state.get("aff_private_notes") == "config 긍정"
        assert state.get("neg_private_notes") == "config 부정"

    @patch("Agent_Structure.debate.runner.build_debate_graph")
    def test_individual_param_overrides_config(self, mock_build):
        """개별 파라미터가 config보다 우선."""
        from Agent_Structure.debate.runner import DebateConfig, create_debate

        mock_build.return_value = MagicMock()

        cfg = DebateConfig(
            aff_initial_notes="config 긍정",
            neg_initial_notes="config 부정",
        )
        graph, state = create_debate(
            "논제",
            config=cfg,
            aff_initial_notes="override 긍정",
        )

        assert state.get("aff_private_notes") == "override 긍정"
        # neg은 config 값 유지
        assert state.get("neg_private_notes") == "config 부정"

    @patch("Agent_Structure.debate.runner.build_debate_graph")
    def test_no_notes_no_error(self, mock_build):
        """메모 파라미터 없이 호출해도 정상 동작."""
        from Agent_Structure.debate.runner import create_debate

        mock_build.return_value = MagicMock()

        graph, state = create_debate("논제")
        assert state["proposition"] == "논제"


# ── 4. run_debate / stream_debate 파라미터 존재 확인 ──


class TestRunnerSignatures:
    """고수준 runner 함수들이 초기 메모 파라미터를 받을 수 있어야 함."""

    def test_run_debate_accepts_initial_notes(self):
        """run_debate 시그니처에 initial_notes 파라미터 존재."""
        import inspect

        from Agent_Structure.debate.runner import run_debate

        sig = inspect.signature(run_debate)
        assert "aff_initial_notes" in sig.parameters
        assert "neg_initial_notes" in sig.parameters

    def test_arun_debate_accepts_initial_notes(self):
        """arun_debate 시그니처에 initial_notes 파라미터 존재."""
        import inspect

        from Agent_Structure.debate.runner import arun_debate

        sig = inspect.signature(arun_debate)
        assert "aff_initial_notes" in sig.parameters
        assert "neg_initial_notes" in sig.parameters

    def test_stream_debate_accepts_initial_notes(self):
        """stream_debate 시그니처에 initial_notes 파라미터 존재."""
        import inspect

        from Agent_Structure.debate.runner import stream_debate

        sig = inspect.signature(stream_debate)
        assert "aff_initial_notes" in sig.parameters
        assert "neg_initial_notes" in sig.parameters

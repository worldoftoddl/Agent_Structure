"""
평가 양식 기반 프롬프트 테스트.

평가 양식의 채점 체계:
  - 입론 40점 (주장 명확성 15점 + 논거 논리 25점)
  - 교차조사 30점 (질문 전략성 15점 + 답변 적절성 15점)
  - 반론 20점 (반박 적절성 10점 + 반박 근거 10점)
  - 전달 10점 (전달력/매너)
  - 합계 100점
"""
from __future__ import annotations

import pytest

PROPOSITION = "테스트 논제"


# ── 심판 프롬프트: 배점 체계 반영 ──


class TestJudgePromptScoring:
    """심판 프롬프트가 평가 양식의 4개 영역 + 배점을 포함하는지 확인."""

    def _prompt(self) -> str:
        from Agent_Structure.debate.prompts import get_judge_system_prompt
        return get_judge_system_prompt(PROPOSITION)

    def test_contains_scoring_categories(self):
        """4개 평가 영역(입론, 교차조사, 반론, 전달)이 모두 포함."""
        prompt = self._prompt()
        assert "입론" in prompt
        assert "교차조사" in prompt
        assert "반론" in prompt
        assert "전달" in prompt

    def test_contains_point_allocations(self):
        """각 영역의 배점이 명시되어 있음."""
        prompt = self._prompt()
        # 입론 40점 (15 + 25)
        assert "15" in prompt
        assert "25" in prompt
        # 교차조사 30점
        assert "30" in prompt or ("15" in prompt)  # 15+15
        # 반론 20점
        assert "10" in prompt  # 10+10
        # 총점
        assert "100" in prompt

    def test_contains_total_score(self):
        """100점 만점 체계가 명시됨."""
        prompt = self._prompt()
        assert "100" in prompt

    def test_output_format_has_scoring_table(self):
        """출력 형식에 항목별 점수 기재 구조가 있음."""
        prompt = self._prompt()
        # 긍정측/부정측 각각의 점수를 기재하는 구조
        assert "긍정측" in prompt
        assert "부정측" in prompt
        assert "총점" in prompt

    def test_winner_determination(self):
        """총점 기반 승자 결정 지시가 있음."""
        prompt = self._prompt()
        assert "승자" in prompt


# ── 토론자 프롬프트: 평가 기준 인지 ──


class TestDebaterPromptAwareness:
    """토론자가 심판의 평가 기준(배점)을 인지하도록 안내."""

    def test_affirmative_knows_scoring(self):
        from Agent_Structure.debate.prompts import get_affirmative_system_prompt
        prompt = get_affirmative_system_prompt(PROPOSITION)
        # 토론자가 어떤 기준으로 평가받는지 알아야 함
        assert "입론" in prompt or "40" in prompt
        assert "평가" in prompt or "채점" in prompt or "배점" in prompt

    def test_negative_knows_scoring(self):
        from Agent_Structure.debate.prompts import get_negative_system_prompt
        prompt = get_negative_system_prompt(PROPOSITION)
        assert "입론" in prompt or "40" in prompt
        assert "평가" in prompt or "채점" in prompt or "배점" in prompt


# ── 라운드 지시사항: 채점 기준 반영 ──


class TestRoundInstructionsScoring:
    """각 라운드 지시사항이 해당 영역의 채점 기준을 반영."""

    def _instructions(self, round_id: str, speech_type: str) -> str:
        from Agent_Structure.debate.prompts import get_round_instructions
        from Agent_Structure.debate.state import RoundConfig
        cfg = RoundConfig(round_id=round_id, speaker="affirmative", speech_type=speech_type)
        return get_round_instructions(cfg)

    def test_constructive_mentions_scoring(self):
        """입론 지시사항에 채점 기준(주장 명확성, 논거 논리) 반영."""
        instructions = self._instructions("1AC", "constructive")
        # 주장 명확성과 논거 논리가 채점됨을 인지
        assert "주장" in instructions
        assert "논거" in instructions or "근거" in instructions

    def test_cx_question_mentions_scoring(self):
        """교차조사 질문 지시사항에 채점 기준 반영."""
        instructions = self._instructions("CX_1AC_Q", "cx_question")
        assert "질문" in instructions

    def test_cx_answer_mentions_scoring(self):
        """교차조사 답변 지시사항에 채점 기준 반영."""
        instructions = self._instructions("CX_1AC_A", "cx_answer")
        assert "답변" in instructions

    def test_rebuttal_mentions_scoring(self):
        """반론 지시사항에 채점 기준 반영."""
        instructions = self._instructions("1AR", "rebuttal")
        assert "반박" in instructions

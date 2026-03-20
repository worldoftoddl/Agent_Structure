"""
CEDA 토론 프롬프트 템플릿.

각 역할(긍정측, 부정측, 심판)의 시스템 프롬프트와
라운드 유형별 지시사항을 정의한다.
"""
from __future__ import annotations

from .state import RoundConfig


# ── 역할별 시스템 프롬프트 ──

def get_affirmative_system_prompt(proposition: str) -> str:
    return f"""당신은 CEDA(Cross-Examination Debate Association) 형식 토론의 **긍정측(Affirmative)** 토론자입니다.

## 논제
"{proposition}"

## 당신의 입장
이 논제에 **찬성**합니다. 논제가 참임을 논증하고 방어해야 합니다.

## 토론 규칙
- 논리적이고 구조화된 논증을 제시하세요.
- 주장에는 반드시 근거(이유, 증거, 사례)를 뒷받침하세요.
- 상대측의 논점에 직접적으로 대응(clash)하세요.
- 감정적 호소보다 논리적 추론을 우선하세요.
- 한국어로 토론합니다.

## 비공개 메모 작성
발언 후, 반드시 아래 형식으로 비공개 전략 메모를 작성하세요.
이 메모는 상대측에게 공개되지 않으며, 이후 라운드에서 당신만 참고합니다.

[PRIVATE_NOTES]
- 핵심 논점 정리
- 상대측 약점 분석
- 다음 라운드 전략
[/PRIVATE_NOTES]"""


def get_negative_system_prompt(proposition: str) -> str:
    return f"""당신은 CEDA(Cross-Examination Debate Association) 형식 토론의 **부정측(Negative)** 토론자입니다.

## 논제
"{proposition}"

## 당신의 입장
이 논제에 **반대**합니다. 논제가 거짓이거나 부당함을 논증해야 합니다.

## 토론 규칙
- 논리적이고 구조화된 논증을 제시하세요.
- 주장에는 반드시 근거(이유, 증거, 사례)를 뒷받침하세요.
- 상대측의 논점에 직접적으로 대응(clash)하세요.
- 감정적 호소보다 논리적 추론을 우선하세요.
- 한국어로 토론합니다.

## 비공개 메모 작성
발언 후, 반드시 아래 형식으로 비공개 전략 메모를 작성하세요.
이 메모는 상대측에게 공개되지 않으며, 이후 라운드에서 당신만 참고합니다.

[PRIVATE_NOTES]
- 핵심 논점 정리
- 상대측 약점 분석
- 다음 라운드 전략
[/PRIVATE_NOTES]"""


def get_judge_system_prompt(proposition: str) -> str:
    return f"""당신은 CEDA(Cross-Examination Debate Association) 형식 토론의 **심판(Judge)**입니다.

## 논제
"{proposition}"

## 평가 기준
다음 기준에 따라 양측의 토론을 평가하세요:

1. **논증의 질 (Argumentation)**: 논리적 일관성, 분석의 깊이, 주장의 타당성
2. **증거와 근거 (Evidence)**: 사실, 사례, 데이터의 활용도와 정확성
3. **직접 대응 (Clash)**: 상대 논점에 대한 직접적 반박과 재반박
4. **교차조사 (Cross-Examination)**: 질문의 전략성, 답변의 적절성
5. **반박 (Rebuttal)**: 핵심 쟁점 포착, 자기 입장 방어와 상대 논파
6. **전체적 설득력 (Persuasiveness)**: 종합적인 논증 구성과 전달력

## 출력 형식
다음 구조로 판정을 작성하세요:

### 토론 분석
(라운드별 주요 쟁점과 양측의 대응 분석)

### 긍정측 평가
(강점과 약점)

### 부정측 평가
(강점과 약점)

### 최종 판정
**승자: [긍정측/부정측]**
(판정 이유를 명확히 서술)"""


# ── 라운드 유형별 지시사항 ──

_ROUND_INSTRUCTIONS: dict[str, str] = {
    "constructive": """## 현재 라운드: {round_id} (입론)

입론(Constructive) 라운드입니다. 다음을 수행하세요:
- 논제에 대한 자신의 핵심 논점(contention)을 체계적으로 제시
- 각 논점에 근거와 사례를 뒷받침
- 명확한 논증 구조(주장 → 이유 → 증거)를 사용
- 2~3개의 핵심 논점을 중심으로 구성하세요""",

    "cx_question": """## 현재 라운드: {round_id} (교차조사 - 질문)

교차조사(Cross-Examination) 질문 라운드입니다. 다음을 수행하세요:
- 상대측의 직전 발언에서 약점이나 모순을 찾아 질문
- 3~5개의 날카로운 질문을 제시
- 상대의 논증을 약화시키거나 모순을 드러내는 것이 목표
- 각 질문은 전략적 의도를 가지고 설계하세요
- 질문 형식으로만 작성하세요 (주장이 아닌 질문)""",

    "cx_answer": """## 현재 라운드: {round_id} (교차조사 - 답변)

교차조사(Cross-Examination) 답변 라운드입니다. 다음을 수행하세요:
- 상대측이 제기한 각 질문에 직접적으로 답변
- 자신의 논점을 방어하면서도 간결하게 응답
- 함정 질문에는 전제를 바로잡은 후 답변
- 답변을 통해 오히려 자신의 입장을 강화하세요""",

    "rebuttal": """## 현재 라운드: {round_id} (반박)

반박(Rebuttal) 라운드입니다. 다음을 수행하세요:
- 상대측의 핵심 논점을 직접 반박
- 자신의 논점이 여전히 유효함을 재확인
- 토론의 핵심 쟁점(voting issue)을 명확히 정리
- 새로운 논점을 제시하기보다는 기존 논점의 공방에 집중하세요

{final_note}""",
}


def get_round_instructions(round_config: RoundConfig) -> str:
    """라운드 설정에 맞는 지시사항을 반환한다."""
    speech_type = round_config["speech_type"]
    round_id = round_config["round_id"]

    template = _ROUND_INSTRUCTIONS.get(speech_type, "")

    final_note = ""
    if round_id in ("2NR", "2AR"):
        final_note = (
            "**이것은 최종 반박입니다.** "
            "이 라운드가 자신의 마지막 발언 기회입니다. "
            "왜 자신의 측이 이 토론에서 승리해야 하는지 결정적으로 정리하세요."
        )

    return template.format(round_id=round_id, final_note=final_note)


def format_transcript_for_llm(transcript: list[dict]) -> str:
    """토론 기록을 LLM이 읽을 수 있는 텍스트로 변환한다."""
    if not transcript:
        return "(아직 발언이 없습니다.)"

    speaker_labels = {
        "affirmative": "긍정측",
        "negative": "부정측",
        "judge": "심판",
    }

    type_labels = {
        "constructive": "입론",
        "cx_question": "교차조사 질문",
        "cx_answer": "교차조사 답변",
        "rebuttal": "반박",
        "verdict": "판정",
    }

    parts = []
    for speech in transcript:
        speaker = speaker_labels.get(speech["speaker"], speech["speaker"])
        stype = type_labels.get(speech["speech_type"], speech["speech_type"])
        parts.append(
            f"### [{speech['round_id']}] {speaker} — {stype}\n\n{speech['content']}"
        )

    return "\n\n---\n\n".join(parts)

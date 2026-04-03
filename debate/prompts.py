"""
CEDA 토론 프롬프트 템플릿.

각 역할(긍정측, 부정측, 심판)의 시스템 프롬프트와
라운드 유형별 지시사항을 정의한다.
"""
from __future__ import annotations

from .state import FINAL_REBUTTAL_ROUND_IDS, RoundConfig, SpeechRecord

DEFAULT_SUMMARY_CHARS: int = 200


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

## 평가 배점 (심판 채점 기준)
심판은 아래 기준으로 채점합니다. 배점이 높은 영역에 집중하세요.
- **입론 40점**: 주장 명확성(15) + 논거 논리·근거(25)
- **교차조사 30점**: 질문 전략성(15) + 답변 적절성(15)
- **반론 20점**: 반박 적절성(10) + 반박 근거(10)
- **전달 10점**: 논증 구성과 전달력

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

## 평가 배점 (심판 채점 기준)
심판은 아래 기준으로 채점합니다. 배점이 높은 영역에 집중하세요.
- **입론 40점**: 주장 명확성(15) + 논거 논리·근거(25)
- **교차조사 30점**: 질문 전략성(15) + 답변 적절성(15)
- **반론 20점**: 반박 적절성(10) + 반박 근거(10)
- **전달 10점**: 논증 구성과 전달력

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

## 채점 기준 (100점 만점)

아래 4개 영역의 세부 항목에 따라 긍정측과 부정측에 각각 점수를 부여하세요.

### 1. 입론 (40점)
| 세부 항목 | 배점 | 평가 내용 |
|-----------|------|-----------|
| 주장 명확성 | 15점 | 해당 측의 주장을 명확하게 제시하였는가? |
| 논거 논리 | 25점 | 주요 논거의 논리를 적절하게 제시하였는가? 근거(사례, 데이터)가 충분한가? |

### 2. 교차조사 (30점)
| 세부 항목 | 배점 | 평가 내용 |
|-----------|------|-----------|
| 질문 전략성 | 15점 | 상대측 주장의 약점이나 모순을 파악하여 논리적으로 적절한 질문을 제시하였는가? |
| 답변 적절성 | 15점 | 상대측 질문에 대해 자신의 논거를 방어하며 적절하게 답변하였는가? |

### 3. 반론 (20점)
| 세부 항목 | 배점 | 평가 내용 |
|-----------|------|-----------|
| 반박 적절성 | 10점 | 상대측의 주요 논거에 대한 반박이 적절한가? 새로운 논증이 타당한가? |
| 반박 근거 | 10점 | 반박에 대한 근거(자료, 논증, 사례 등)를 적절히 제시하였는가? |

### 4. 전달 (10점)
| 세부 항목 | 배점 | 평가 내용 |
|-----------|------|-----------|
| 전달력 | 10점 | 전반적인 논증의 구성, 전달력, 설득력이 적절하였는가? |

## 출력 형식

다음 구조로 판정을 작성하세요:

### 토론 분석
(라운드별 주요 쟁점과 양측의 대응 분석)

### 채점표

| 평가 영역 | 세부 항목 | 긍정측 | 부정측 |
|-----------|-----------|--------|--------|
| 입론 (40) | 주장 명확성 (15) | /15 | /15 |
| | 논거 논리 (25) | /25 | /25 |
| 교차조사 (30) | 질문 전략성 (15) | /15 | /15 |
| | 답변 적절성 (15) | /15 | /15 |
| 반론 (20) | 반박 적절성 (10) | /10 | /10 |
| | 반박 근거 (10) | /10 | /10 |
| 전달 (10) | 전달력 (10) | /10 | /10 |
| **총점** | | **/100** | **/100** |

### 긍정측 평가
(강점과 약점을 항목별로 서술)

### 부정측 평가
(강점과 약점을 항목별로 서술)

### 최종 판정
**승자: [긍정측/부정측]**
(총점이 높은 측이 승리. 동점 시 반론과 교차조사 영역의 점수를 우선 비교하여 판정)"""


# ── 라운드 유형별 지시사항 ──

_ROUND_INSTRUCTIONS: dict[str, str] = {
    "constructive": """## 현재 라운드: {round_id} (입론)

입론(Constructive) 라운드입니다. 다음을 수행하세요:
- 논제에 대한 **정확히 3개의 핵심 논점(contention)**을 제시
- 각 논점에 근거와 사례를 뒷받침
- 명확한 논증 구조(주장 → 이유 → 증거)를 사용

**출력 구조:**
## 논점 1: [제목]
(주장, 이유, 증거)

## 논점 2: [제목]
(주장, 이유, 증거)

## 논점 3: [제목]
(주장, 이유, 증거)""",

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


def get_round_instructions(round_config: RoundConfig, max_speech_chars: int = 0) -> str:
    """라운드 설정에 맞는 지시사항을 반환한다."""
    speech_type = round_config["speech_type"]
    round_id = round_config["round_id"]

    template = _ROUND_INSTRUCTIONS.get(speech_type)
    if template is None:
        raise ValueError(
            f"알 수 없는 speech_type: '{speech_type}'. "
            f"허용 값: {list(_ROUND_INSTRUCTIONS.keys())}"
        )

    final_note = ""
    if round_id in FINAL_REBUTTAL_ROUND_IDS:
        final_note = (
            "**이것은 최종 반박입니다.** "
            "이 라운드가 자신의 마지막 발언 기회입니다. "
            "왜 자신의 측이 이 토론에서 승리해야 하는지 결정적으로 정리하세요."
        )

    result = template.format(round_id=round_id, final_note=final_note)

    if max_speech_chars > 0:
        result += (
            f"\n\n## 분량 제한\n"
            f"공개 발언은 **{max_speech_chars}자 이내**로 작성하세요. "
            f"비공개 메모([PRIVATE_NOTES])는 분량 제한에 포함되지 않습니다. "
            f"핵심 논점에 집중하여 간결하게 작성하세요."
        )

    return result


def format_transcript_for_llm(
    transcript: list[SpeechRecord],
    context_window: int = 0,
    summary_chars: int = DEFAULT_SUMMARY_CHARS,
) -> str:
    """토론 기록을 LLM이 읽을 수 있는 텍스트로 변환한다.

    Args:
        transcript: 발언 기록 리스트
        context_window: 최근 N개 라운드만 전문 유지 (0이면 전체 전문)
        summary_chars: 윈도우 밖 발언의 요약 길이 (글자 수)
    """
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

    def _format_speech(speech: SpeechRecord, truncate: bool = False) -> str:
        speaker = speaker_labels.get(speech["speaker"], speech["speaker"])
        stype = type_labels.get(speech["speech_type"], speech["speech_type"])
        content = speech["content"]
        if truncate and len(content) > summary_chars:
            content = content[:summary_chars].rstrip() + " [... 이하 생략]"
        return f"### [{speech['round_id']}] {speaker} — {stype}\n\n{content}"

    # context_window == 0: 전체 전문 (기존 동작)
    if context_window <= 0 or len(transcript) <= context_window:
        return "\n\n---\n\n".join(_format_speech(s) for s in transcript)

    # 윈도우 분할
    split = len(transcript) - context_window
    old_parts = [_format_speech(s, truncate=True) for s in transcript[:split]]
    recent_parts = [_format_speech(s) for s in transcript[split:]]

    return (
        "\n\n---\n\n".join(old_parts)
        + "\n\n--- 이상 요약 / 이하 최근 발언 전문 ---\n\n"
        + "\n\n---\n\n".join(recent_parts)
    )

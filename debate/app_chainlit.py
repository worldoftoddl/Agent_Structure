"""Chainlit 기반 CEDA 토론 UI.

실행:
    cd /home/shin/Project
    PYTHONPATH=. chainlit run Agent_Structure/debate/app_chainlit.py
"""

from __future__ import annotations

import uuid

import chainlit as cl

from Agent_Structure.debate import create_debate

SPEAKER_LABELS = {"affirmative": "긍정측", "negative": "부정측", "judge": "심판"}
TYPE_LABELS = {
    "constructive": "입론",
    "cx_question": "교차조사 질문",
    "cx_answer": "교차조사 답변",
    "rebuttal": "반박",
    "verdict": "판정",
}


@cl.on_chat_start
async def start() -> None:
    """채팅 시작 시 세션 ID 생성 및 논제 입력 안내."""
    cl.user_session.set("thread_id", f"chainlit-{uuid.uuid4()}")
    await cl.Message(content="토론할 논제를 입력하세요.").send()


@cl.on_message
async def main(message: cl.Message) -> None:
    """논제를 받아 토론을 실행하고 라운드별로 스트리밍."""
    proposition = message.content
    await cl.Message(content=f"**논제:** {proposition}\n\n토론을 시작합니다...").send()

    thread_id = cl.user_session.get("thread_id")
    graph, initial_state = create_debate(proposition)

    aff_notes = ""
    neg_notes = ""

    async for event in graph.astream(
        initial_state,
        config={"configurable": {"thread_id": thread_id}},
        stream_mode="updates",
    ):
        for _node_name, updates in event.items():
            if "aff_private_notes" in updates:
                aff_notes = updates["aff_private_notes"]
            if "neg_private_notes" in updates:
                neg_notes = updates["neg_private_notes"]

            for speech in updates.get("transcript", []):
                speaker = speech["speaker"]
                round_id = speech["round_id"]
                label = SPEAKER_LABELS.get(speaker, speaker)
                stype = TYPE_LABELS.get(speech["speech_type"], speech["speech_type"])

                my_notes = aff_notes if speaker == "affirmative" else neg_notes

                # 비공개 메모를 Text element로 첨부 (클릭 시 사이드 패널에 표시)
                elements = []
                if my_notes:
                    elements.append(
                        cl.Text(
                            name=f"📋 {label} 비공개 메모 [{round_id}]",
                            content=my_notes,
                            display="side",
                        )
                    )

                msg = cl.Message(
                    content=f"**[{round_id}] {stype}**\n\n{speech['content']}",
                    author=label,
                    elements=elements,
                )
                await msg.send()

    await cl.Message(content="토론이 종료되었습니다.").send()

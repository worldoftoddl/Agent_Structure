# skills/ — 스킬 파일 (프롬프트·가이드라인)

## 역할

DeepAgents의 skills 기능용 마크다운/텍스트 파일을 보관한다. `build_agent(skills_dirs=["skills/"])`로 전달하면 에이전트가 스킬 파일을 참조할 수 있다.

## 파일 구조

- `writing_rules.md` — 한국어 미디어 글쓰기 첨삭 규칙 (23개 원칙)
- `README.md` — 스킬 폴더 설명

## writing_rules.md 요약

윌리엄 진서(William Zinsser)와 로이 피터 클락(Roy Peter Clark)의 원칙 기반:
- 클러터 제거, 능동태 사용, 구체적 표현
- Smart Brevity 4단계 블록 구조
- 퇴고 6원칙, 접속어 절제
- 독자 중심 글쓰기, 내러티브와 감정선

## 새 스킬 추가 방법

1. `skills/` 디렉토리에 마크다운 파일 추가 (예: `skills/tax_analysis.md`)
2. `build_agent(skills_dirs=["skills/"])`로 디렉토리 전체를 전달하거나, 특정 파일만 지정

## 수정 시 주의사항

- 스킬 파일은 에이전트의 시스템 프롬프트에 주입될 수 있으므로, 토큰 사용량에 주의.
- 파일명이 에이전트에게 스킬 이름으로 노출될 수 있다.

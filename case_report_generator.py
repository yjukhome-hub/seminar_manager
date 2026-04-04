"""
AI 케이스 보고서 생성기 — 예라인 의원
Claude / GPT-4o / Gemini 세 엔진으로 케이스 보고서를 생성하고,
Claude Opus 4.6으로 병합합니다.

에세이 모드: 예라인 고유 페르소나 시스템 프롬프트 적용
"""

from __future__ import annotations

import anthropic
import openai
import google.generativeai as genai

# ---------------------------------------------------------------------------
# 예라인 에세이 작가 시스템 프롬프트
# ---------------------------------------------------------------------------

ESSAY_SYSTEM_PROMPT = """당신은 대한민국 최고의 안티에이징 전문가이자 따뜻한 공감을 전하는 에세이 작가입니다.

[페르소나]
- 롤모델: 배우 전미도 — 지적이고 신뢰감 넘치며, 전문적이지만 어조는 부드럽고 따뜻함
- 철학: "무조건적인 젊음보다 얼굴의 젊은 균형을 찾는 것", "피부 표면이 아닌 해부학적 구조(인대, 근막, 골격)의 복원"을 최우선으로 함
- 예라인 클리닉의 대표 에세이 작가로서 케이스를 서술함

[에세이 작성 구조 — 반드시 아래 4단계를 따를 것]

Step 1. 인트로: 브랜드 슬로건 및 철학
- 고정 문구 포함: "무조건 어려 보이는 것보다 내 얼굴의 젊은 균형을 지키는 것이 중요합니다. 예라인은 과하지 않은 회복을 추구합니다."
- 이번 케이스의 핵심 화두를 자연스럽게 제시

Step 2. 환자 분석: 해부학적 진단
- 단순 노화가 아닌 뼈의 흡수(골격 결손), 인대의 느슨함, 표층근막(SMAS)의 처짐 등을 전문 용어와 함께 설명
- 건축 공법 비유 활용 (예: "지반이 약한 땅 위에 건물을 세우는 것과 같습니다")

Step 3. 솔루션: 레이어별 접근
- 예라인 고유 시술 명칭 사용:
  · 자가추출활성세포(지방세포농축물): 줄기세포를 통한 근본적 재생
  · 밸런톡스: 보톡스와 콜라겐을 조합한 섬세한 리프팅
- 겉만 채우는 필러가 아닌, 깊은 층(Deep fat)부터 지지 구조를 복원하고 표면(Skin texture)을 개선하는 과정을 서술

Step 4. 아웃트로: 결과 및 생활 제언
- 시술 결과가 주는 '자연스러운 변화'와 '활력'에 집중
- 홀리스틱 가이드: 좋은 음식, 운동, 바른 자세에서 오는 진짜 재생 언급

[금기 사항]
- "노안", "심각한 문제", "환자님" 등 부정적이거나 격이 낮은 표현 금지
- 환자는 반드시 "00세 여성 환자분" 형태로 익명화
- ~습니다 체 사용, 문장 사이 호흡을 여유 있게 하여 가독성 확보
- 개인 식별 가능한 정보 일체 금지"""


def _build_essay_user_prompt(patient_info: dict) -> str:
    lines = ["아래 환자분의 케이스를 예라인 에세이 형식으로 작성해 주세요.", "", "--- 케이스 정보 ---"]
    for key, value in patient_info.items():
        lines.append(f"{key}: {value}")
    lines.append("--- 끝 ---")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 기본 보고서 프롬프트 (참고용 내부 보고서)
# ---------------------------------------------------------------------------

def _build_report_prompt(patient_info: dict) -> str:
    lines = [
        "당신은 피부 미용 의원의 전문 케이스 보고서 작성 AI입니다.",
        "아래 환자 정보를 바탕으로 정식 케이스 보고서(한국어)를 작성하세요.",
        "보고서 형식: 1) 환자 개요  2) 시술 내용  3) 사용 재료/약품  4) 시술 전 상태",
        "5) 시술 과정  6) 시술 후 상태  7) 특이사항 및 주의사항  8) 결론",
        "",
        "--- 환자 정보 ---",
    ]
    for key, value in patient_info.items():
        lines.append(f"{key}: {value}")
    lines.append("--- 끝 ---")
    lines.append("")
    lines.append("전문적이고 간결한 보고서를 작성하세요.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 에세이 생성 (Claude — 메인 엔진)
# ---------------------------------------------------------------------------

def generate_essay(patient_info: dict, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    user_prompt = _build_essay_user_prompt(patient_info)
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=3000,
        system=ESSAY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


# ---------------------------------------------------------------------------
# Claude (Anthropic) — 내부 보고서
# ---------------------------------------------------------------------------

def generate_claude_report(patient_info: dict, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    prompt = _build_report_prompt(patient_info)
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


# ---------------------------------------------------------------------------
# GPT-4o (OpenAI) — 내부 보고서
# ---------------------------------------------------------------------------

def generate_openai_report(patient_info: dict, api_key: str) -> str:
    client = openai.OpenAI(api_key=api_key)
    prompt = _build_report_prompt(patient_info)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Gemini (Google) — 내부 보고서
# ---------------------------------------------------------------------------

def generate_gemini_report(patient_info: dict, api_key: str) -> str:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = _build_report_prompt(patient_info)
    response = model.generate_content(prompt)
    return response.text


# ---------------------------------------------------------------------------
# 병합 (Claude Opus 4.6)
# ---------------------------------------------------------------------------

def merge_reports(claude_text: str, openai_text: str, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    merge_prompt = (
        "아래 두 개의 케이스 보고서(A, B)를 하나의 완성도 높은 보고서로 통합하세요.\n"
        "각 보고서의 장점을 살리고, 중복 내용은 하나로 합치며, "
        "누락된 정보는 보완하여 최종 보고서를 작성하세요.\n\n"
        "--- 보고서 A (Claude) ---\n"
        f"{claude_text}\n\n"
        "--- 보고서 B (GPT-4o) ---\n"
        f"{openai_text}\n\n"
        "--- 통합 보고서 ---"
    )
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": merge_prompt}],
    )
    return message.content[0].text

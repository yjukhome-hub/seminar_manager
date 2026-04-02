"""
AI 케이스 보고서 생성기 — 예라인 의원
Claude / GPT-4o / Gemini 세 엔진으로 케이스 보고서를 생성하고,
Claude Opus 4.6으로 병합합니다.
"""

from __future__ import annotations

import anthropic
import openai
import google.generativeai as genai

# ---------------------------------------------------------------------------
# 공통 프롬프트 헬퍼
# ---------------------------------------------------------------------------

def _build_prompt(patient_info: dict) -> str:
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
# Claude (Anthropic)
# ---------------------------------------------------------------------------

def generate_claude_report(patient_info: dict, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    prompt = _build_prompt(patient_info)
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


# ---------------------------------------------------------------------------
# GPT-4o (OpenAI)
# ---------------------------------------------------------------------------

def generate_openai_report(patient_info: dict, api_key: str) -> str:
    client = openai.OpenAI(api_key=api_key)
    prompt = _build_prompt(patient_info)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Gemini (Google)
# ---------------------------------------------------------------------------

def generate_gemini_report(patient_info: dict, api_key: str) -> str:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = _build_prompt(patient_info)
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

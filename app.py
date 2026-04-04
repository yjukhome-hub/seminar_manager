"""
예라인 의원 AI 케이스 보고서 생성기
Streamlit 웹앱
"""

from __future__ import annotations

import json
import os

import streamlit as st

from case_storage import CATEGORIES, add_case, delete_case, load_cases, update_case
from case_report_generator import (
    generate_claude_report,
    generate_essay,
    generate_gemini_report,
    generate_openai_report,
    merge_reports,
)

# ---------------------------------------------------------------------------
# 페이지 설정
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="예라인 의원 AI 케이스 보고서",
    page_icon="🏥",
    layout="wide",
)

# ---------------------------------------------------------------------------
# API 키 저장/불러오기
# ---------------------------------------------------------------------------

API_KEYS_FILE = "api_keys.json"


def load_api_keys() -> dict:
    if os.path.exists(API_KEYS_FILE):
        with open(API_KEYS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"anthropic": "", "openai": "", "google": ""}


def save_api_keys(keys: dict) -> None:
    with open(API_KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(keys, f, ensure_ascii=False, indent=2)


if "api_keys" not in st.session_state:
    st.session_state["api_keys"] = load_api_keys()

# ---------------------------------------------------------------------------
# 사이드바 메뉴
# ---------------------------------------------------------------------------

st.sidebar.title("🏥 예라인 의원")
st.sidebar.caption("AI 케이스 보고서 생성기")
menu = st.sidebar.radio(
    "메뉴",
    ["🆕 새 케이스 생성", "📚 케이스 아카이브", "⚙️ 설정"],
    label_visibility="collapsed",
)

# ---------------------------------------------------------------------------
# ⚙️ 설정
# ---------------------------------------------------------------------------

if menu == "⚙️ 설정":
    st.title("⚙️ API 키 설정")
    st.info("API 키는 서버에 `api_keys.json`으로 저장됩니다. 한 번 저장하면 재입력이 필요 없습니다.")

    keys = st.session_state["api_keys"]

    anthropic_key = st.text_input(
        "Anthropic API Key (Claude)",
        value=keys.get("anthropic", ""),
        type="password",
        placeholder="sk-ant-...",
    )
    openai_key = st.text_input(
        "OpenAI API Key (GPT-4o)",
        value=keys.get("openai", ""),
        type="password",
        placeholder="sk-...",
    )
    google_key = st.text_input(
        "Google API Key (Gemini)",
        value=keys.get("google", ""),
        type="password",
        placeholder="AIza...",
    )

    if st.button("💾 저장", use_container_width=True, type="primary"):
        new_keys = {"anthropic": anthropic_key, "openai": openai_key, "google": google_key}
        save_api_keys(new_keys)
        st.session_state["api_keys"] = new_keys
        st.success("API 키가 저장되었습니다.")

# ---------------------------------------------------------------------------
# 🆕 새 케이스 생성
# ---------------------------------------------------------------------------

elif menu == "🆕 새 케이스 생성":
    st.title("🆕 새 케이스 보고서 생성")

    keys = st.session_state["api_keys"]

    # 환자 정보 입력
    with st.form("case_form"):
        st.subheader("환자 정보")

        c1, c2, c3 = st.columns(3)
        age = c1.number_input("나이", min_value=1, max_value=120, value=40, step=1)
        gender = c2.selectbox("성별", ["여성", "남성", "기타"])
        category = c3.selectbox("시술 카테고리", CATEGORIES)

        treatment_detail = st.text_area(
            "시술 내용",
            placeholder="예: 얼굴 전체 줄기세포 시술 (성장인자 포함)",
            height=100,
        )
        materials = st.text_area(
            "사용 재료 / 약품",
            placeholder="예: 줄기세포 배양액 5mL, 히알루론산 필러 1cc",
            height=80,
        )
        pre_condition = st.text_area(
            "시술 전 상태",
            placeholder="예: 얼굴 전반적 건조, 잔주름 다수, 탄력 저하",
            height=80,
        )
        procedure_notes = st.text_area(
            "시술 과정 특이사항",
            placeholder="예: 마취 크림 도포 30분 후 시술, 통증 호소 없음",
            height=80,
        )
        special_notes = st.text_area(
            "기타 특이사항 / 주의사항",
            placeholder="예: 임신 가능성 없음 확인, 항생제 알레르기 없음",
            height=80,
        )

        st.subheader("생성할 보고서 선택")
        use_essay = st.checkbox(
            "✍️ 예라인 케이스 에세이 (Claude — 메인)",
            value=bool(keys.get("anthropic")),
            help="예라인 페르소나 시스템 프롬프트로 SNS/블로그용 에세이를 생성합니다.",
        )
        st.caption("─ 내부 참고용 보고서 (선택) ─")
        col_a, col_b, col_c = st.columns(3)
        use_claude = col_a.checkbox("Claude 보고서", value=False)
        use_openai = col_b.checkbox("GPT-4o 보고서", value=bool(keys.get("openai")))
        use_gemini = col_c.checkbox("Gemini 보고서", value=bool(keys.get("google")))

        submitted = st.form_submit_button("🚀 보고서 생성", use_container_width=True, type="primary")

    if submitted:
        patient_info = {
            "나이": f"{age}세",
            "성별": gender,
            "시술 카테고리": category,
            "시술 내용": treatment_detail,
            "사용 재료/약품": materials,
            "시술 전 상태": pre_condition,
            "시술 과정 특이사항": procedure_notes,
            "기타 특이사항": special_notes,
        }

        if not any([use_essay, use_claude, use_openai, use_gemini]):
            st.warning("최소 하나의 생성 옵션을 선택하세요.")
            st.stop()

        essay_result = ""
        claude_result = ""
        openai_result = ""
        gemini_result = ""
        errors = []

        progress = st.progress(0, text="보고서 생성 중...")
        step = 0
        total = sum([use_essay, use_claude, use_openai, use_gemini])

        if use_essay:
            if not keys.get("anthropic"):
                errors.append("Anthropic API 키가 없습니다. ⚙️ 설정에서 입력하세요.")
            else:
                with st.spinner("✍️ 예라인 에세이 작성 중..."):
                    try:
                        essay_result = generate_essay(patient_info, keys["anthropic"])
                    except Exception as e:
                        errors.append(f"에세이 생성 오류: {e}")
            step += 1
            progress.progress(step / total, text=f"진행 중 ({step}/{total})")

        if use_claude:
            if not keys.get("anthropic"):
                errors.append("Anthropic API 키가 없습니다. ⚙️ 설정에서 입력하세요.")
            else:
                with st.spinner("Claude 보고서 생성 중..."):
                    try:
                        claude_result = generate_claude_report(patient_info, keys["anthropic"])
                    except Exception as e:
                        errors.append(f"Claude 오류: {e}")
            step += 1
            progress.progress(step / total, text=f"진행 중 ({step}/{total})")

        if use_openai:
            if not keys.get("openai"):
                errors.append("OpenAI API 키가 없습니다. ⚙️ 설정에서 입력하세요.")
            else:
                with st.spinner("GPT-4o 보고서 생성 중..."):
                    try:
                        openai_result = generate_openai_report(patient_info, keys["openai"])
                    except Exception as e:
                        errors.append(f"GPT-4o 오류: {e}")
            step += 1
            progress.progress(step / total, text=f"진행 중 ({step}/{total})")

        if use_gemini:
            if not keys.get("google"):
                errors.append("Google API 키가 없습니다. ⚙️ 설정에서 입력하세요.")
            else:
                with st.spinner("Gemini 보고서 생성 중..."):
                    try:
                        gemini_result = generate_gemini_report(patient_info, keys["google"])
                    except Exception as e:
                        errors.append(f"Gemini 오류: {e}")
            step += 1
            progress.progress(step / total, text=f"완료!")

        for err in errors:
            st.error(err)

        # 병합
        merged_result = ""
        if claude_result and openai_result and keys.get("anthropic"):
            with st.spinner("Claude + GPT-4o 병합 중..."):
                try:
                    merged_result = merge_reports(claude_result, openai_result, keys["anthropic"])
                except Exception as e:
                    st.warning(f"병합 오류: {e}")

        # 결과 탭
        tab_labels = []
        tab_contents = []
        if essay_result:
            tab_labels.append("✍️ 예라인 에세이")
            tab_contents.append(essay_result)
        if use_claude:
            tab_labels.append("Claude 보고서")
            tab_contents.append(claude_result)
        if use_openai:
            tab_labels.append("GPT-4o 보고서")
            tab_contents.append(openai_result)
        if use_gemini:
            tab_labels.append("Gemini 보고서")
            tab_contents.append(gemini_result)
        if merged_result:
            tab_labels.append("🔀 병합 버전")
            tab_contents.append(merged_result)

        if tab_labels:
            tabs = st.tabs(tab_labels)
            for tab, content in zip(tabs, tab_contents):
                with tab:
                    st.markdown(content if content else "_생성 실패_")

        # 최종 편집 및 저장
        st.divider()
        st.subheader("최종 보고서 편집 및 저장")

        default_final = essay_result or merged_result or claude_result or openai_result or gemini_result
        final_text = st.text_area("최종 버전 편집", value=default_final, height=400)

        if st.button("💾 최종 버전 저장", use_container_width=True, type="primary"):
            if not final_text.strip():
                st.warning("저장할 내용이 없습니다.")
            else:
                case_data = {
                    "category": category,
                    "patient_info": patient_info,
                    "reports": {
                        "essay": essay_result,
                        "claude": claude_result,
                        "openai": openai_result,
                        "gemini": gemini_result,
                        "merged": merged_result,
                    },
                    "final_report": final_text,
                    "status": "완성",
                }
                saved = add_case(case_data)
                st.success(f"케이스가 저장되었습니다. (ID: {saved['id']})")

# ---------------------------------------------------------------------------
# 📚 케이스 아카이브
# ---------------------------------------------------------------------------

elif menu == "📚 케이스 아카이브":
    st.title("📚 케이스 아카이브")

    cases = load_cases()

    if not cases:
        st.info("저장된 케이스가 없습니다.")
        st.stop()

    # 필터
    col_f1, col_f2, col_f3 = st.columns(3)
    filter_cat = col_f1.selectbox("카테고리 필터", ["전체"] + CATEGORIES)
    filter_status = col_f2.selectbox("상태 필터", ["전체", "완성", "초안"])
    search_text = col_f3.text_input("검색어", placeholder="내용 검색...")

    filtered = cases
    if filter_cat != "전체":
        filtered = [c for c in filtered if c.get("category") == filter_cat]
    if filter_status != "전체":
        filtered = [c for c in filtered if c.get("status") == filter_status]
    if search_text:
        filtered = [
            c for c in filtered
            if search_text.lower() in json.dumps(c, ensure_ascii=False).lower()
        ]

    st.caption(f"총 {len(filtered)}건")

    # 내보내기 / 가져오기
    exp_col, imp_col = st.columns(2)
    with exp_col:
        export_data = json.dumps(filtered, ensure_ascii=False, indent=2)
        st.download_button(
            "📤 JSON 내보내기",
            data=export_data,
            file_name="cases_export.json",
            mime="application/json",
            use_container_width=True,
        )
    with imp_col:
        uploaded = st.file_uploader("📥 JSON 가져오기", type="json", label_visibility="collapsed")
        if uploaded:
            try:
                imported = json.load(uploaded)
                existing_ids = {c["id"] for c in load_cases()}
                new_count = 0
                all_cases = load_cases()
                for case in imported:
                    if case.get("id") not in existing_ids:
                        all_cases.append(case)
                        new_count += 1
                from case_storage import save_cases
                save_cases(all_cases)
                st.success(f"{new_count}건 가져왔습니다. 페이지를 새로고침하세요.")
            except Exception as e:
                st.error(f"가져오기 실패: {e}")

    st.divider()

    # 케이스 목록
    if "editing_case_id" not in st.session_state:
        st.session_state["editing_case_id"] = None

    for case in reversed(filtered):
        case_id = case["id"]
        created = case.get("created_at", "")[:16].replace("T", " ")
        cat = case.get("category", "기타")
        status = case.get("status", "완성")
        info = case.get("patient_info", {})
        label = f"**{created}** | {cat} | {status} | {info.get('나이', '')} {info.get('성별', '')}"

        with st.expander(label):
            if st.session_state["editing_case_id"] == case_id:
                # 편집 모드
                new_final = st.text_area(
                    "최종 보고서 편집",
                    value=case.get("final_report", ""),
                    height=300,
                    key=f"edit_text_{case_id}",
                )
                new_status = st.selectbox(
                    "상태",
                    ["완성", "초안"],
                    index=0 if status == "완성" else 1,
                    key=f"edit_status_{case_id}",
                )
                save_c, cancel_c = st.columns(2)
                if save_c.button("💾 저장", key=f"save_{case_id}", use_container_width=True, type="primary"):
                    updated = dict(case)
                    updated["final_report"] = new_final
                    updated["status"] = new_status
                    update_case(case_id, updated)
                    st.session_state["editing_case_id"] = None
                    st.success("저장되었습니다.")
                    st.rerun()
                if cancel_c.button("✖ 취소", key=f"cancel_{case_id}", use_container_width=True):
                    st.session_state["editing_case_id"] = None
                    st.rerun()
            else:
                # 보기 모드
                st.markdown("**최종 보고서**")
                st.markdown(case.get("final_report", "_내용 없음_"))

                # 개별 AI 결과
                reports = case.get("reports", {})
                if any(reports.values()):
                    all_report_tabs = [
                        ("✍️ 예라인 에세이", reports.get("essay")),
                        ("Claude 보고서", reports.get("claude")),
                        ("GPT-4o 보고서", reports.get("openai")),
                        ("Gemini 보고서", reports.get("gemini")),
                        ("🔀 병합", reports.get("merged")),
                    ]
                    visible = [(label, content) for label, content in all_report_tabs if content]
                    if visible:
                        sub_tabs = st.tabs([label for label, _ in visible])
                        for i, (_, content) in enumerate(visible):
                            with sub_tabs[i]:
                                st.markdown(content)

                btn_c1, btn_c2 = st.columns(2)
                if btn_c1.button("✏️ 편집", key=f"edit_{case_id}", use_container_width=True):
                    st.session_state["editing_case_id"] = case_id
                    st.rerun()
                if btn_c2.button("🗑️ 삭제", key=f"del_{case_id}", use_container_width=True):
                    delete_case(case_id)
                    st.success("삭제되었습니다.")
                    st.rerun()

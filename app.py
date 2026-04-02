import streamlit as st
import pandas as pd
from datetime import datetime
import os
from case_report_generator import (
    PROVIDER_LABELS, STREAM_FUNCS, build_user_prompt, generate_all_parallel,
)

# 페이지 설정
st.set_page_config(page_title="대한 첨단재생의료 연구회", layout="wide")

# 데이터 저장 파일
DB_FILE = "seminar_combined_data.csv"
SCANS_DIR = "scans"
os.makedirs(SCANS_DIR, exist_ok=True)

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["날짜", "주제", "장소", "참석인원", "안건", "결정사항", "유형", "항목", "금액", "비고", "스캔파일", "첨부서류"])

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

if 'df' not in st.session_state:
    st.session_state['df'] = load_data()

if 'finance_rows' not in st.session_state:
    st.session_state['finance_rows'] = [{"유형": "지출", "항목": "", "금액": 0, "비고": "", "스캔파일": None}]

st.title("🏛️ 대한 첨단재생의료 연구회 세미나 회의록 및 재무관리")

menu = st.sidebar.radio("메뉴", ["📝 회의록 및 내역 작성", "📜 회의록 아카이브", "💰 재무 엑셀 리포트", "🏥 AI 케이스 보고서 생성기"])

# 1. 작성 섹션 (문서 형태)
if menu == "📝 회의록 및 내역 작성":
    st.subheader("✍️ 정기 세미나 회의록 작성")

    with st.expander("1. 회의 기본 정보", expanded=True):
        c1, c2 = st.columns(2)
        date = c1.date_input("회의 날짜", datetime.now())
        location = c2.text_input("장소", "연구회 세미나실")
        title = st.text_area("세미나 주제", placeholder="예: 제 5차 피부미용 학술 세미나\n(Shift+Enter로 줄바꿈)", height=100)
        attendees = st.text_area("참석자 명단", placeholder="원장님 외 0명")
        doc_files = st.file_uploader(
            "참석 사인 / 의결 동의안 스캔본 첨부 (JPG, PNG, PDF · 여러 파일 가능)",
            type=["jpg", "jpeg", "png", "pdf"],
            accept_multiple_files=True,
            key="doc_files"
        )

    with st.expander("2. 회의 및 결정 사항", expanded=True):
        agenda = st.text_area("회의 안건 (Agenda)")
        decisions = st.text_area("결정 사항 (Decisions)")

    with st.expander("3. 수입 및 지출 내역", expanded=True):
        updated_rows = []
        for i, row in enumerate(st.session_state['finance_rows']):
            st.markdown(f"**항목 {i+1}**")
            c3, c4, c5 = st.columns([1, 1, 2])
            etype    = c3.selectbox("구분", ["수입", "지출"],
                                    index=["수입", "지출"].index(row["유형"]) if row["유형"] in ["수입", "지출"] else 1,
                                    key=f"etype_{i}")
            cat      = c4.text_input("항목명", value=row["항목"], placeholder="회비 / 강사비 / 식대 등", key=f"cat_{i}")
            amt      = c5.number_input("금액(원)", min_value=0, step=1000, value=row["금액"], key=f"amt_{i}")
            note_val = st.text_input("비고 (입금자명 등)", value=row["비고"], key=f"note_{i}")
            scan_f   = st.file_uploader("스캔 이미지 첨부 (JPG, PNG, PDF)", type=["jpg", "jpeg", "png", "pdf"], key=f"scan_{i}")
            updated_rows.append({"유형": etype, "항목": cat, "금액": amt, "비고": note_val, "스캔파일": scan_f})
            if i < len(st.session_state['finance_rows']) - 1:
                st.divider()

        st.session_state['finance_rows'] = updated_rows

        bc1, bc2 = st.columns(2)
        if bc1.button("➕ 항목 추가", use_container_width=True):
            st.session_state['finance_rows'].append({"유형": "지출", "항목": "", "금액": 0, "비고": "", "스캔파일": None})
            st.rerun()
        if bc2.button("➖ 마지막 항목 삭제", use_container_width=True, disabled=len(st.session_state['finance_rows']) <= 1):
            st.session_state['finance_rows'].pop()
            st.rerun()

    if st.button("💾 회의록 및 내역 저장하기", use_container_width=True):
        # 첨부 서류 저장 (여러 파일)
        doc_filenames = []
        for df_file in (doc_files or []):
            fname = f"{date.strftime('%Y%m%d')}_doc_{df_file.name}"
            with open(os.path.join(SCANS_DIR, fname), "wb") as f:
                f.write(df_file.read())
            doc_filenames.append(fname)
        doc_filenames_str = "|".join(doc_filenames)

        new_rows = []
        for row in st.session_state['finance_rows']:
            scan_filename = ""
            if row["스캔파일"] is not None:
                scan_filename = f"{date.strftime('%Y%m%d')}_{row['스캔파일'].name}"
                with open(os.path.join(SCANS_DIR, scan_filename), "wb") as f:
                    f.write(row["스캔파일"].read())
            new_rows.append({
                "날짜": date.strftime("%Y-%m-%d"), "주제": title, "장소": location,
                "참석인원": attendees, "안건": agenda, "결정사항": decisions,
                "유형": row["유형"], "항목": row["항목"], "금액": row["금액"],
                "비고": row["비고"], "스캔파일": scan_filename,
                "첨부서류": doc_filenames_str
            })
        st.session_state['df'] = pd.concat([st.session_state['df'], pd.DataFrame(new_rows)], ignore_index=True)
        save_data(st.session_state['df'])
        st.session_state['finance_rows'] = [{"유형": "지출", "항목": "", "금액": 0, "비고": "", "스캔파일": None}]
        st.success("회의록과 내역이 성공적으로 기록되었습니다!")
        st.rerun()

# 2. 회의록 아카이브 (문서 형태 조회)
elif menu == "📜 회의록 아카이브":
    st.subheader("📚 역대 회의록 기록")
    df = st.session_state['df']

    if "editing_idx" not in st.session_state:
        st.session_state["editing_idx"] = None

    if not df.empty:
        unique_seminars = df.drop_duplicates(subset=["날짜", "주제"]).reset_index()

        for pos, row in unique_seminars.iterrows():
            orig_idx = row["index"]
            with st.container():
                st.markdown(f"### {row['날짜']} | {row['주제']}")

                # 수정 모드
                if st.session_state["editing_idx"] == orig_idx:
                    with st.form(key=f"edit_form_{orig_idx}"):
                        ec1, ec2 = st.columns(2)
                        new_date      = ec1.text_input("날짜", value=row["날짜"])
                        new_location  = ec2.text_input("장소", value=str(row["장소"]))
                        new_title     = st.text_input("주제", value=str(row["주제"]))
                        new_attendees = st.text_area("참석자 명단", value=str(row["참석인원"]))
                        new_doc_files = st.file_uploader(
                            "첨부 서류 교체 (사인 / 의결 동의안 · 여러 파일 가능, 비워두면 기존 유지)",
                            type=["jpg", "jpeg", "png", "pdf"],
                            accept_multiple_files=True,
                        )
                        new_agenda    = st.text_area("안건", value=str(row["안건"]))
                        new_decisions = st.text_area("결정사항", value=str(row["결정사항"]))

                        fc1, fc2 = st.columns(2)
                        save_btn   = fc1.form_submit_button("💾 저장", use_container_width=True, type="primary")
                        cancel_btn = fc2.form_submit_button("✖ 취소", use_container_width=True)

                    if save_btn:
                        st.session_state['df'].loc[orig_idx, "날짜"]     = new_date
                        st.session_state['df'].loc[orig_idx, "장소"]     = new_location
                        st.session_state['df'].loc[orig_idx, "주제"]     = new_title
                        st.session_state['df'].loc[orig_idx, "참석인원"] = new_attendees
                        st.session_state['df'].loc[orig_idx, "안건"]     = new_agenda
                        st.session_state['df'].loc[orig_idx, "결정사항"] = new_decisions
                        if new_doc_files:
                            saved = []
                            for f in new_doc_files:
                                fname = f"{new_date.replace('-', '')}_doc_{f.name}"
                                with open(os.path.join(SCANS_DIR, fname), "wb") as fp:
                                    fp.write(f.read())
                                saved.append(fname)
                            st.session_state['df'].loc[orig_idx, "첨부서류"] = "|".join(saved)
                        save_data(st.session_state['df'])
                        st.session_state["editing_idx"] = None
                        st.success("수정되었습니다.")
                        st.rerun()
                    if cancel_btn:
                        st.session_state["editing_idx"] = None
                        st.rerun()

                # 조회 모드
                else:
                    st.info(f"📍 **장소:** {row['장소']}  |  👥 **참석자:** {row['참석인원']}")
                    st.write(f"**📝 안건:** {row['안건']}")
                    st.write(f"**✅ 결정사항:** {row['결정사항']}")

                    # 첨부 서류 (사인, 의결 동의안 등)
                    doc_val = row.get("첨부서류", "")
                    if pd.notna(doc_val) and doc_val:
                        st.markdown("**📎 첨부 서류 (사인 / 의결 동의안)**")
                        doc_cols = st.columns(3)
                        for di, fname in enumerate(str(doc_val).split("|")):
                            if not fname:
                                continue
                            fpath = os.path.join(SCANS_DIR, fname)
                            if os.path.exists(fpath) and fname.lower().endswith((".jpg", ".jpeg", ".png")):
                                doc_cols[di % 3].image(fpath, caption=fname, use_container_width=True)
                            elif os.path.exists(fpath):
                                doc_cols[di % 3].caption(f"📄 {fname}")

                    # 수입/지출 스캔파일
                    if pd.notna(row.get("스캔파일")) and row.get("스캔파일"):
                        fpath = os.path.join(SCANS_DIR, row["스캔파일"])
                        if os.path.exists(fpath) and row["스캔파일"].lower().endswith((".jpg", ".jpeg", ".png")):
                            st.image(fpath, caption=row["스캔파일"], width=300)
                        elif os.path.exists(fpath):
                            st.caption(f"📎 영수증: {row['스캔파일']}")

                    if st.button("✏️ 수정", key=f"edit_btn_{orig_idx}"):
                        st.session_state["editing_idx"] = orig_idx
                        st.rerun()

                st.divider()
    else:
        st.info("기록된 회의록이 없습니다.")

# 3. 재무 엑셀 리포트 (엑셀 형식)
elif menu == "💰 재무 엑셀 리포트":
    st.subheader("📊 수입 및 지출 재무 제표 (Excel)")
    df = st.session_state['df']

    # 이월금 입력
    with st.expander("🏦 기초 이월금 설정", expanded=True):
        c_carry, c_note = st.columns([1, 2])
        carryover = c_carry.number_input("전기 이월금 (원)", min_value=0, step=1000, value=0)
        c_note.caption("이전 회계 기간에서 넘어온 잔액을 입력하세요.")

    if not df.empty:
        # 수입 테이블
        st.write("### 🟢 수입 내역 (Incomes)")
        income_df = df[df["유형"] == "수입"][["날짜", "항목", "금액", "비고"]]
        st.table(income_df)

        # 지출 테이블
        st.write("### 🔴 지출 내역 (Expenses)")
        expense_df = df[df["유형"] == "지출"][["날짜", "항목", "금액", "비고"]]
        st.table(expense_df)

        # 통계 요약 (이월금 반영)
        total_in = income_df["금액"].sum()
        total_out = expense_df["금액"].sum()
        balance = carryover + total_in - total_out

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("전기 이월금", f"{carryover:,}원")
        c2.metric("총 수입", f"{total_in:,}원")
        c3.metric("총 지출", f"{total_out:,}원")
        c4.metric("현재 잔액", f"{balance:,}원", delta=f"{balance - carryover:,}원")

        # 엑셀 다운로드 버튼
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📤 전체 내역 엑셀로 내보내기", csv, "seminar_finance_report.csv", "text/csv")
    else:
        st.info("금융 내역이 없습니다.")

# 4. AI 케이스 보고서 생성기
elif menu == "🏥 AI 케이스 보고서 생성기":
    st.subheader("🤖 예라인 의원 AI 케이스 보고서 생성기")
    st.caption("Claude · GPT-4o · Gemini 중 원하는 AI를 선택하거나 전체 비교 결과를 한 번에 받아보세요.")

    # ── 환자 정보 입력 ──────────────────────────────
    with st.expander("1. 환자 기본 정보", expanded=True):
        c1, c2 = st.columns(2)
        patient_age = c1.text_input("나이", placeholder="예: 40대 후반")
        patient_gender = c2.selectbox("성별", ["여성", "남성"])
        chief_complaint = st.text_area(
            "주요 고민 및 증상",
            placeholder="예: 만성 주사피부염으로 피부가 얇고 매우 붉음. 반복된 레이저 시술로 장벽이 무너진 상태.",
            height=100,
        )

    with st.expander("2. 원장님의 진단", expanded=True):
        diagnosis = st.text_area(
            "해부학적/구조적 진단",
            placeholder="예: 진피층의 구조적 붕괴와 혈관 과확장. 안면부 근육 과긴장으로 인한 순환 저하.",
            height=120,
        )

    with st.expander("3. 시술 내용", expanded=True):
        treatment = st.text_area(
            "시술 부위 및 방법",
            placeholder="예: 자가세포 재생술을 통한 진피 재건 + 경추부 근육 이완을 통한 순환 개선(밸런톡스 활용).",
            height=120,
        )

    with st.expander("4. 추가 참고 사항 (선택)", expanded=False):
        additional_notes = st.text_area(
            "추가 지침 또는 강조 사항",
            placeholder="예: 전후 사진의 차이를 서술할 것. 특정 비유나 표현 스타일을 사용할 것.",
            height=100,
        )

    st.divider()

    # ── AI 선택 ──────────────────────────────────
    st.markdown("#### 🧠 AI 선택")
    ai_cols = st.columns(3)
    use_claude = ai_cols[0].checkbox("🟣 Claude (Anthropic)", value=True)
    use_openai = ai_cols[1].checkbox("🟢 GPT-4o (OpenAI)", value=False)
    use_gemini = ai_cols[2].checkbox("🔵 Gemini (Google)", value=False)

    selected_providers = []
    if use_claude:
        selected_providers.append("claude")
    if use_openai:
        selected_providers.append("openai")
    if use_gemini:
        selected_providers.append("gemini")

    # ── API 키 입력 ───────────────────────────────
    with st.expander("🔑 API 키 설정", expanded=bool(selected_providers)):
        api_keys: dict = {}
        if use_claude:
            api_keys["claude"] = st.text_input(
                "Anthropic API 키", type="password", placeholder="sk-ant-...",
                help="ANTHROPIC_API_KEY 환경 변수로 대체 가능",
                key="key_claude",
            )
        if use_openai:
            api_keys["openai"] = st.text_input(
                "OpenAI API 키", type="password", placeholder="sk-...",
                help="OPENAI_API_KEY 환경 변수로 대체 가능",
                key="key_openai",
            )
        if use_gemini:
            api_keys["gemini"] = st.text_input(
                "Google AI API 키", type="password", placeholder="AIza...",
                help="GOOGLE_API_KEY 환경 변수로 대체 가능",
                key="key_gemini",
            )

    # ── 세션 상태 초기화 ──────────────────────────
    if "cr_results" not in st.session_state:
        st.session_state["cr_results"] = {}

    col_gen, col_clear = st.columns([3, 1])
    generate_btn = col_gen.button("✨ 케이스 보고서 생성하기", use_container_width=True, type="primary")
    clear_btn = col_clear.button("🗑️ 초기화", use_container_width=True)

    if clear_btn:
        st.session_state["cr_results"] = {}
        st.rerun()

    if generate_btn:
        import os

        if not patient_age or not chief_complaint or not diagnosis or not treatment:
            st.warning("나이, 주요 고민, 진단, 시술 내용은 필수 입력 항목입니다.")
        elif not selected_providers:
            st.warning("AI를 한 개 이상 선택해 주세요.")
        else:
            # 환경 변수 폴백 처리
            resolved_keys: dict = {}
            for p in selected_providers:
                key_input = api_keys.get(p, "").strip()
                env_map = {"claude": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY", "gemini": "GOOGLE_API_KEY"}
                resolved = key_input or os.environ.get(env_map[p], "")
                resolved_keys[p] = resolved or None

            missing = [PROVIDER_LABELS[p] for p in selected_providers if not resolved_keys[p]]
            if missing:
                st.error(f"API 키가 없는 AI: {', '.join(missing)}")
            else:
                user_prompt = build_user_prompt(
                    patient_age, patient_gender, chief_complaint,
                    diagnosis, treatment, additional_notes,
                )
                st.session_state["cr_results"] = {}

                # ── 단일 AI: 실시간 스트리밍 ──────────────
                if len(selected_providers) == 1:
                    provider = selected_providers[0]
                    placeholder = st.empty()
                    status = st.status(
                        f"{PROVIDER_LABELS[provider]}가 보고서를 생성하고 있습니다...",
                        expanded=True,
                    )
                    try:
                        collected = ""
                        for chunk in STREAM_FUNCS[provider](user_prompt, resolved_keys[provider]):
                            collected += chunk
                            placeholder.markdown(collected)
                        st.session_state["cr_results"][provider] = collected
                        status.update(label="✅ 생성 완료!", state="complete", expanded=False)
                    except Exception as e:
                        status.update(label="❌ 오류 발생", state="error", expanded=False)
                        st.error(f"{PROVIDER_LABELS[provider]} 오류: {e}")

                # ── 복수 AI: 병렬 생성 후 탭 표시 ──────────
                else:
                    labels = [PROVIDER_LABELS[p] for p in selected_providers]
                    with st.spinner(f"{' · '.join(labels)} 동시 생성 중... (잠시 기다려 주세요)"):
                        results = generate_all_parallel(selected_providers, user_prompt, resolved_keys)
                    st.session_state["cr_results"] = results

                    errors = {p: v for p, v in results.items() if isinstance(v, Exception)}
                    if errors:
                        for p, err in errors.items():
                            st.error(f"{PROVIDER_LABELS[p]} 오류: {err}")

    # ── 결과 표시 ─────────────────────────────────
    results = st.session_state.get("cr_results", {})
    success_results = {p: v for p, v in results.items() if isinstance(v, str)}

    if success_results:
        st.divider()
        st.markdown("### 📋 생성된 케이스 보고서")

        if len(success_results) == 1:
            provider, text = next(iter(success_results.items()))
            st.caption(f"생성 AI: {PROVIDER_LABELS[provider]}")
            st.markdown(text)
            st.download_button(
                label="📥 보고서 다운로드 (.txt)",
                data=text.encode("utf-8"),
                file_name=f"케이스보고서_{provider}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
            )
        else:
            tab_labels = [f"{PROVIDER_LABELS[p]}" for p in success_results]
            tabs = st.tabs(tab_labels)
            for tab, (provider, text) in zip(tabs, success_results.items()):
                with tab:
                    st.markdown(text)
                    st.download_button(
                        label=f"📥 {PROVIDER_LABELS[provider]} 보고서 다운로드",
                        data=text.encode("utf-8"),
                        file_name=f"케이스보고서_{provider}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        key=f"dl_{provider}",
                    )

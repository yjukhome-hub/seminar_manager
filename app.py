import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="대한 첨단재생의료 연구회", layout="wide")

# 데이터 저장 파일
DB_FILE = "seminar_combined_data.csv"
SCANS_DIR = "scans"
os.makedirs(SCANS_DIR, exist_ok=True)

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["날짜", "주제", "장소", "참석인원", "안건", "결정사항", "유형", "항목", "금액", "비고", "스캔파일"])

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

if 'df' not in st.session_state:
    st.session_state['df'] = load_data()

if 'finance_rows' not in st.session_state:
    st.session_state['finance_rows'] = [{"유형": "지출", "항목": "", "금액": 0, "비고": "", "스캔파일": None}]

st.title("🏛️ 대한 첨단재생의료 연구회 세미나 회의록 및 재무관리")

menu = st.sidebar.radio("메뉴", ["📝 회의록 및 내역 작성", "📜 회의록 아카이브", "💰 재무 엑셀 리포트"])

# 1. 작성 섹션 (문서 형태)
if menu == "📝 회의록 및 내역 작성":
    st.subheader("✍️ 정기 세미나 회의록 작성")

    with st.expander("1. 회의 기본 정보", expanded=True):
        c1, c2 = st.columns(2)
        date = c1.date_input("회의 날짜", datetime.now())
        location = c2.text_input("장소", "연구회 세미나실")
        title = st.text_input("세미나 주제", placeholder="예: 제 5차 피부미용 학술 세미나")
        attendees = st.text_area("참석자 명단", placeholder="원장님 외 0명")

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
                "비고": row["비고"], "스캔파일": scan_filename
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
                        new_date     = ec1.text_input("날짜", value=row["날짜"])
                        new_location = ec2.text_input("장소", value=str(row["장소"]))
                        new_title    = st.text_input("주제", value=str(row["주제"]))
                        new_attendees= st.text_area("참석자 명단", value=str(row["참석인원"]))
                        new_agenda   = st.text_area("안건", value=str(row["안건"]))
                        new_decisions= st.text_area("결정사항", value=str(row["결정사항"]))

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
                    if pd.notna(row.get("스캔파일")) and row.get("스캔파일"):
                        fpath = os.path.join(SCANS_DIR, row["스캔파일"])
                        if os.path.exists(fpath) and row["스캔파일"].lower().endswith((".jpg", ".jpeg", ".png")):
                            st.image(fpath, caption=row["스캔파일"], width=300)
                        elif os.path.exists(fpath):
                            st.caption(f"📎 첨부파일: {row['스캔파일']}")
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

import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="연구회 세미나 매니저", layout="wide")

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

st.title("🏛️ 연구회 세미나 회의록 및 재무관리")

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
        c3, c4, c5 = st.columns([1, 1, 2])
        entry_type = c3.selectbox("구분", ["수입", "지출"])
        category = c4.text_input("항목명", placeholder="회비 / 강사비 / 식대 등")
        amount = c5.number_input("금액(원)", min_value=0, step=1000)
        note = st.text_input("비고 (입금자명 등)")
        scan_file = st.file_uploader("스캔 이미지 첨부 (JPG, PNG, PDF)", type=["jpg", "jpeg", "png", "pdf"])

    if st.button("💾 회의록 및 내역 저장하기", use_container_width=True):
        scan_filename = ""
        if scan_file is not None:
            scan_filename = f"{date.strftime('%Y%m%d')}_{scan_file.name}"
            with open(os.path.join(SCANS_DIR, scan_filename), "wb") as f:
                f.write(scan_file.read())

        new_data = {
            "날짜": date.strftime("%Y-%m-%d"), "주제": title, "장소": location,
            "참석인원": attendees, "안건": agenda, "결정사항": decisions,
            "유형": entry_type, "항목": category, "금액": amount, "비고": note,
            "스캔파일": scan_filename
        }
        st.session_state['df'] = pd.concat([st.session_state['df'], pd.DataFrame([new_data])], ignore_index=True)
        save_data(st.session_state['df'])
        st.success("회의록과 내역이 성공적으로 기록되었습니다!")

# 2. 회의록 아카이브 (문서 형태 조회)
elif menu == "📜 회의록 아카이브":
    st.subheader("📚 역대 회의록 기록")
    df = st.session_state['df']
    if not df.empty:
        unique_seminars = df.drop_duplicates(subset=["날짜", "주제"])
        for _, row in unique_seminars.iterrows():
            with st.container():
                st.markdown(f"### {row['날짜']} | {row['주제']}")
                st.info(f"📍 **장소:** {row['장소']}  |  👥 **참석자:** {row['참석인원']}")
                st.write(f"**📝 안건:** {row['안건']}")
                st.write(f"**✅ 결정사항:** {row['결정사항']}")
                if pd.notna(row.get("스캔파일")) and row.get("스캔파일"):
                    fpath = os.path.join(SCANS_DIR, row["스캔파일"])
                    if os.path.exists(fpath) and row["스캔파일"].lower().endswith((".jpg", ".jpeg", ".png")):
                        st.image(fpath, caption=row["스캔파일"], width=300)
                    elif os.path.exists(fpath):
                        st.caption(f"📎 첨부파일: {row['스캔파일']}")
                st.divider()
    else:
        st.info("기록된 회의록이 없습니다.")

# 3. 재무 엑셀 리포트 (엑셀 형식)
elif menu == "💰 재무 엑셀 리포트":
    st.subheader("📊 수입 및 지출 재무 제표 (Excel)")
    df = st.session_state['df']

    if not df.empty:
        # 수입 테이블
        st.write("### 🟢 수입 내역 (Incomes)")
        income_df = df[df["유형"] == "수입"][["날짜", "항목", "금액", "비고"]]
        st.table(income_df)

        # 지출 테이블
        st.write("### 🔴 지출 내역 (Expenses)")
        expense_df = df[df["유형"] == "지출"][["날짜", "항목", "금액", "비고"]]
        st.table(expense_df)

        # 통계 요약
        total_in = income_df["금액"].sum()
        total_out = expense_df["금액"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("총 수입", f"{total_in:,}원")
        c2.metric("총 지출", f"{total_out:,}원")
        c3.metric("현재 잔액", f"{total_in - total_out:,}원")

        # 엑셀 다운로드 버튼
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📤 전체 내역 엑셀로 내보내기", csv, "seminar_finance_report.csv", "text/csv")
    else:
        st.info("금융 내역이 없습니다.")

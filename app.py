import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import uuid
from datetime import datetime, date
from io import BytesIO

# ── 경로 설정 ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RECEIPTS_DIR = os.path.join(DATA_DIR, "receipts")
SEMINARS_CSV = os.path.join(DATA_DIR, "seminars.csv")
EXPENSES_CSV = os.path.join(DATA_DIR, "expenses.csv")

os.makedirs(RECEIPTS_DIR, exist_ok=True)

EXPENSE_CATEGORIES = ["강사비", "식사비", "간식비", "기타"]

# ── CSV 초기화 / 로드 ──────────────────────────────────────────────────────────
def load_seminars() -> pd.DataFrame:
    if os.path.exists(SEMINARS_CSV):
        df = pd.read_csv(SEMINARS_CSV, parse_dates=["date"])
        return df
    return pd.DataFrame(columns=["id", "date", "title", "location", "attendees", "agenda", "created_at"])


def load_expenses() -> pd.DataFrame:
    if os.path.exists(EXPENSES_CSV):
        return pd.read_csv(EXPENSES_CSV)
    return pd.DataFrame(columns=["id", "seminar_id", "category", "amount", "sponsorship", "receipt_filename"])


def save_seminars(df: pd.DataFrame):
    df.to_csv(SEMINARS_CSV, index=False)


def save_expenses(df: pd.DataFrame):
    df.to_csv(EXPENSES_CSV, index=False)


# ── 유틸 ──────────────────────────────────────────────────────────────────────
def format_krw(amount: int) -> str:
    return f"₩{amount:,}"


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="세미나_재무_기록")
    return buf.getvalue()


# ── 페이지: 세미나 등록 ────────────────────────────────────────────────────────
def page_register():
    st.header("세미나 등록")

    if "expense_rows" not in st.session_state:
        st.session_state.expense_rows = [{"category": "식사비", "amount": 0, "sponsorship": 0, "file": None}]

    with st.form("seminar_form", clear_on_submit=False):
        st.subheader("기본 정보")
        col1, col2 = st.columns(2)
        with col1:
            seminar_date = st.date_input("날짜", value=date.today())
            title = st.text_input("주제", placeholder="예: 딥러닝 최신 동향")
        with col2:
            location = st.text_input("장소", placeholder="예: 세미나실 A")
            attendees = st.number_input("참석 인원", min_value=0, step=1)

        agenda = st.text_area("회의 안건", placeholder="이번 모임에서 논의한 주요 안건을 입력하세요.", height=100)

        st.divider()
        st.subheader("지출 내역")
        st.caption("아래에 지출 항목을 추가하세요. 항목이 여러 개인 경우 행을 추가하세요.")

        # 동적 지출 행
        updated_rows = []
        for i, row in enumerate(st.session_state.expense_rows):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 3])
            with c1:
                cat = st.selectbox(
                    "항목",
                    EXPENSE_CATEGORIES,
                    index=EXPENSE_CATEGORIES.index(row["category"]) if row["category"] in EXPENSE_CATEGORIES else 0,
                    key=f"cat_{i}",
                )
            with c2:
                amt = st.number_input("금액 (원)", min_value=0, step=1000, value=row["amount"], key=f"amt_{i}")
            with c3:
                spon = st.number_input("후원비 (원)", min_value=0, step=1000, value=row["sponsorship"], key=f"spon_{i}")
            with c4:
                uploaded = st.file_uploader(
                    "영수증 (JPG/PNG/PDF)",
                    type=["jpg", "jpeg", "png", "pdf"],
                    key=f"file_{i}",
                    label_visibility="visible",
                )
            updated_rows.append({"category": cat, "amount": amt, "sponsorship": spon, "file": uploaded})

        st.session_state.expense_rows = updated_rows

        btn_col1, btn_col2, _ = st.columns([1, 1, 4])
        with btn_col1:
            add_row = st.form_submit_button("+ 항목 추가")
        with btn_col2:
            remove_row = st.form_submit_button("- 마지막 행 삭제")

        st.divider()
        submitted = st.form_submit_button("저장", type="primary", use_container_width=True)

    # 행 추가 / 삭제 (폼 제출 후 처리)
    if add_row:
        st.session_state.expense_rows.append({"category": "기타", "amount": 0, "sponsorship": 0, "file": None})
        st.rerun()

    if remove_row and len(st.session_state.expense_rows) > 1:
        st.session_state.expense_rows.pop()
        st.rerun()

    if submitted:
        if not title.strip():
            st.error("주제를 입력해 주세요.")
            return

        seminars = load_seminars()
        expenses = load_expenses()

        seminar_id = str(uuid.uuid4())[:8]
        new_seminar = {
            "id": seminar_id,
            "date": seminar_date.strftime("%Y-%m-%d"),
            "title": title.strip(),
            "location": location.strip(),
            "attendees": int(attendees),
            "agenda": agenda.strip(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        seminars = pd.concat([seminars, pd.DataFrame([new_seminar])], ignore_index=True)
        save_seminars(seminars)

        for row in st.session_state.expense_rows:
            receipt_filename = ""
            if row["file"] is not None:
                ext = os.path.splitext(row["file"].name)[1]
                receipt_filename = f"{seminar_id}_{str(uuid.uuid4())[:6]}{ext}"
                with open(os.path.join(RECEIPTS_DIR, receipt_filename), "wb") as f:
                    f.write(row["file"].read())

            new_expense = {
                "id": str(uuid.uuid4())[:8],
                "seminar_id": seminar_id,
                "category": row["category"],
                "amount": int(row["amount"]),
                "sponsorship": int(row["sponsorship"]),
                "receipt_filename": receipt_filename,
            }
            expenses = pd.concat([expenses, pd.DataFrame([new_expense])], ignore_index=True)

        save_expenses(expenses)

        st.success(f"'{title}' 세미나가 성공적으로 저장되었습니다!")
        st.session_state.expense_rows = [{"category": "식사비", "amount": 0, "sponsorship": 0, "file": None}]
        st.rerun()


# ── 페이지: 히스토리 조회 ──────────────────────────────────────────────────────
def page_history():
    st.header("히스토리 조회")

    seminars = load_seminars()
    expenses = load_expenses()

    if seminars.empty:
        st.info("등록된 세미나가 없습니다. 먼저 세미나를 등록해 주세요.")
        return

    seminars["date"] = pd.to_datetime(seminars["date"])

    # ── 필터 ──
    with st.expander("필터 옵션", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            min_date = seminars["date"].min().date()
            max_date = seminars["date"].max().date()
            date_from = st.date_input("시작일", value=min_date, key="hist_from")
        with col2:
            date_to = st.date_input("종료일", value=max_date, key="hist_to")
        with col3:
            cat_filter = st.multiselect(
                "지출 항목 필터",
                EXPENSE_CATEGORIES,
                default=[],
                placeholder="전체 (선택 없음 = 전체)",
            )

    # 날짜 필터
    mask = (seminars["date"].dt.date >= date_from) & (seminars["date"].dt.date <= date_to)
    filtered = seminars[mask].sort_values("date", ascending=False).reset_index(drop=True)

    # 지출 항목 필터 적용 (해당 항목이 있는 세미나만 표시)
    if cat_filter:
        valid_ids = expenses[expenses["category"].isin(cat_filter)]["seminar_id"].unique()
        filtered = filtered[filtered["id"].isin(valid_ids)]

    # 지출 집계를 세미나에 병합
    if not expenses.empty:
        exp_agg = expenses.groupby("seminar_id").agg(
            total_amount=("amount", "sum"),
            total_sponsorship=("sponsorship", "sum"),
        ).reset_index()
        exp_agg["net_expense"] = exp_agg["total_amount"] - exp_agg["total_sponsorship"]
        merged = filtered.merge(exp_agg, left_on="id", right_on="seminar_id", how="left")
    else:
        merged = filtered.copy()
        merged["total_amount"] = 0
        merged["total_sponsorship"] = 0
        merged["net_expense"] = 0

    merged[["total_amount", "total_sponsorship", "net_expense"]] = (
        merged[["total_amount", "total_sponsorship", "net_expense"]].fillna(0).astype(int)
    )

    st.markdown(f"**총 {len(merged)}건** 조회됨")

    # ── 타임라인 테이블 ──
    display_cols = {
        "date": "날짜",
        "title": "주제",
        "location": "장소",
        "attendees": "참석 인원",
        "total_amount": "총 지출",
        "total_sponsorship": "후원비",
        "net_expense": "순 지출",
    }
    table_df = merged[[c for c in display_cols if c in merged.columns]].rename(columns=display_cols)
    table_df["날짜"] = table_df["날짜"].dt.strftime("%Y-%m-%d")
    for col in ["총 지출", "후원비", "순 지출"]:
        if col in table_df.columns:
            table_df[col] = table_df[col].apply(format_krw)

    st.dataframe(table_df, use_container_width=True, hide_index=True)

    # ── 세미나 상세 보기 ──
    if not merged.empty:
        st.divider()
        st.subheader("세미나 상세 보기")
        options = merged.apply(lambda r: f"{r['date'].strftime('%Y-%m-%d')} — {r['title']}", axis=1).tolist()
        selected_label = st.selectbox("세미나 선택", options)
        idx = options.index(selected_label)
        row = merged.iloc[idx]

        c1, c2, c3 = st.columns(3)
        c1.metric("날짜", row["date"].strftime("%Y-%m-%d"))
        c2.metric("참석 인원", f"{int(row['attendees'])}명")
        c3.metric("장소", row["location"] if row["location"] else "-")

        if row.get("agenda"):
            st.markdown("**회의 안건**")
            st.write(row["agenda"])

        # 해당 세미나 지출
        sem_expenses = expenses[expenses["seminar_id"] == row["id"]]
        if not sem_expenses.empty:
            st.markdown("**지출 내역**")
            exp_display = sem_expenses[["category", "amount", "sponsorship", "receipt_filename"]].copy()
            exp_display.columns = ["항목", "금액", "후원비", "영수증"]
            exp_display["금액"] = exp_display["금액"].apply(format_krw)
            exp_display["후원비"] = exp_display["후원비"].apply(format_krw)
            exp_display["영수증"] = exp_display["영수증"].apply(lambda x: "첨부됨" if x else "-")
            st.dataframe(exp_display, use_container_width=True, hide_index=True)

            # 영수증 이미지 미리보기
            receipt_files = sem_expenses["receipt_filename"].dropna()
            receipt_files = receipt_files[receipt_files != ""]
            if not receipt_files.empty:
                st.markdown("**영수증 미리보기**")
                img_cols = st.columns(min(len(receipt_files), 3))
                for i, fname in enumerate(receipt_files):
                    fpath = os.path.join(RECEIPTS_DIR, fname)
                    if os.path.exists(fpath) and fname.lower().endswith((".jpg", ".jpeg", ".png")):
                        img_cols[i % 3].image(fpath, caption=fname, use_container_width=True)

    # ── 내보내기 ──
    st.divider()
    st.subheader("데이터 내보내기")
    if not expenses.empty and not seminars.empty:
        full_df = seminars.merge(expenses, left_on="id", right_on="seminar_id", how="left", suffixes=("", "_exp"))
        export_cols = ["date", "title", "location", "attendees", "agenda", "category", "amount", "sponsorship", "receipt_filename"]
        export_cols = [c for c in export_cols if c in full_df.columns]
        export_df = full_df[export_cols].copy()
        export_df.rename(columns={
            "date": "날짜", "title": "주제", "location": "장소", "attendees": "참석인원",
            "agenda": "회의안건", "category": "지출항목", "amount": "금액",
            "sponsorship": "후원비", "receipt_filename": "영수증파일명",
        }, inplace=True)
    else:
        export_df = merged.copy()

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        csv_data = export_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "CSV 다운로드",
            data=csv_data.encode("utf-8-sig"),
            file_name=f"seminar_records_{date.today()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_dl2:
        st.download_button(
            "Excel 다운로드",
            data=to_excel_bytes(export_df),
            file_name=f"seminar_records_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


# ── 페이지: 통계 분석 ──────────────────────────────────────────────────────────
def page_analytics():
    st.header("통계 및 재무 분석")

    seminars = load_seminars()
    expenses = load_expenses()

    if seminars.empty or expenses.empty:
        st.info("분석할 데이터가 없습니다. 세미나와 지출 내역을 먼저 등록해 주세요.")
        return

    seminars["date"] = pd.to_datetime(seminars["date"])

    # ── 상단 요약 지표 ──
    total_expense = int(expenses["amount"].sum())
    total_sponsorship = int(expenses["sponsorship"].sum())
    net_expense = total_expense - total_sponsorship
    total_seminars = len(seminars)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("총 세미나 수", f"{total_seminars}회")
    m2.metric("총 지출", format_krw(total_expense))
    m3.metric("총 후원비", format_krw(total_sponsorship))
    m4.metric("순 지출 (Net Expense)", format_krw(net_expense))

    st.divider()

    col_l, col_r = st.columns(2)

    # ── 항목별 지출 파이 차트 ──
    with col_l:
        st.subheader("항목별 지출 비중")
        cat_sum = expenses.groupby("category")["amount"].sum().reset_index()
        cat_sum.columns = ["항목", "금액"]
        fig_pie = px.pie(
            cat_sum,
            names="항목",
            values="금액",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            hole=0.35,
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(showlegend=True, margin=dict(t=20, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── 항목별 지출 막대 그래프 ──
    with col_r:
        st.subheader("항목별 지출 금액")
        fig_bar = px.bar(
            cat_sum.sort_values("금액", ascending=False),
            x="항목",
            y="금액",
            color="항목",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            text_auto=True,
        )
        fig_bar.update_traces(texttemplate="₩%{y:,}")
        fig_bar.update_layout(showlegend=False, yaxis_tickformat=",", margin=dict(t=20, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # ── 세미나별 지출 추이 ──
    st.subheader("세미나별 지출 추이")
    sem_exp = expenses.groupby("seminar_id").agg(
        total_amount=("amount", "sum"),
        total_sponsorship=("sponsorship", "sum"),
    ).reset_index()
    sem_exp["net"] = sem_exp["total_amount"] - sem_exp["total_sponsorship"]
    timeline = seminars.merge(sem_exp, left_on="id", right_on="seminar_id", how="left").fillna(0)
    timeline = timeline.sort_values("date")
    timeline["label"] = timeline["date"].dt.strftime("%Y-%m-%d") + "\n" + timeline["title"]

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(
        x=timeline["label"], y=timeline["total_amount"],
        name="총 지출", marker_color="#636EFA",
    ))
    fig_trend.add_trace(go.Bar(
        x=timeline["label"], y=timeline["total_sponsorship"],
        name="후원비", marker_color="#00CC96",
    ))
    fig_trend.add_trace(go.Scatter(
        x=timeline["label"], y=timeline["net"],
        name="순 지출", mode="lines+markers",
        line=dict(color="#EF553B", width=2),
    ))
    fig_trend.update_layout(
        barmode="group",
        yaxis_tickformat=",",
        legend=dict(orientation="h", y=1.08),
        margin=dict(t=40, b=80),
        xaxis_tickangle=-30,
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.divider()

    # ── 수지 분석 테이블 ──
    st.subheader("수지 분석 상세")
    analysis = timeline[["date", "title", "total_amount", "total_sponsorship", "net"]].copy()
    analysis["date"] = analysis["date"].dt.strftime("%Y-%m-%d")
    analysis.columns = ["날짜", "주제", "총 지출", "후원비", "순 지출"]
    for col in ["총 지출", "후원비", "순 지출"]:
        analysis[col] = analysis[col].astype(int).apply(format_krw)

    sponsorship_ratio = (total_sponsorship / total_expense * 100) if total_expense > 0 else 0
    st.dataframe(analysis, use_container_width=True, hide_index=True)
    st.caption(f"후원비 충당률: **{sponsorship_ratio:.1f}%** (총 지출 대비 후원비 비율)")


# ── 메인 앱 ───────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="연구회 세미나 관리",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    with st.sidebar:
        st.title("📚 연구회 세미나 관리")
        st.caption("세미나 기록 및 재무 관리 시스템")
        st.divider()
        page = st.radio(
            "메뉴",
            ["세미나 등록", "히스토리 조회", "통계 분석"],
            format_func=lambda x: {
                "세미나 등록": "✏️  세미나 등록",
                "히스토리 조회": "📋  히스토리 조회",
                "통계 분석": "📊  통계 분석",
            }[x],
        )
        st.divider()

        # 사이드바 요약
        seminars = load_seminars()
        expenses = load_expenses()
        st.metric("등록된 세미나", f"{len(seminars)}회")
        if not expenses.empty:
            total = int(expenses["amount"].sum())
            st.metric("누적 지출", format_krw(total))

    if page == "세미나 등록":
        page_register()
    elif page == "히스토리 조회":
        page_history()
    elif page == "통계 분석":
        page_analytics()


if __name__ == "__main__":
    main()

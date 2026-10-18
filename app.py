import datetime
import streamlit as st

# ============================================================
# アプリケーション基本設定
# ============================================================
st.set_page_config(
    page_title="スケジュール管理システム",
    page_icon="📅",
    layout="wide",
)

# カスタムCSSスタイル
st.markdown(
    """
<style>
    .inspection-badge {
        background-color: #fee2e2;
        color: #b91c1c;
        border: 2px solid #ef4444;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 0.85rem;
        display: inline-block;
        box-shadow: 0 2px 4px rgba(239, 68, 68, 0.2);
        animation: pulse 2s infinite ease-in-out;
    }
    .default-badge {
        background-color: #f1f5f9;
        color: #334155;
        border: 1px solid #cbd5e1;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .schedule-card-inspection {
        border-left: 6px solid #ef4444 !important;
        background-color: #fffafb;
    }
</style>
""",
    unsafe_allow_html=True,
)

# カテゴリの定義
CATEGORIES = ["通常業務", "定期点検", "改修工事", "安全確認"]

# セッション状態の初期化（初期サンプルデータ含む）
if "schedules" not in st.session_state:
    now = datetime.datetime.now()
    st.session_state.schedules = [
        {
            "id": 1,
            "title": "空調設備・給排水システムの法定点検",
            "datetime": now.replace(hour=10, minute=0, second=0, microsecond=0)
            + datetime.timedelta(days=1),
            "category": "定期点検",
            "memo": "全フロアの空調フィルター交換および動作確認",
        },
        {
            "id": 2,
            "title": "週次プロジェクト進捗ミーティング",
            "datetime": now.replace(hour=13, minute=30, second=0, microsecond=0),
            "category": "通常業務",
            "memo": "進捗共有および課題の洗い出し",
        },
        {
            "id": 3,
            "title": "エントランス自動ドア制御盤の更新",
            "datetime": now.replace(hour=9, minute=0, second=0, microsecond=0)
            + datetime.timedelta(days=3),
            "category": "改修工事",
            "memo": "業者立ち会いおよび安全エリア確保",
        },
        {
            "id": 4,
            "title": "避難経路および非常口の安全巡回",
            "datetime": now.replace(hour=16, minute=0, second=0, microsecond=0)
            + datetime.timedelta(days=2),
            "category": "安全確認",
            "memo": "非常扉前の荷物撤去確認",
        },
    ]

# タイトルヘッダー
st.title("📅 スケジュール管理ダッシュボード")
st.caption(
    "業務スケジュールの登録・確認を行えます。定期点検スケジュールはバッジでハイライトされます。"
)
st.divider()

# メインレイアウト（左：登録フォーム、右：スケジュール一覧）
col_form, col_list = st.columns([1, 1.6], gap="large")

# ============================================================
# 1. スケジュール登録フォーム
# ============================================================
with col_form:
    st.subheader("➕ スケジュール登録")

    with st.form("schedule_form", clear_on_submit=True):
        # 1. タイトル
        title = st.text_input(
            "タイトル",
            placeholder="例: 第1電気室 設備点検",
            help="予定のタイトルを入力してください",
        )

        # 2. 日時
        st.markdown("**日時**")
        dt_col1, dt_col2 = st.columns(2)
        with dt_col1:
            schedule_date = st.date_input("日付", value=datetime.date.today())
        with dt_col2:
            schedule_time = st.time_input(
                "時刻", value=datetime.time(10, 0), step=1800
            )

        # 3. カテゴリ
        category = st.selectbox(
            "カテゴリ",
            options=CATEGORIES,
            help="該当する業務カテゴリを選択してください",
        )

        # 備考・メモ
        memo = st.text_area(
            "詳細・メモ（任意）",
            placeholder="詳細な作業内容や担当者などを入力",
            height=100,
        )

        submitted = st.form_submit_button(
            "登録する", type="primary", use_container_width=True
        )

        if submitted:
            if not title.strip():
                st.error("⚠️ タイトルを入力してください。")
            else:
                combined_dt = datetime.datetime.combine(
                    schedule_date, schedule_time
                )
                new_schedule = {
                    "id": int(datetime.datetime.now().timestamp() * 1000),
                    "title": title.strip(),
                    "datetime": combined_dt,
                    "category": category,
                    "memo": memo.strip(),
                }
                st.session_state.schedules.append(new_schedule)
                st.success(f"✅ スケジュール「{title}」を登録しました！")
                st.rerun()

# ============================================================
# 2. スケジュール一覧画面
# ============================================================
with col_list:
    st.subheader("📋 スケジュール一覧")

    # 絞り込みフィルター & ソート
    filter_col1, filter_col2 = st.columns([1.5, 1])
    with filter_col1:
        category_filter = st.selectbox(
            "カテゴリで絞り込み",
            options=["すべて"] + CATEGORIES,
            index=0,
        )
    with filter_col2:
        sort_order = st.selectbox(
            "並び順",
            options=["日時が近い順", "日時が遠い順"],
            index=0,
        )

    # フィルタリング
    display_list = st.session_state.schedules
    if category_filter != "すべて":
        display_list = [
            s for s in display_list if s["category"] == category_filter
        ]

    # ソート
    display_list = sorted(
        display_list,
        key=lambda x: x["datetime"],
        reverse=(sort_order == "日時が遠い順"),
    )

    st.write(f"表示件数: **{len(display_list)}件**")

    if not display_list:
        st.info("該当するスケジュールはありません。")
    else:
        for item in display_list:
            is_inspection = item["category"] == "定期点検"

            with st.container(border=True):
                head_col, action_col = st.columns([5, 1])

                with head_col:
                    # カテゴリに応じたバッジ表示（定期点検は特大強調バッジ）
                    if is_inspection:
                        badge_html = '<span class="inspection-badge">【🚨 定期点検】</span>'
                    else:
                        badge_html = f'<span class="default-badge">【{item["category"]}】</span>'

                    # タイトルとバッジの表示
                    st.markdown(
                        f"""
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                            <h4 style="margin: 0; padding: 0;">{item['title']}</h4>
                            {badge_html}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # 日時の表示
                    dt_str = item["datetime"].strftime("%Y年%m月%d日（%a） %H:%M")
                    st.markdown(f"🕒 **日時**: `{dt_str}`")

                    # メモの表示
                    if item.get("memo"):
                        st.caption(f"📝 {item['memo']}")

                with action_col:
                    if st.button("削除", key=f"del_{item['id']}"):
                        st.session_state.schedules = [
                            s
                            for s in st.session_state.schedules
                            if s["id"] != item["id"]
                        ]
                        st.rerun()

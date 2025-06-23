import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib as mpl
import os

# フォントパス指定（Streamlit Cloud用に絶対パス化）
import pathlib
font_path = str(pathlib.Path("font/NotoSansJP-VariableFont_wght.ttf").resolve())

# フォントを登録
fm.fontManager.addfont(font_path)
font_prop = fm.FontProperties(fname=font_path)

# matplotlibにフォントを設定
mpl.rcParams["font.family"] = font_prop.get_name()
mpl.rcParams["axes.unicode_minus"] = False

# チームカラー辞書（例）
TEAM_COLORS = {
    "giants": "#f97709", "hanshin": "#ffe201", "dragons": "#002569",
    "baystars": "#0091e1", "swallows": "#98c145", "carp": "#ff0000",
    "hawks": "#fcc700", "lions": "#0071c0", "eagles": "#870010",
    "marines": "#c0c0c0", "Buffaloes": "#000000", "fighters": "#01609a"
}

# データ読み込み
def load_data():
    conn = sqlite3.connect("pitching_stats.db")
    df = pd.read_sql_query("SELECT * FROM pitching_stats", conn)
    conn.close()
    return df

df = load_data()

df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["IP_"] = pd.to_numeric(df["IP_"], errors="coerce")
df["登板"] = pd.to_numeric(df["登板"], errors="coerce")
df["先発"] = pd.to_numeric(df["先発"], errors="coerce")


# フィルター
years = sorted(df["year"].dropna().unique())
teams = sorted(df["team_name"].dropna().unique())

with st.sidebar:
    selected_year = st.selectbox("年度を選択", years, index=len(years) - 1)
    team_mode = st.radio("チーム範囲", ["12球団", "セ・パ6球団", "1球団"])
    if team_mode == "1球団":
        selected_teams = st.multiselect("チームを選択", teams, default=teams[0])
    elif team_mode == "セ・パ6球団":
        league_selection = st.radio("リーグを選択", ["セ・リーグ", "パ・リーグ"])
        if league_selection == "セ・リーグ":
            selected_teams = [t for t in teams if t in ["giants", "hanshin", "dragons", "baystars", "swallows", "carp"]]
        else:
            selected_teams = [t for t in teams if t in ["hawks", "lions", "eagles", "marines", "Buffaloes", "fighters"]]
    else:
        selected_teams = teams
    # モード選択追加
    mode = st.radio("モード選択", ["投手", "野手"])

# グローバルフィルター
if mode == "投手":
    df_filtered = df[(df["year"] == selected_year) & (df["team_name"].isin(selected_teams))]
else:
    df_filtered = pd.DataFrame()  # 野手用のデータ読み込みが後日実装される前提

# タブ定義
if mode == "投手":
    tabs = st.tabs([
        "🏆 項目別ランキング",
        "📈 昨年→今年 比較ランキング",
        "📊 年度別推移",
        "🏟 チーム別比較",
        "📌 詳細解析",
        "🚀 ブレイク選手",
        "📋 サマリーパネル",
        "🧱 選手層（年齢×ポジション）"
    ])
else:
    tabs = st.tabs([
        "🏆 野手ランキング（未実装）",
        "📊 野手年度推移（未実装）",
        "🏟 チーム打撃比較（未実装）"
    ])

# 今後、各タブに処理を追加していく（この構造で分岐・分割）
with tabs[0]:
    if mode == "野手":
        st.info("野手モードは現在未実装です。")
        st.stop()
    st.write("### 項目別ランキング")
    
    min_ip = st.slider("最低投球回", 0, 200, 30)
    min_games = st.slider("最低登板数", 0, 50, 10)
    min_starts = st.slider("最低先発数", 0, 30, 0)
    min_reliever = st.slider("最低中継ぎ登板数", 0, 100, 0)
    
    metric = st.selectbox("ランキング指標を選択", [
    "防御率","投球回","勝率","勝","敗","セーブ","HP",
    "登板", "先発", "完封", "完投", "QS", "QS率", "HQS","HQS率",
    "奪三振", "奪三率", "与四球", "四球率", "与死球", "死球率",
    "被安打", "被打率", "圏打率", "圏率差", "圏安打",
    "右被率", "右率差", "右被安", "左被率", "左率差",
    "被本率", "K/BB", "WHIP", "許盗率", "暴投",
    "K/9", "BB/9", "K-BB%", "Command+"
    ])
    ascending = st.radio("並べ替え順", ["昇順", "降順"]) == "昇順"
    top_n = st.slider("表示件数", 1, 30, 10)

    # 指標数値変換
    df_rank = df_filtered.copy()
    for col in [metric, "IP_", "登板", "先発"]:
        df_rank[col] = pd.to_numeric(df_rank[col], errors="coerce")

    df_rank = df_rank.dropna(subset=[metric])
    df_rank["中継ぎ"] = (df_rank["登板"] - df_rank["先発"]).abs()
    df_rank = df_rank[
        (df_rank["IP_"] >= min_ip) &
        (df_rank["登板"] >= min_games) &
        (df_rank["先発"] >= min_starts) &
        (df_rank["中継ぎ"] >= min_reliever)
    ]

    df_rank = df_rank.sort_values(metric, ascending=ascending).head(top_n)

    st.dataframe(df_rank[["選手名", "team_name", "year", metric]])

    # 棒グラフ
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.barh(df_rank["選手名"], df_rank[metric], color="#4fc3f7")
    ax.invert_yaxis()
    ax.set_xlabel(metric)
    ax.set_title(f"{selected_year}年 {metric} ランキング")
    st.pyplot(fig)

with tabs[1]:
    if mode == "野手":
        st.info("野手モードは現在未実装です。")
        st.stop()
    st.write("### 昨年→今年 比較ランキング（未実装）")

with tabs[2]:
    if mode == "野手":
        st.info("野手モードは現在未実装です。")
        st.stop()
    st.write("### 年度別推移（未実装）")

with tabs[3]:
    if mode == "野手":
        st.info("野手モードは現在未実装です。")
        st.stop()
    st.write("### チーム別成績比較")

    metric = st.selectbox("比較指標を選択", [
        "防御率", "奪三振", "与四球", "被安打", "被本率", "WHIP", "K/9", "BB/9", "QS率",
        "K/BB", "被打率", "HQS率", "奪三率", "四球率", "完封", "完投", "与死球", "許盗率",
        "勝-セーブ",
    ])
    ascending = st.radio("並び替え", ["昇順", "降順"]) == "昇順"

    # 指標ごとの集計方式
    AGG_METHOD = {
        "防御率": "weighted_era",
        "奪三振": "sum",
        "与四球": "sum",
        "被安打": "sum",
        "被本率": "weighted_hr9",
        "WHIP": "recalc_whip",
        "K/9": "weighted_k9",
        "BB/9": "weighted_bb9",
        "QS率": "weighted_qs",
        "K/BB": "recalc_kbb",
        "被打率": "recalc_avg",
        "HQS率": "weighted_hqs",
        "奪三率": "weighted_k9",
        "四球率": "weighted_bb9",
        "完封": "sum",
        "完投": "sum",
        "与死球": "sum",
        "許盗率": "weighted_sb",
        "勝-セーブ": "sum_diff_win_sv",
    }

    df_team = df_filtered.copy()
    agg_type = AGG_METHOD.get(metric, "mean")
    if metric not in ["勝-セーブ"]:  # 実在しない列はスキップ
        df_team[metric] = pd.to_numeric(df_team[metric], errors="coerce")
    df_team["IP_"] = pd.to_numeric(df_team["IP_"], errors="coerce")

    if agg_type == "weighted_era":
        df_team["自責点"] = df_team["防御率"] * df_team["IP_"] / 9
        df_grouped = df_team.groupby("team_name").agg({"自責点": "sum", "IP_": "sum"})
        df_grouped["防御率"] = df_grouped["自責点"] / df_grouped["IP_"] * 9
        df_grouped = df_grouped["防御率"].dropna().sort_values(ascending=ascending)

    elif agg_type == "weighted_hr9":
        df_team["被本率"] = pd.to_numeric(df_team["被本率"], errors="coerce")
        df_team["被本数_推定"] = df_team["被本率"] * df_team["IP_"] / 9
        df_grouped = df_team.groupby("team_name").agg({"被本数_推定": "sum", "IP_": "sum"})
        df_grouped["被本率"] = df_grouped["被本数_推定"] / df_grouped["IP_"] * 9
        df_grouped = df_grouped["被本率"].dropna().sort_values(ascending=ascending)

    elif agg_type == "recalc_whip":
        df_team["WHIP"] = pd.to_numeric(df_team["WHIP"], errors="coerce")
        df_team["被安打"] = pd.to_numeric(df_team["被安打"], errors="coerce")
        df_team["与四球"] = pd.to_numeric(df_team["与四球"], errors="coerce")
        df_team["WHIP_分子"] = df_team["被安打"] + df_team["与四球"]
        df_grouped = df_team.groupby("team_name").agg({"WHIP_分子": "sum", "IP_": "sum"})
        df_grouped["WHIP"] = df_grouped["WHIP_分子"] / df_grouped["IP_"]
        df_grouped = df_grouped["WHIP"].dropna().sort_values(ascending=ascending)

    elif agg_type == "weighted_k9":
        df_team["奪三振"] = pd.to_numeric(df_team["奪三振"], errors="coerce")
        df_grouped = df_team.groupby("team_name").agg({"奪三振": "sum", "IP_": "sum"})
        df_grouped["K/9"] = df_grouped["奪三振"] / df_grouped["IP_"] * 9
        df_grouped = df_grouped["K/9"].dropna().sort_values(ascending=ascending)

    elif agg_type == "weighted_bb9":
        df_team["与四球"] = pd.to_numeric(df_team["与四球"], errors="coerce")
        df_grouped = df_team.groupby("team_name").agg({"与四球": "sum", "IP_": "sum"})
        df_grouped["BB/9"] = df_grouped["与四球"] / df_grouped["IP_"] * 9
        df_grouped = df_grouped["BB/9"].dropna().sort_values(ascending=ascending)

    elif agg_type == "weighted_qs":
        df_team["QS"] = pd.to_numeric(df_team["QS"], errors="coerce")
        df_team["先発"] = pd.to_numeric(df_team["先発"], errors="coerce")
        df_grouped = df_team.groupby("team_name").agg({"QS": "sum", "先発": "sum"})
        df_grouped["QS率"] = df_grouped["QS"] / df_grouped["先発"]
        df_grouped = df_grouped["QS率"].dropna().sort_values(ascending=ascending)

    elif agg_type == "recalc_kbb":
        df_team["奪三振"] = pd.to_numeric(df_team["奪三振"], errors="coerce")
        df_team["与四球"] = pd.to_numeric(df_team["与四球"], errors="coerce")
        df_grouped = df_team.groupby("team_name").agg({"奪三振": "sum", "与四球": "sum"})
        df_grouped["K/BB"] = df_grouped["奪三振"] / df_grouped["与四球"]
        df_grouped = df_grouped["K/BB"].dropna().sort_values(ascending=ascending)

    elif agg_type == "recalc_avg":
        df_team["被安打"] = pd.to_numeric(df_team["被安打"], errors="coerce")
        df_team["打数"] = pd.to_numeric(df_team["打数"], errors="coerce")
        df_grouped = df_team.groupby("team_name").agg({"被安打": "sum", "打数": "sum"})
        df_grouped["被打率"] = df_grouped["被安打"] / df_grouped["打数"]
        df_grouped = df_grouped["被打率"].dropna().sort_values(ascending=ascending)

    elif agg_type == "weighted_hqs":
        df_team["HQS"] = pd.to_numeric(df_team["HQS"], errors="coerce")
        df_team["先発"] = pd.to_numeric(df_team["先発"], errors="coerce")
        df_grouped = df_team.groupby("team_name").agg({"HQS": "sum", "先発": "sum"})
        df_grouped["HQS率"] = df_grouped["HQS"] / df_grouped["先発"]
        df_grouped = df_grouped["HQS率"].dropna().sort_values(ascending=ascending)

    elif agg_type == "sum_diff_win_sv":
        df_team["勝"] = pd.to_numeric(df_team["勝"], errors="coerce")
        df_team["セーブ"] = pd.to_numeric(df_team["セーブ"], errors="coerce")
        df_team["勝-セーブ"] = df_team["勝"] - df_team["セーブ"]
        df_grouped = df_team.groupby("team_name")["勝-セーブ"].sum().dropna().sort_values(ascending=ascending)

    elif agg_type == "sum":
        df_grouped = df_team.groupby("team_name")[metric].sum().dropna().sort_values(ascending=ascending)

    elif agg_type == "weighted_sb":
        df_team["許盗数"] = pd.to_numeric(df_team["許盗数"], errors="coerce")
        df_team["被盗企"] = pd.to_numeric(df_team["被盗企"], errors="coerce")
        df_grouped = df_team.groupby("team_name").agg({"許盗数": "sum", "被盗企": "sum"})
        df_grouped["許盗率"] = df_grouped["許盗数"] / df_grouped["被盗企"]
        df_grouped = df_grouped["許盗率"].dropna().sort_values(ascending=ascending)

    else:
        df_grouped = df_team.groupby("team_name")[metric].mean().dropna().sort_values(ascending=ascending)

    # 横並びレイアウト
    col1, col2 = st.columns([2, 1])

    with col1:
        fig, ax = plt.subplots()
        ax.barh(df_grouped.index, df_grouped.values, color=[TEAM_COLORS.get(t, '#90caf9') for t in df_grouped.index])
        ax.set_xlabel(metric)
        ax.set_title(f"{selected_year}年 チーム別 {metric}")
        ax.invert_yaxis()
        st.pyplot(fig)

    with col2:
        st.dataframe(df_grouped.reset_index().rename(columns={metric: f"{metric}"}))

    st.markdown("### 各指標で上位/下位チーム一覧")

    display_mode = st.radio("表示モード", ["上位3チーム", "ワースト3チーム"])

    summary_results = []
    for m, agg in AGG_METHOD.items():
        try:
            temp = df_team.copy()
            temp["IP_"] = pd.to_numeric(temp["IP_"], errors="coerce")

            if agg == "weighted_era":
                temp["自責点"] = pd.to_numeric(temp["防御率"], errors="coerce") * temp["IP_"] / 9
                g = temp.groupby("team_name").agg({"自責点": "sum", "IP_": "sum"})
                g["値"] = g["自責点"] / g["IP_"] * 9
            elif agg == "weighted_hr9":
                temp["被本率"] = pd.to_numeric(temp["被本率"], errors="coerce")
                temp["被本数_推定"] = temp["被本率"] * temp["IP_"] / 9
                g = temp.groupby("team_name").agg({"被本数_推定": "sum", "IP_": "sum"})
                g["値"] = g["被本数_推定"] / g["IP_"] * 9
            elif agg == "recalc_whip":
                temp["被安打"] = pd.to_numeric(temp["被安打"], errors="coerce")
                temp["与四球"] = pd.to_numeric(temp["与四球"], errors="coerce")
                g = temp.groupby("team_name").agg({"被安打": "sum", "与四球": "sum", "IP_": "sum"})
                g["値"] = (g["被安打"] + g["与四球"]) / g["IP_"]
            elif agg == "weighted_k9":
                temp["奪三振"] = pd.to_numeric(temp["奪三振"], errors="coerce")
                g = temp.groupby("team_name").agg({"奪三振": "sum", "IP_": "sum"})
                g["値"] = g["奪三振"] / g["IP_"] * 9
            elif agg == "weighted_bb9":
                temp["与四球"] = pd.to_numeric(temp["与四球"], errors="coerce")
                g = temp.groupby("team_name").agg({"与四球": "sum", "IP_": "sum"})
                g["値"] = g["与四球"] / g["IP_"] * 9
            elif agg == "weighted_qs":
                temp["QS"] = pd.to_numeric(temp["QS"], errors="coerce")
                temp["先発"] = pd.to_numeric(temp["先発"], errors="coerce")
                g = temp.groupby("team_name").agg({"QS": "sum", "先発": "sum"})
                g["値"] = g["QS"] / g["先発"]
            elif agg == "recalc_kbb":
                temp["奪三振"] = pd.to_numeric(temp["奪三振"], errors="coerce")
                temp["与四球"] = pd.to_numeric(temp["与四球"], errors="coerce")
                g = temp.groupby("team_name").agg({"奪三振": "sum", "与四球": "sum"})
                g["値"] = g["奪三振"] / g["与四球"]
            elif agg == "recalc_avg":
                temp["被安打"] = pd.to_numeric(temp["被安打"], errors="coerce")
                temp["打数"] = pd.to_numeric(temp["打数"], errors="coerce")
                g = temp.groupby("team_name").agg({"被安打": "sum", "打数": "sum"})
                g["値"] = g["被安打"] / g["打数"]
            elif agg == "weighted_hqs":
                temp["HQS"] = pd.to_numeric(temp["HQS"], errors="coerce")
                temp["先発"] = pd.to_numeric(temp["先発"], errors="coerce")
                g = temp.groupby("team_name").agg({"HQS": "sum", "先発": "sum"})
                g["値"] = g["HQS"] / g["先発"]
            elif agg == "sum_diff_win_sv":
                temp["勝"] = pd.to_numeric(temp["勝"], errors="coerce")
                temp["セーブ"] = pd.to_numeric(temp["セーブ"], errors="coerce")
                temp["値"] = temp["勝"] - temp["セーブ"]
                g = temp.groupby("team_name")["値"].sum().to_frame()
            elif agg == "sum":
                temp[m] = pd.to_numeric(temp[m], errors="coerce")
                g = temp.groupby("team_name")[m].sum().to_frame(name="値")
            elif agg == "weighted_sb":
                temp["許盗数"] = pd.to_numeric(temp["許盗数"], errors="coerce")
                temp["被盗企"] = pd.to_numeric(temp["被盗企"], errors="coerce")
                g = temp.groupby("team_name").agg({"許盗数": "sum", "被盗企": "sum"})
                g["値"] = g["許盗数"] / g["被盗企"]
            else:
                temp[m] = pd.to_numeric(temp[m], errors="coerce")
                g = temp.groupby("team_name")[m].mean().to_frame(name="値")

            g = g.dropna()
            is_better_high = m not in ["防御率", "与四球", "与死球", "被安打", "被本率", "BB/9", "四球率", "被打率", "許盗率", "WHIP"]
            if display_mode == "上位3チーム":
                sorted_g = g.sort_values("値", ascending=not is_better_high)
                top_df = sorted_g.head(3)
            else:
                sorted_g = g.sort_values("値", ascending=is_better_high)
                top_df = sorted_g.head(3)

            result_row = {"指標": m}
            for idx, (team, row) in enumerate(top_df.iterrows(), 1):
                result_row[f"{idx}位チーム"] = team
                result_row[f"{idx}位値"] = round(row["値"], 3)
            summary_results.append(result_row)

        except Exception:
            continue

    # チーム名カラー反映用関数
    def color_team_name(team_name):
        color = TEAM_COLORS.get(team_name, "#000000")
        return f'<span style="color:{color}">{team_name}</span>'

    df_summary = pd.DataFrame(summary_results).copy()
    for rank in [1, 2, 3]:
        col = f"{rank}位チーム"
        if col in df_summary.columns:
            df_summary[col] = df_summary[col].apply(lambda x: color_team_name(x) if pd.notna(x) and x != "" else "")

    # HTML表示（unsafe_allow_html=True）
    st.markdown(df_summary.to_html(escape=False, index=False), unsafe_allow_html=True)

with tabs[4]:
    if mode == "野手":
        st.info("野手モードは現在未実装です。")
        st.stop()
    st.write("### 詳細解析：指標の分布図")

    x_metric = st.selectbox("横軸（例：勝率など）", df_filtered.columns.tolist(), index=df_filtered.columns.get_loc("勝率") if "勝率" in df_filtered.columns else 0)
    y_metric = st.selectbox("縦軸（例：QS率など）", df_filtered.columns.tolist(), index=df_filtered.columns.get_loc("QS率") if "QS率" in df_filtered.columns else 1)

    min_ip_detail = st.slider("最低投球回（詳細解析用）", 0, 200, 30)

    df_plot = df_filtered.copy()
    df_plot[x_metric] = pd.to_numeric(df_plot[x_metric], errors="coerce")
    df_plot[y_metric] = pd.to_numeric(df_plot[y_metric], errors="coerce")
    df_plot["IP_"] = pd.to_numeric(df_plot["IP_"], errors="coerce")

    df_plot = df_plot.dropna(subset=[x_metric, y_metric, "IP_", "選手名", "team_name"])
    df_plot = df_plot[df_plot["IP_"] >= min_ip_detail]

    fig, ax = plt.subplots()
    for team in df_plot["team_name"].unique():
        sub_df = df_plot[df_plot["team_name"] == team]
        ax.scatter(sub_df[x_metric], sub_df[y_metric],
                   label=team,
                   color=TEAM_COLORS.get(team, "#888888"),
                   alpha=0.7)
        for _, row in sub_df.iterrows():
            ax.text(row[x_metric], row[y_metric], row["選手名"], fontsize=7)

    ax.set_xlabel(x_metric)
    ax.set_ylabel(y_metric)
    ax.set_title(f"{selected_year}年 選手分布：{y_metric} vs {x_metric}")
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    st.pyplot(fig)

with tabs[5]:
    if mode == "野手":
        st.info("野手モードは現在未実装です。")
        st.stop()
    st.write("### ブレイク選手（未実装）")

with tabs[6]:
    if mode == "野手":
        st.info("野手モードは現在未実装です。")
        st.stop()
    st.write("### サマリーパネル（選手ごとの年度別成績）")

    available_players = df_filtered["選手名"].dropna().unique().tolist()
    selected_player = st.selectbox("選手を選択", sorted(available_players))

    df_player = df[df["選手名"] == selected_player].copy()
    if df_player.empty:
        st.warning(f"{selected_player} のデータが見つかりませんでした。")
        st.stop()
    # ここから選手基本情報表示
    latest = df_player.sort_values("year", ascending=False).iloc[0]
    def safe_str(value):
        return "不明" if value in [0.0, 0, "0.0", "0", None, "nan", "NaN"] else str(value)

    latest_position = safe_str(latest.get("position"))
    latest_hand = safe_str(latest.get("hand"))
    latest_draft = safe_str(latest.get("draft"))
    latest_birth = safe_str(latest.get("birth"))

    try:
        latest_number = int(float(latest.get("number", 0)))
    except:
        latest_number = "不明"

    try:
        latest_age = int(float(latest.get("age", 0)))
    except:
        latest_age = "不明"

    st.markdown("#### 基本情報")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**背番号**: {latest_number}")
        st.markdown(f"**ポジション**: {latest_position}")
        st.markdown(f"**投打**: {latest_hand}")
    with col2:
        st.markdown(f"**ドラフト**: {latest_draft}")
        st.markdown(f"**生年月日**: {latest_birth}")
        st.markdown(f"**年齢**: {latest_age}")
    # 年度別成績表示
    df_player["year"] = pd.to_numeric(df_player["year"], errors="coerce")
    df_player = df_player.sort_values("year")

    st.write(f"#### 年度別成績一覧（{selected_player}）")
    drop_cols = [col for col in ["group_file"] if col in df_player.columns]
    st.dataframe(df_player.drop(columns=drop_cols))


with tabs[7]:
    if mode == "野手":
        st.info("野手モードは現在未実装です。")
        st.stop()

    st.write("### 🧱 投手年齢分布（左投/右投）")

    # 年とチーム選択を個別に指定
    unique_teams = sorted(df["team_name"].dropna().unique())
    team_selected = st.selectbox("チームを選択", unique_teams, key="team_selected_pitcher_only")
    df_pos = df[(df["year"] == selected_year) & (df["team_name"] == team_selected)].copy()

    # 投手だけに絞る
    df_pos["age"] = pd.to_numeric(df_pos["age"], errors="coerce")
    df_pos = df_pos.dropna(subset=["position", "age", "hand"])
    df_pos = df_pos[df_pos["position"].astype(str).str.contains("投")]
    df_pos["age"] = df_pos["age"].astype(int).clip(lower=18, upper=43)


    def classify_throwing_hand(hand_str):
        if isinstance(hand_str, str):
            hand_str = hand_str.strip().replace(" ", "").replace("　", "")  # 半角・全角スペース除去
            if "左投" in hand_str:
                return "左投"
            elif "右投" in hand_str:
                return "右投"
        return "不明"

    df_pos["投手種別"] = df_pos["hand"].apply(classify_throwing_hand)
    df_pos = df_pos[df_pos["投手種別"].isin(["左投", "右投"])]

    # 年齢ごとの人数をカウント
    age_hand_counts = df_pos.groupby(["age", "投手種別"]).size().unstack(fill_value=0).sort_index()
    # 年齢範囲を埋める
    full_age_range = range(df_pos["age"].min(), df_pos["age"].max() + 1)
    age_hand_counts = age_hand_counts.reindex(full_age_range, fill_value=0)

    # グラフ描画とテーブルを横並びに表示
    fig, ax = plt.subplots(figsize=(6, 5))
    age_hand_counts.plot(kind="bar", stacked=True, ax=ax, color={"左投": "#42a5f5", "右投": "#ef5350"})
    ax.set_ylabel("人数")
    ax.set_xlabel("年齢")
    ax.set_title(f"{selected_year}年 {team_selected} 投手年齢分布（左投/右投）")
    fig.tight_layout()

    df_display = df_pos[["age", "選手名", "投手種別"]].copy()
    def color_name(row):
        color = "#42a5f5" if row["投手種別"] == "左投" else "#ef5350"
        return f'<span style="color:{color}">{row["選手名"]}</span>'

    df_display["選手名"] = df_display.apply(color_name, axis=1)
    # group by age, join player names with 、 and smaller font
    df_display_grouped = df_display.groupby("age")["選手名"].apply(lambda x: "、".join(x)).reset_index()
    df_display_grouped = df_display_grouped.sort_values("age")

    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.markdown("<br>", unsafe_allow_html=True)  # さらにスペースを追加
        st.pyplot(fig)
        # 左右投手人数・割合をテキストで表示
        hand_counts_total = df_pos["投手種別"].value_counts().reindex(["左投", "右投"]).fillna(0)
        left_count = int(hand_counts_total.get("左投", 0))
        right_count = int(hand_counts_total.get("右投", 0))
        total = left_count + right_count
        if total > 0:
            left_pct = round(left_count / total * 100, 1)
            right_pct = round(right_count / total * 100, 1)
            st.markdown(f"**左投手**: {left_count}人（{left_pct}%）  /  **右投手**: {right_count}人（{right_pct}%）")
        else:
            st.markdown("**左投手/右投手の情報がありません。**")
    with col2:
        styled_html = (
            "<div style='font-size: 12px;'>"
            + df_display_grouped.to_html(escape=False, index=False)
            + "</div>"
        )
        st.markdown(styled_html, unsafe_allow_html=True)
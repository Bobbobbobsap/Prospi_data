import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib as mpl
import os
from scipy.stats import zscore  # クラスタタイプ分類で使用

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
    conn = sqlite3.connect("player_stats.db")
    df = pd.read_sql_query("SELECT * FROM pitching_stats", conn)
    conn.close()
    return df

# 野手データ読み込み
def load_batter_data():
    conn = sqlite3.connect("player_stats.db")
    df = pd.read_sql_query("SELECT * FROM batting_stats", conn)
    conn.close()
    return df

# 能力データ読み込み
def load_ability_data():
    conn = sqlite3.connect("player_stats.db")
    df = pd.read_sql_query("SELECT * FROM ability_stats", conn)
    conn.close()
    return df

df = load_data()
df_batter = pd.DataFrame()

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
    # モード選択: 「投手」「野手」のみ
    mode = st.radio("モード選択", ["投手", "野手"])
    st.markdown("#### 📦 バージョン: v1.2")

# グローバルフィルター
df_filtered = pd.DataFrame()  # 初期化
df_batter = pd.DataFrame()    # 初期化
if mode == "投手":
    df_filtered = df[(df["year"] == selected_year) & (df["team_name"].isin(selected_teams))]
elif mode == "野手":
    df_batter = load_batter_data()
    for col in ["1", "2", "3", "4", "5"]:
        if col in df_batter.columns:
            df_batter[col] = df_batter[col].astype(str)
    df_batter["year"] = pd.to_numeric(df_batter["year"], errors="coerce")
    df_filtered = df_batter[(df_batter["year"] == selected_year) & (df_batter["team_name"].isin(selected_teams))]

tabs = st.tabs([
    "🏆 項目別ランキング",
    "📈 昨年→今年 比較ランキング",
    "📊 年度別推移",
    "🏟 チーム別比較",
    "📌 詳細解析",
    "🚀 ブレイク選手",
    "📋 サマリーパネル",
    "🧱 選手層（年齢×ポジション）",
    "🧍 ポジション別出場主力",
    "🏆 タイトル・順位",
    "🧠 クラスタ分析（リーグ・チーム別）"
])

# 今後、各タブに処理を追加していく（この構造で分岐・分割）

with tabs[0]:
    if mode == "野手":
        st.write("### 野手ランキング")

        # フィルター設定（最低打席数）
        min_pa = st.slider("最低打席数", 0, 700, 50)

        df_bat_rank = df_filtered.copy()
        df_bat_rank["打席"] = pd.to_numeric(df_bat_rank["打席"], errors="coerce")
        df_bat_rank = df_bat_rank[df_bat_rank["打席"] >= min_pa]

        # 年齢フィルター追加
        min_age, max_age = st.slider("年齢範囲を選択", 18, 45, (18, 45))
        df_bat_rank["age"] = pd.to_numeric(df_bat_rank["age"], errors="coerce")
        df_bat_rank = df_bat_rank[(df_bat_rank["age"] >= min_age) & (df_bat_rank["age"] <= max_age)]

        # ポジションフィルター
        position_options = ["捕", "一", "二", "三", "遊", "左", "中", "右"]
        selected_positions = st.multiselect("ポジションを選択（複数選択可）", position_options, default=position_options)

        def position_filter(pos):
            if isinstance(pos, str):
                return any(p in pos for p in selected_positions)
            return False

        df_bat_rank = df_bat_rank[df_bat_rank["position"].apply(position_filter)]

        bat_metrics = ["打率", "出塁率", "長打率", "OPS", "本塁打", "打点", "得点", "四球", "三振", "盗塁"]
        bat_metric = st.selectbox("ランキング指標を選択", bat_metrics, index=3)
        ascending = st.radio("並べ替え順", ["昇順", "降順"], index=1) == "昇順"
        top_n = st.slider("表示件数", 1, 30, 10)

        df_bat_rank[bat_metric] = pd.to_numeric(df_bat_rank[bat_metric], errors="coerce")
        df_bat_rank = df_bat_rank.dropna(subset=[bat_metric])
        df_bat_rank = df_bat_rank.sort_values(bat_metric, ascending=ascending).head(top_n)

        st.dataframe(df_bat_rank[["選手名", "team_name", "year", bat_metric]])

        fig, ax = plt.subplots(figsize=(8, 4))
        bars = ax.barh(df_bat_rank["選手名"], df_bat_rank[bat_metric], color="#81c784")
        ax.invert_yaxis()
        ax.set_xlabel(bat_metric)
        ax.set_title(f"{selected_year}年 {bat_metric} ランキング")
        st.pyplot(fig)
    elif mode == "投手":
        st.write("### 項目別ランキング")
        
        min_ip = st.slider("最低投球回", 0, 200, 30)
        min_games = st.slider("最低登板数", 0, 50, 10)
        min_starts = st.slider("最低先発数", 0, 30, 0)
        min_reliever = st.slider("最低中継ぎ登板数", 0, 100, 0)
        
        metrics_options = [
            "防御率","投球回","勝率","勝","敗","セーブ","HP",
            "登板", "先発", "完封", "完投", "QS", "QS率", "HQS","HQS率",
            "奪三振", "奪三率", "与四球", "四球率", "与死球", "死球率",
            "被安打", "被打率", "圏打率", "圏率差", "圏安打",
            "右被率", "右率差", "右被安", "左被率", "左率差",
            "被本率", "K/BB", "WHIP", "許盗率", "暴投",
            "K/9", "BB/9", "K-BB%", "Command+"
        ]
        metric = st.selectbox("ランキング指標を選択", metrics_options, index=0)
        ascending = st.radio("並べ替え順", ["昇順", "降順"]) == "昇順"
        top_n = st.slider("表示件数", 1, 30, 10)

        # 指標数値変換
        df_rank = df_filtered.copy()
        for col in [metric, "IP_", "登板", "先発"]:
            if isinstance(col, str) and col in df_rank.columns:
                df_rank[col] = pd.to_numeric(df_rank[col], errors="coerce")

        # カラム存在チェック
        if metric not in df_rank.columns:
            st.warning(f"選択された指標 '{metric}' はデータに存在しません。")
            st.stop()
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
    else:
        pass

with tabs[1]:
    if mode == "野手":
        st.info("野手モードは現在未実装です。")
    elif mode == "投手":
        pass
    st.write("### 昨年→今年 比較ランキング（未実装）")

with tabs[2]:
    if mode == "野手":
        st.info("野手モードは現在未実装です。")
    elif mode == "投手":
        pass
    st.write("### 年度別推移（未実装）")

with tabs[3]:
    if mode == "野手":
        st.write("### チーム別成績比較（野手）")

        metric = st.selectbox("比較指標を選択", [
            "打率", "出塁率", "長打率", "OPS", "本塁打", "打点", "得点", "盗塁", "四球", "三振", "アダム・ダン率"
        ])
        ascending = st.radio("並び替え", ["昇順", "降順"], index=1) == "昇順"

        df_team = df_filtered.copy()
        df_team[metric] = pd.to_numeric(df_team[metric], errors="coerce")
        df_team["打席"] = pd.to_numeric(df_team["打席"], errors="coerce")

        # Define weighted average metrics and their weighting columns
        BATTING_WEIGHTED_METRICS = {
            "打率": "打数",
            "出塁率": "打数",
            "長打率": "打数",
            "OPS": "打数",
            "盗塁率": "盗塁企画",  # assuming exists; otherwise remove
            "三振率": "打席",
            "アダム・ダン率": "打席",
        }

        # Calculate derived columns if needed
        if metric == "アダム・ダン率":
            df_team["四球"] = pd.to_numeric(df_team["四球"], errors="coerce")
            df_team["三振"] = pd.to_numeric(df_team["三振"], errors="coerce")
            df_team["本塁打"] = pd.to_numeric(df_team["本塁打"], errors="coerce")
            df_team["アダム・ダン率"] = (df_team["四球"] + df_team["三振"] + df_team["本塁打"]) / df_team["打席"]
        if metric == "OPS":
            # OPS = 出塁率 + 長打率
            df_team["出塁率"] = pd.to_numeric(df_team["出塁率"], errors="coerce")
            df_team["長打率"] = pd.to_numeric(df_team["長打率"], errors="coerce")
            df_team["OPS"] = df_team["出塁率"] + df_team["長打率"]
        if metric == "打率":
            df_team["安打"] = pd.to_numeric(df_team.get("安打", None), errors="coerce")
            df_team["打数"] = pd.to_numeric(df_team.get("打数", None), errors="coerce")
            df_team["打率"] = df_team["安打"] / df_team["打数"]
        if metric == "盗塁率":
            if "盗塁企画" in df_team.columns and "盗塁" in df_team.columns:
                df_team["盗塁"] = pd.to_numeric(df_team["盗塁"], errors="coerce")
                df_team["盗塁企画"] = pd.to_numeric(df_team["盗塁企画"], errors="coerce")
                df_team["盗塁率"] = df_team["盗塁"] / df_team["盗塁企画"]
        if metric == "三振率":
            # 三振率 = 三振 / 打席
            df_team["三振"] = pd.to_numeric(df_team["三振"], errors="coerce")
            df_team["三振率"] = df_team["三振"] / df_team["打席"]

        # Use weighted average if applicable
        if metric in BATTING_WEIGHTED_METRICS:
            weight_col = BATTING_WEIGHTED_METRICS[metric]
            if weight_col in df_team.columns:
                df_team[weight_col] = pd.to_numeric(df_team[weight_col], errors="coerce")
                df_team[metric] = pd.to_numeric(df_team[metric], errors="coerce")
                df_team = df_team.dropna(subset=[metric, weight_col])
                df_team["weighted_value"] = df_team[metric] * df_team[weight_col]
                df_grouped = df_team.groupby("team_name").agg({
                    "weighted_value": "sum",
                    weight_col: "sum"
                })
                df_grouped[metric] = df_grouped["weighted_value"] / df_grouped[weight_col]
                df_grouped = df_grouped[metric].dropna().sort_values(ascending=ascending)
            else:
                # fallback to mean if weight column not present
                df_grouped = df_team.groupby("team_name")[metric].mean().dropna().sort_values(ascending=ascending)
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

        # --- 上位/下位チーム一覧 追加 ---
        st.markdown("### 各指標で上位/下位チーム一覧")

        display_mode = st.radio("表示モード", ["上位3チーム", "ワースト3チーム"], key="batting_summary_display")

        summary_results = []
        bat_metrics_list = [
            "打率", "出塁率", "長打率", "OPS", "本塁打", "打点", "得点", "盗塁", "四球", "三振", "アダム・ダン率"
        ]
        for m in bat_metrics_list:
            try:
                temp = df_filtered.copy()
                temp["打席"] = pd.to_numeric(temp["打席"], errors="coerce")
                temp["打数"] = pd.to_numeric(temp["打数"], errors="coerce")

                if m == "アダム・ダン率":
                    temp["四球"] = pd.to_numeric(temp["四球"], errors="coerce")
                    temp["三振"] = pd.to_numeric(temp["三振"], errors="coerce")
                    temp["本塁打"] = pd.to_numeric(temp["本塁打"], errors="coerce")
                    temp[m] = (temp["四球"] + temp["三振"] + temp["本塁打"]) / temp["打席"]
                    weight_col = "打席"
                elif m == "OPS":
                    temp["出塁率"] = pd.to_numeric(temp["出塁率"], errors="coerce")
                    temp["長打率"] = pd.to_numeric(temp["長打率"], errors="coerce")
                    temp[m] = temp["出塁率"] + temp["長打率"]
                    weight_col = "打数"
                elif m == "打率":
                    temp["安打"] = pd.to_numeric(temp["安打"], errors="coerce")
                    temp[m] = temp["安打"] / temp["打数"]
                    weight_col = "打数"
                elif m == "盗塁率":
                    temp["盗塁"] = pd.to_numeric(temp["盗塁"], errors="coerce")
                    temp["盗塁企画"] = pd.to_numeric(temp.get("盗塁企画", 0), errors="coerce")
                    temp[m] = temp["盗塁"] / temp["盗塁企画"]
                    weight_col = "盗塁企画"
                elif m == "三振率":
                    temp["三振"] = pd.to_numeric(temp["三振"], errors="coerce")
                    temp[m] = temp["三振"] / temp["打席"]
                    weight_col = "打席"
                else:
                    temp[m] = pd.to_numeric(temp[m], errors="coerce")
                    weight_col = "打数"

                temp = temp.dropna(subset=[m, weight_col])
                temp["weighted_value"] = temp[m] * temp[weight_col]
                g = temp.groupby("team_name").agg({"weighted_value": "sum", weight_col: "sum"})
                g["値"] = g["weighted_value"] / g[weight_col]
                g = g.dropna()

                is_better_high = m not in ["三振", "三振率"]
                sorted_g = g.sort_values("値", ascending=not is_better_high) if display_mode == "上位3チーム" else g.sort_values("値", ascending=is_better_high)
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

        st.markdown(df_summary.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        # 投手モードの処理（既存のコードをそのまま保持）
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
        st.write("### 詳細解析：指標の分布図")

        x_metric = st.selectbox("横軸（例：OPSなど）", df_filtered.columns.tolist(), index=0, key="bat_x_metric")
        y_metric = st.selectbox("縦軸（例：本塁打など）", df_filtered.columns.tolist(), index=1, key="bat_y_metric")

        # 追加: 最低打席数スライダー
        min_pa_detail = st.slider("最低打席数", 0, 700, 50, key="min_pa_detail")

        df_plot = df_filtered.copy()
        df_plot["打席"] = pd.to_numeric(df_plot["打席"], errors="coerce")
        df_plot = df_plot[df_plot["打席"] >= min_pa_detail]

        df_plot[x_metric] = pd.to_numeric(df_plot[x_metric], errors="coerce")
        df_plot[y_metric] = pd.to_numeric(df_plot[y_metric], errors="coerce")
        df_plot = df_plot.dropna(subset=[x_metric, y_metric, "選手名", "team_name"])

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
        if df_plot["team_name"].nunique() > 0:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        st.pyplot(fig)
    else: 
        st.write("### 詳細解析：指標の分布図")

        x_metric = st.selectbox("横軸（例：勝率など）", df_filtered.columns.tolist(), index=df_filtered.columns.get_loc("勝率") if "勝率" in df_filtered.columns else 0)
        y_metric = st.selectbox("縦軸（例：QS率など）", df_filtered.columns.tolist(), index=df_filtered.columns.get_loc("QS率") if "QS率" in df_filtered.columns else 1)

        # 追加: 詳細解析用のフィルタ
        min_ip = st.slider("最低投球回", 0, 200, 30, key="ip_detail")
        min_games = st.slider("最低登板数", 0, 50, 10, key="games_detail")
        min_starts = st.slider("最低先発数", 0, 30, 0, key="starts_detail")
        min_reliever = st.slider("最低中継ぎ登板数", 0, 100, 0, key="reliever_detail")

        df_plot = df_filtered.copy()
        df_plot[x_metric] = pd.to_numeric(df_plot[x_metric], errors="coerce")
        df_plot[y_metric] = pd.to_numeric(df_plot[y_metric], errors="coerce")
        df_plot["IP_"] = pd.to_numeric(df_plot["IP_"], errors="coerce")

        df_plot = df_plot.dropna(subset=[x_metric, y_metric, "IP_", "選手名", "team_name"])

        # 追加: 項目別ランキングと同様のフィルタ
        df_plot["登板"] = pd.to_numeric(df_plot["登板"], errors="coerce")
        df_plot["先発"] = pd.to_numeric(df_plot["先発"], errors="coerce")
        df_plot["中継ぎ"] = (df_plot["登板"] - df_plot["先発"]).abs()

        df_plot = df_plot[
            (df_plot["IP_"] >= min_ip) &
            (df_plot["登板"] >= min_games) &
            (df_plot["先発"] >= min_starts) &
            (df_plot["中継ぎ"] >= min_reliever)
        ]

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
        st.write("### ブレイク選手（未実装）")
    elif mode == "投手":
        pass


with tabs[6]:
    # サマリーパネル: データが空の場合のガード
    if df_filtered.empty:
        st.warning("データが存在しません。")
        
    if mode == "野手":
        st.write("### サマリーパネル（選手ごとの年度別成績）")

        available_players = df_filtered["選手名"].dropna().unique().tolist()
        selected_player = st.selectbox("選手を選択", sorted(available_players), key="summary_batter")

        # 画像表示処理を追加
        import os
        from PIL import Image

        image_path = None
        image_dir = f"image/{selected_year}"

        # データ取得: df_batterを使う
        try:
            df_player = df_batter[
                (df_batter["選手名"] == selected_player) &
                (df_batter["team_name"].isin(selected_teams))
            ].copy()
        except Exception:
            st.warning(f"{selected_player} のデータ取得でエラーが発生しました。")
            st.stop()

        # チーム名も表示するヒント
        st.markdown(f"**選手名**: {selected_player}（チーム候補: {', '.join(df_player['team_name'].unique())}）")

        # 画像ファイル名取得
        filename_candidate = ""
        if not df_player.empty and "filename" in df_player.columns:
            try:
                filename_candidate = df_player.sort_values("year", ascending=False).iloc[0].get("filename", "")
            except Exception:
                filename_candidate = ""
        if isinstance(filename_candidate, str) and filename_candidate and filename_candidate.lower().endswith(".png"):
            candidate_path = os.path.join(image_dir, filename_candidate)
            if os.path.exists(candidate_path):
                image_path = candidate_path
            else:
                st.warning(f"画像ファイルが存在しません: {candidate_path}")
        elif filename_candidate:
            st.warning(f"不正なファイル名: {filename_candidate}")

        if image_path:
            try:
                st.image(image_path, caption=f"{selected_player}の画像", use_container_width=True)
            except Exception as e:
                st.error(f"画像表示に失敗しました: {e}")
        else:
            st.info("画像が見つかりませんでした。")

        if df_player.empty:
            st.warning(f"{selected_player} のデータが見つかりませんでした。")
            st.stop()
        # ここから選手基本情報表示
        latest = df_player.sort_values("year", ascending=False).iloc[0]
        def safe_str(value):
            return "不明" if value in [0.0, 0, "0.0", "0", None, "nan", "NaN"] else str(value)

        # 各カラムの存在チェック
        latest_position = safe_str(latest.get("position")) if "position" in df_player.columns else "不明"
        latest_hand = safe_str(latest.get("hand")) if "hand" in df_player.columns else "不明"
        latest_draft = safe_str(latest.get("draft")) if "draft" in df_player.columns else "不明"
        latest_birth = safe_str(latest.get("birth")) if "birth" in df_player.columns else "不明"

        try:
            latest_number = int(float(latest.get("number", 0))) if "number" in df_player.columns else "不明"
        except:
            latest_number = "不明"

        try:
            latest_age = int(float(latest.get("age", 0))) if "age" in df_player.columns else "不明"
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
        latest_year = df_player["year"].max()
        df_player = df_player[df_player["year"] == latest_year]
        df_player = df_player.sort_values("year")
        # --- BABIPを計算して追加 ---
        try:
            H = pd.to_numeric(df_player["安打"], errors="coerce")
            HR = pd.to_numeric(df_player["本塁打"], errors="coerce")
            AB = pd.to_numeric(df_player["打数"], errors="coerce")
            SO = pd.to_numeric(df_player["三振"], errors="coerce")
            SF = pd.to_numeric(df_player["犠飛"], errors="coerce")
            denominator = AB - SO - HR + SF
            df_player["BABIP"] = ((H - HR) / denominator).round(3)
        except Exception as e:
            df_player["BABIP"] = None

        # レーダーチャートの表示（主要打撃指標）
        st.subheader("📊 レーダーチャートによる成績可視化")

        radar_cols = ["打率", "出塁率", "長打率", "本塁打", "三振率", "盗塁", "OPS"]
        radar_raw = {col: pd.to_numeric(latest.get(col), errors="coerce") for col in radar_cols}
        def normalize_radar_values(raw_dict):
            norm = {}
            norm["打率"] = max(0.0, min(1.0, (raw_dict["打率"] - 0.2) / (0.35 - 0.2)))
            norm["出塁率"] = min(raw_dict["出塁率"] / 0.45, 1.0)
            norm["長打率"] = max(0.0, min(1.0, (raw_dict["長打率"] - 0.2) / (0.65 - 0.2)))
            norm["本塁打"] = min(raw_dict["本塁打"] / 40, 1.0)
            norm["三振率"] = max(0.0, min(1.0, (0.35 - raw_dict["三振率"]) / (0.35 - 0.1)))
            norm["盗塁"] = min(raw_dict["盗塁"] / 30, 1.0)
            norm["OPS"] = max(0.0, min(1.0, (raw_dict["OPS"] - 0.5) / (1.2 - 0.5)))
            return [norm[k] for k in ["打率", "出塁率", "長打率", "本塁打", "三振率", "盗塁", "OPS"]]

        if any(pd.isna(list(radar_raw.values()))):
            st.warning("一部の指標が欠損しているため、レーダーチャートを表示できません。")
        else:
            import matplotlib.pyplot as plt
            import numpy as np

            def plot_radar_chart(labels, values, title="レーダーチャート"):
                num_vars = len(labels)
                angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
                values = values + values[:1]
                angles = angles + angles[:1]

                fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
                ax.plot(angles, values, color="tab:blue", linewidth=2)
                ax.fill(angles, values, color="tab:blue", alpha=0.25)
                ax.set_thetagrids(np.degrees(angles[:-1]), labels)
                ax.set_ylim(0, 1.0) 
                ax.set_title(title)
                ax.grid(True)
                return fig

            scaled = normalize_radar_values(radar_raw)
            fig = plot_radar_chart(radar_cols, scaled, title=f"{selected_player}（{latest_year}）")
            st.pyplot(fig)
        drop_cols = [col for col in ["group_file"] if col in df_player.columns]
        st.write(f"### 昨年の成績一覧")
        base_cols = ["year", "選手名"]

        # --- 打席0のときはNo Data表示 ---
        if latest.get("打席") == 0:
            st.markdown("**No Data**（打席が0のため）")
        else:
            st.subheader("【基本打撃成績】")
            cols1 = ['打率', '試合', '打席', '打数', '安打', '単打', '二塁打', '三塁打', '本塁打', '本打率', '塁打', '長打率', 'OPS']
            st.dataframe(df_player[[c for c in cols1 if c in df_player.columns]])

            st.subheader("【得点圏・満塁成績】")
            cols2 = ['打点', '得点圏打率', '圏率差', '圏打数', '圏安打', '満塁率', '満率差', '満塁数', '満塁安', '得点圏差']
            st.dataframe(df_player[ [c for c in cols2 if c in df_player.columns]])

            st.subheader("【対右・対左の傾向】")
            cols3 = ['対右率', '右率差', '対右数', '対右安', '対左率', '左率差', '対左数', '対左安']
            st.dataframe(df_player[ [c for c in cols3 if c in df_player.columns]])

            st.subheader("【出塁・三振・選球眼】")
            cols4 = ['出塁率', '四球', '死球', '三振', '三振率', 'BB%', 'K%', 'BB/K', 'IsoD', 'アダム・ダン率']
            st.dataframe(df_player[ [c for c in cols4 if c in df_player.columns]])

            st.subheader("【走塁・盗塁】")
            cols5 = ['盗企数', '盗塁', '盗塁率', '盗塁死', '赤星式盗塁']
            st.dataframe(df_player[[c for c in cols5 if c in df_player.columns]])

            st.subheader("【小技・併殺打】")
            cols6 = ['犠打', '犠飛', '併殺打', '併打率']
            st.dataframe(df_player[ [c for c in cols6 if c in df_player.columns]])

            st.subheader("【その他】")
            cols7 = ['連続安', '連試出', '連無安', '猛打賞', 'PA/HR', '得点', '内野安', '内安率', 'IsoP','BABIP']
            st.dataframe(df_player[base_cols + [c for c in cols7 if c in df_player.columns]])

            st.write(f"#### 年度別成績一覧（{selected_player}）")
            drop_cols = [col for col in ["group_file"] if col in df_player.columns]
            if "filename" in df_player.columns:
                drop_cols.append("filename")
            st.dataframe(df_player.drop(columns=drop_cols))
        # st.stop()
    else:
        # 投手モード
        st.write("### サマリーパネル（選手ごとの年度別成績）")

        available_players = df_filtered["選手名"].dropna().unique().tolist()
        selected_player = st.selectbox("選手を選択", sorted(available_players), key="summary_pitcher")

        # 画像表示処理を追加
        import os
        from PIL import Image

        image_path = None
        image_dir = f"image/{selected_year}"
        df_player = df[
            (df["選手名"] == selected_player) &
            (df["team_name"].isin(selected_teams))
        ].copy()

        if not df_player.empty:
            filename_candidate = df_player.sort_values("year", ascending=False).iloc[0].get("filename", "")
            # nanやNoneのときはstr()で"nan"などにならないように
            if isinstance(filename_candidate, str) and filename_candidate and filename_candidate.lower().endswith(".png"):
                candidate_path = os.path.join(image_dir, filename_candidate)
                if os.path.exists(candidate_path):
                    image_path = candidate_path
                else:
                    st.warning(f"画像ファイルが存在しません: {candidate_path}")
            else:
                st.warning(f"不正なファイル名: {filename_candidate}")

        if image_path:
            try:
                st.image(image_path, caption=f"{selected_player}の画像", use_container_width=True)
            except Exception as e:
                st.error(f"画像表示に失敗しました: {e}")
        else:
            st.info("画像が見つかりませんでした。") 

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

        # 投手レーダーチャートの表示
        # 追加: 投球回が0の場合はNo Data表示
        if latest.get("IP_") == 0:
            st.subheader("📊 レーダーチャートによる成績可視化")
            st.markdown("**No Data**（投球回が0のため）")
        else:
            st.subheader("📊 レーダーチャートによる成績可視化")

            import numpy as np
            import matplotlib.pyplot as plt

            radar_cols = ["防御率", "奪三率", "BB/9", "WHIP", "QS", "被打率", "被本率"]
            radar_raw = {col: pd.to_numeric(latest.get(col), errors="coerce") for col in radar_cols}

            def normalize_pitcher_radar(raw):
                norm = {}
                # 防御率: 1.00〜5.00（低いほど良い）
                norm["防御率"] = max(0.0, min(1.0, (5.0 - raw["防御率"]) / (5.0 - 1.0)))
                # 奪三率: 7.0〜11.0（高いほど良い）
                norm["奪三率"] = max(0.0, min(1.0, (raw["奪三率"] - 3.0) / (11.0 - 3.0)))
                # 四球率: 0.1〜0.5（低いほど良い）
                norm["BB/9"] = max(0.0, min(1.0, (9 - raw["BB/9"]) / (9 - 3)))
                # WHIP: 1.0〜2.0（低いほど良い）
                norm["WHIP"] = max(0.0, min(1.0, (2.0 - raw["WHIP"]) / (2.0 - 1.0)))
                # QS: 0〜20（高いほど良い）
                norm["QS"] = min(raw["QS"] / 20.0, 1.0)
                # 被打率: 0.2〜0.35（低いほど良い）
                norm["被打率"] = max(0.0, min(1.0, (0.35 - raw["被打率"]) / (0.35 - 0.2)))
                # 被本率: 0.0〜1.0（低いほど良い）
                norm["被本率"] = max(0.0, min(1.0, (1.0 - raw["被本率"]) / 1.0))
                return [norm[k] for k in ["防御率", "奪三率", "BB/9", "WHIP", "QS", "被打率", "被本率"]]

            if any(pd.isna(list(radar_raw.values()))):
                st.warning("一部の指標が欠損しているため、レーダーチャートを表示できません。")
            else:
                def plot_radar_chart(labels, values, title="レーダーチャート"):
                    num_vars = len(labels)
                    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
                    values = values + values[:1]
                    angles = angles + angles[:1]
                    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
                    ax.plot(angles, values, color="tab:blue", linewidth=2)
                    ax.fill(angles, values, color="tab:blue", alpha=0.25)
                    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
                    ax.set_ylim(0, 1.0)
                    ax.set_title(title)
                    ax.grid(True)
                    return fig
                latest_year = df_player["year"].max()
                scaled = normalize_pitcher_radar(radar_raw)
                fig = plot_radar_chart(radar_cols, scaled, title=f"{selected_player}（{latest_year}）")
                st.pyplot(fig)



        # 年度別成績表示
        latest_year = df_player["year"].max()
        df_player = df_player[df_player["year"] == latest_year]
        df_player = df_player.sort_values("year")
        drop_cols = [col for col in ["group_file"] if col in df_player.columns]
        st.write(f"### 昨年の成績一覧")
        df_player = df_player.drop(columns=drop_cols)

        base_cols = ["year", "選手名"]

        st.subheader("【登板・勝敗・防御率】")
        cols1 = ['投球回', '勝', '敗', '勝率', '先発', '登板', '防御率']
        st.dataframe(df_player[base_cols + [c for c in cols1 if c in df_player.columns]])

        st.subheader("【完封・完投・QS関連】")
        cols2 = ['完封', '完投', 'QS', 'QS率', 'HQS', 'HQS率', '被安打', '被打率', '被本率']
        # st.dataframe(df_player[base_cols + [c for c in cols2 if c in df_player.columns]])
        st.dataframe(df_player[[c for c in cols2 if c in df_player.columns]])
        st.subheader("【与四球・奪三振・WHIP】")
        cols3 = ['与四球', 'BB/9', '奪三振', 'K/9', 'K/BB', 'K-BB%', 'WHIP']
        st.dataframe(df_player[[c for c in cols3 if c in df_player.columns]])

        st.subheader("【得点圏・左右打者の被打率】")
        cols4 = ['圏打率', '圏安打', '圏率差', '右被安', '右被率', '右率差', '左被安', '左被率', '左率差']
        st.dataframe(df_player[ [c for c in cols4 if c in df_player.columns]])

        st.subheader("【死球・盗塁・暴投】")
        cols5 = ['死球率', '暴投', '被盗企', '許盗数', '許盗率']
        st.dataframe(df_player[[c for c in cols5 if c in df_player.columns]])

        st.write(f"##### 年度別成績一覧（{selected_player}）")
        drop_cols = [col for col in ["group_file"] if col in df_player.columns]
        if "filename" in df_player.columns:
            drop_cols.append("filename")
        st.dataframe(df_player.drop(columns=drop_cols))


with tabs[7]:
    # 年とチーム選択を個別に指定（共通化）
    unique_teams = sorted(df["team_name"].dropna().unique())
    team_selected = st.selectbox("チームを選択", unique_teams, key="team_selected_final")

    if mode == "野手":
        st.write("### 打撃方向別人数（右打ち・左打ち）")

        df_pos = df_batter[(df_batter["year"] == selected_year) & (df_batter["team_name"] == team_selected)].copy()
        df_pos = df_pos[df_pos["hand"].notna()]
        df_pos = df_pos[df_pos["hand"].str.contains("打")]

        def classify_batting_direction(hand_str):
            if isinstance(hand_str, str):
                hand_str = hand_str.strip().replace(" ", "").replace("　", "")
                if "右打" in hand_str:
                    return "右打"
                elif "左打" in hand_str:
                    return "左打"
                elif "両打" in hand_str:
                    return "両打"
            return "不明"

        df_pos["打撃方向"] = df_pos["hand"].apply(classify_batting_direction)
        direction_counts = df_pos["打撃方向"].value_counts().sort_index()

        # グラフ表示
        fig, ax = plt.subplots()
        ax.bar(direction_counts.index, direction_counts.values, color=["#ef5350", "#42a5f5", "#9ccc65", "#aaaaaa"])
        ax.set_ylabel("人数")
        ax.set_title(f"{selected_year}年 {team_selected} 打撃方向別人数")
        st.pyplot(fig)
        st.markdown("""
        <div style='font-size:13px;'>
        <span style='display:inline-block;width:15px;height:15px;background-color:#ef5350;border-radius:2px;margin-right:5px'></span>右打　
        <span style='display:inline-block;width:15px;height:15px;background-color:#42a5f5;border-radius:2px;margin-right:5px'></span>左打　
        <span style='display:inline-block;width:15px;height:15px;background-color:#9ccc65;border-radius:2px;margin-right:5px'></span>両打　
        <span style='display:inline-block;width:15px;height:15px;background-color:#aaaaaa;border-radius:2px;margin-right:5px'></span>不明
        </div>
        """, unsafe_allow_html=True)

        # テーブル表示
        st.dataframe(direction_counts.reset_index().rename(columns={"index": "打撃方向", "打撃方向": "人数"}))

        # メインポジションごとの人数表示
        st.write("### メインポジション別人数")

        df_pos["メインポジション"] = df_pos["position"].astype(str).str[0]
        main_position_counts = df_pos["メインポジション"].value_counts().reindex(["捕", "一", "二", "三", "遊", "左", "中", "右"], fill_value=0)

        fig2, ax2 = plt.subplots()
        ax2.bar(main_position_counts.index, main_position_counts.values, color="#90caf9")
        ax2.set_ylabel("人数")
        ax2.set_title(f"{selected_year}年 {team_selected} メインポジション別人数")
        st.pyplot(fig2)

        st.dataframe(main_position_counts.reset_index().rename(columns={"index": "ポジション", "メインポジション": "人数"}))

        # 年齢 × ポジション 表
        st.write("### 年齢 × ポジション 表")

        df_pos["age"] = pd.to_numeric(df_pos["age"], errors="coerce").fillna(0).astype(int)
        df_pos["age_group"] = df_pos["age"].apply(lambda x: str(x) if x <= 34 else "35~")

        def classify_position(pos_str):
            if pd.isna(pos_str):
                return None
            pos = str(pos_str)[0]
            if pos == "投":
                return "投手"
            elif pos == "捕":
                return "捕手"
            elif pos in "一二三遊":
                return "内野手"
            elif pos in "左右中":
                return "外野手"
            return None

        df_pos["pos_class"] = df_pos["position"].apply(classify_position)

        df_grid = df_pos[["選手名", "age_group", "pos_class", "hand"]].dropna(subset=["pos_class"])
        df_grid["cell_html"] = df_grid.apply(
            lambda row: f"<div style='background-color:{'#ef5350' if '右打' in str(row['hand']) else '#42a5f5' if '左打' in str(row['hand']) else '#9ccc65' if '両打' in str(row['hand']) else '#f0f0f0'};padding:2px;border-radius:4px;margin:1px'>{row['選手名']}</div>",
            axis=1
        )

        pivot = df_grid.groupby(["age_group", "pos_class"])["cell_html"].apply(lambda x: "".join(x)).unstack().fillna("")

        # Render as styled HTML
        styled_html = "<style>table {font-size: 13px;} td {vertical-align: top;}</style>"
        styled_html += pivot.to_html(escape=False)
        st.markdown(styled_html, unsafe_allow_html=True)
        # Add color legend
        st.markdown("""
<div style='font-size:13px; margin-top:10px;'>
凡例：
<span style='display:inline-block;width:15px;height:15px;background-color:#ef5350;border-radius:2px;margin-right:5px'></span>右打　
<span style='display:inline-block;width:15px;height:15px;background-color:#42a5f5;border-radius:2px;margin-right:5px'></span>左打　
<span style='display:inline-block;width:15px;height:15px;background-color:#9ccc65;border-radius:2px;margin-right:5px'></span>両打　
<span style='display:inline-block;width:15px;height:15px;background-color:#f0f0f0;border-radius:2px;margin-right:5px'></span>不明
</div>
""", unsafe_allow_html=True)
    elif mode == "投手":
        st.write("### 🧱 投手年齢分布（左投/右投）")

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

        # 投打フル組み合わせ分類を追加
        def classify_throw_bat(hand_str):
            if isinstance(hand_str, str):
                hand_str = hand_str.strip().replace(" ", "").replace("　", "")
                if "右投右打" in hand_str:
                    return "右投右打"
                elif "右投左打" in hand_str:
                    return "右投左打"
                elif "右投両打" in hand_str:
                    return "右投両打"
                elif "左投右打" in hand_str:
                    return "左投右打"
                elif "左投左打" in hand_str:
                    return "左投左打"
                elif "左投両打" in hand_str:
                    return "左投両打"
            return "不明"
        df_pos["投打分類"] = df_pos["hand"].apply(classify_throw_bat)

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

        # --- クラスタリング表示: 投手モードのときのみ ---
        # ここからクラスタリング処理（t-SNEやKMeans等）を投手モードのみに限定して移動
        if mode == "投手":
            # 必要なライブラリのインポート
            from sklearn.manifold import TSNE
            from sklearn.cluster import KMeans
            import numpy as np

            st.write("### 投手クラスタリング（t-SNE + KMeans）")
            # クラスタリングは年齢、投球回、各種指標（防御率、奪三振、与四球、WHIP）に基づいて分類
            cluster_features = [ "防御率", "奪三率", "四球率", "WHIP","被本率", "被打率"]
            df_cluster = df_pos.copy()
            # 登板数が0の選手を除外
            df_cluster["登板"] = pd.to_numeric(df_cluster["登板"], errors="coerce")
            df_cluster = df_cluster[df_cluster["登板"] > 0]
            # 必要なカラムが揃っているか確認
            if all(f in df_cluster.columns for f in cluster_features):
                cluster_data = df_cluster[cluster_features].apply(pd.to_numeric, errors="coerce").dropna()
                if not cluster_data.empty and len(cluster_data) >= 2:
                    # t-SNEのperplexity要件をチェック
                    # if len(cluster_data) < 30:
                    #     st.warning(f"クラスタリングには最低30選手以上のデータが必要です（現在: {len(cluster_data)}）")
                    #     st.stop()
                    # perplexityはサンプル数の1/3または最大30を目安に自動調整（最低5）
                    tsne = TSNE(n_components=2, random_state=0, perplexity=min(30, max(5, len(cluster_data) // 3)))
                    tsne_result = tsne.fit_transform(cluster_data)
                    # KMeansによりt-SNEで圧縮した2次元データにクラスタ分けを実施
                    n_clusters = st.slider("クラスタ数", 2, 6, 3, key="pitcher_cluster_n")
                    kmeans = KMeans(n_clusters=n_clusters, random_state=0)
                    cluster_labels = kmeans.fit_predict(tsne_result)
                    # 結果をdfに反映
                    df_cluster_vis = df_cluster.loc[cluster_data.index].copy()
                    df_cluster_vis["tsne_x"] = tsne_result[:, 0]
                    df_cluster_vis["tsne_y"] = tsne_result[:, 1]
                    df_cluster_vis["cluster"] = cluster_labels
                    # 可視化
                    fig3, ax3 = plt.subplots()
                    colors = plt.get_cmap("tab10", n_clusters)
                    for i in range(n_clusters):
                        d = df_cluster_vis[df_cluster_vis["cluster"] == i]
                        ax3.scatter(d["tsne_x"], d["tsne_y"], label=f"クラスタ{i+1}", color=colors(i), alpha=0.7)
                        for _, row in d.iterrows():
                            ax3.text(row["tsne_x"], row["tsne_y"], row["選手名"], fontsize=7)
                    ax3.set_title("投手クラスタリング（t-SNE + KMeans）")
                    ax3.set_xlabel("t-SNE 1")
                    ax3.set_ylabel("t-SNE 2")
                    ax3.legend()
                    st.pyplot(fig3)
                else:
                    st.info("クラスタリングに十分なデータがありません。")
            else:
                st.info("クラスタリングに必要な指標が不足しています。")

        # 投打別内訳テーブル
        st.markdown("### 投打別内訳")
        throw_bat_summary = df_pos["投打分類"].value_counts().reset_index()
        throw_bat_summary.columns = ["投打", "人数"]
        st.dataframe(throw_bat_summary)


#
# # --- 外野サンプル表示 ---
# st.markdown("### 外野選手のサンプル表示（全チーム）")

# # df_defの読み込み（未定義エラー対策）
# conn_def = sqlite3.connect("defense_stats.db")
# df_def = pd.read_sql_query("SELECT * FROM defense_stats", conn_def)
# conn_def.close()
# df_def["position_group"] = df_def["ポジション"]
# df_def["team_name"] = df_def["チーム"]

# df_outfield_sample = df_def[df_def["position_group"] == "outfielder"].copy()
# df_outfield_sample["出場"] = pd.to_numeric(df_outfield_sample["試合"], errors="coerce")
# df_outfield_sample = df_outfield_sample.dropna(subset=["team_name", "選手名", "出場"])
# df_outfield_sample = df_outfield_sample.sort_values(["team_name", "出場"], ascending=[True, False])

# # 表示カラムに守備情報も含める
# sample_cols = ["team_name", "選手名", "出場"]
# if "失策" in df_outfield_sample.columns:
#     sample_cols.append("失策")
# if "守備率" in df_outfield_sample.columns:
#     sample_cols.append("守備率")

# st.dataframe(df_outfield_sample[sample_cols])

# --- 新規タブ: ポジション別出場主力 ---
with tabs[8]:
    st.write("### 各チーム ポジション別 主力選手（守備+打撃）")

    # --- チーム選択フィルタ追加 ---
    team_options = sorted(df["team_name"].dropna().unique())
    selected_teams_in_tab = [st.selectbox("表示するチームを選択", team_options)]

    # 守備成績の読み込み
    conn_def = sqlite3.connect("player_stats.db")
    df_def = pd.read_sql_query("SELECT * FROM defense_stats", conn_def)
    conn_def.close()
    # 「outfielder」としてすでに統一されているためそのまま使用
    df_def["position_group"] = df_def["ポジション"]

    # バッティング成績の読み込み
    df_bat_all = load_batter_data()
    df_def["team_name"] = df_def["チーム"]

    # === 能力データの読み込み・マージ ===
    df_ability = load_ability_data()
    df_ability["year"] = pd.to_numeric(df_ability["year"], errors="coerce")
    df_ability = df_ability[df_ability["year"] == selected_year]

    ability_cols = [
        "選手名", "team_name", "Left", "Right", "center",
        "first", "second", "short", "third", "catcher"
    ]

    # 各チーム・ポジションで最も出場数が多い選手を抽出
    df_def["出場"] = pd.to_numeric(df_def["試合"], errors="coerce")
    df_def = df_def.dropna(subset=["team_name", "position_group", "選手名", "出場"])
    df_def_ranked = df_def.sort_values("出場", ascending=False)

    # 各チーム・ポジションごとに、出場数が合計110以上になるよう選手を抽出
    top_players_list = []
    non_outfield_df = df_def_ranked[df_def_ranked["position_group"] != "outfielder"]

    for (team, pos), group in non_outfield_df.groupby(["team_name", "position_group"]):
        group_sorted = group.sort_values("出場", ascending=False)
        total = 0
        rows = []
        for _, row in group_sorted.iterrows():
            rows.append(row)
            total += row["出場"]
            if total >= 110:
                break
        top_players_list.extend(rows)

    top_players = pd.DataFrame(top_players_list)

    # 外野は合計330試合以上になるまで選出
    outfield_players_list = []
    outfield_df = df_def_ranked[df_def_ranked["position_group"] == "outfielder"]

    for team, group in outfield_df.groupby("team_name"):
        group_sorted = group.sort_values("出場", ascending=False)
        total = 0
        rows = []
        for _, row in group_sorted.iterrows():
            rows.append(row)
            total += row["出場"]
            if total >= 330:
                break
        outfield_players_list.extend(rows)

    outfield_top = pd.DataFrame(outfield_players_list)
    outfield_top["position_group"] = "外野"
    outfield_top["ポジション"] = "外野"
    # --- フィルタ前のデータを保持（ベストナイン用） ---
    top_players_raw = top_players.copy()
    outfield_top_raw = outfield_top.copy()
    # === フィルタリング追加ここから ===
    # チーム選択フィルタを top_players, outfield_top に適用
    top_players = top_players[top_players["team_name"].isin(selected_teams_in_tab)]
    outfield_top = outfield_top[outfield_top["team_name"].isin(selected_teams_in_tab)]
    # === フィルタリング追加ここまで ===

    # 外野も結合
    # 空・全NAデータフレームを除外し、全NA列も除去して結合
    top_players_full = pd.concat(
        [df.dropna(how="all", axis=1) for df in [top_players, outfield_top] if not df.empty],
        ignore_index=True
    )

    # ポジション名の日本語化（top_players_full 側にも適用）
    top_players_full["ポジション"] = top_players_full["ポジション"].replace({
        "outfielder": "外野",
        "catcher": "捕手",
        "first": "一塁",
        "second": "二塁",
        "third": "三塁",
        "short": "遊撃"
    })

    # 守備情報列を選定（例：失策、守備率、捕手固有指標も含む）
    defense_cols = ["選手名", "チーム", "ポジション", "試合", "失策", "守備率", "捕逸", "被盗塁企画", "許盗塁", "盗塁刺", "盗阻率"]
    df_def_info = df_def[defense_cols].copy()
    df_def_info["team_name"] = df_def_info["チーム"]
    # ポジション名の統一（英語→日本語）
    df_def_info["ポジション"] = df_def_info["ポジション"].replace({
        "outfielder": "外野",
        "catcher": "捕手",
        "first": "一塁",
        "second": "二塁",
        "third": "三塁",
        "short": "遊撃"
    })

    # バッティング情報とマージ
    df_bat_all["year"] = pd.to_numeric(df_bat_all["year"], errors="coerce")
    df_bat_latest = df_bat_all[df_bat_all["year"] == selected_year]

    # 守備情報を追加（top_players_fullにマージ）
    df_combined = pd.merge(
        top_players_full,
        df_def_info,
        on=["選手名", "team_name", "ポジション"],
        how="left",
        suffixes=("", "_def")
    )

    # バッティング情報とマージ
    df_merged = pd.merge(
        df_combined,
        df_bat_latest[["選手名", "team_name", "打率", "本塁打", "打点", "OPS"]],
        on=["選手名", "team_name"],
        how="left"
    )

    # 能力データをマージ
    df_merged = pd.merge(
        df_merged,
        df_ability[ability_cols],
        on=["選手名", "team_name"],
        how="left"
    )

    # Remove defensive columns if present
    cols_to_remove = ["守備スコア", "守備偏差値", "守備範囲能力"]
    df_merged = df_merged.drop(columns=[col for col in cols_to_remove if col in df_merged.columns], errors="ignore")

    # Calculate OPS偏差値 (global z-score, not by position)
    if "OPS" in df_merged.columns:
        df_merged["OPS"] = pd.to_numeric(df_merged["OPS"], errors="coerce")
        ops_mean = df_merged["OPS"].mean()
        ops_std = df_merged["OPS"].std(ddof=0)
        if ops_std != 0:
            df_merged["OPS偏差値"] = ((df_merged["OPS"] - ops_mean) / ops_std * 10 + 50).round(2)
        else:
            df_merged["OPS偏差値"] = 50
    # Prepare display columns (remove defensive info, add OPS偏差値)
    display_cols = [
        "team_name", "ポジション", "選手名", "出場", "打率", "本塁打", "打点", "OPS"
    ]
    # Add OPS偏差値 if not present
    if "OPS偏差値" in df_merged.columns and "OPS偏差値" not in display_cols:
        display_cols.append("OPS偏差値")
    # Add positional ability columns if present
    for col in ["Left", "Right", "center", "first", "second", "short", "third", "catcher"]:
        if col in df_merged.columns and col not in display_cols:
            display_cols.append(col)
    display_cols = [col for col in display_cols if col in df_merged.columns]
    st.dataframe(df_merged[display_cols])

    # --- 🔥 ベストバッティングナイン（OPS順） ---
    st.write("### 🔥 ベストバッティングナイン（OPS順）")
    selected_league_for_best9 = st.radio("リーグを選択", ["セ・リーグ", "パ・リーグ"], horizontal=True)

    # リーグ定義
    SE_TEAMS = ["giants", "hanshin", "dragons", "baystars", "swallows", "carp"]
    PA_TEAMS = ["hawks", "lions", "eagles", "marines", "Buffaloes", "fighters"]

    # 🔥 ベストナイン用に全チーム分のdfを用意（選択チームフィルタなし）
    top_players_all = pd.concat(
        [df.dropna(how="all", axis=1) for df in [top_players_raw, outfield_top_raw] if not df.empty],
        ignore_index=True
    )
    top_players_all["ポジション"] = top_players_all["ポジション"].replace({
        "outfielder": "外野",
        "catcher": "捕手",
        "first": "一塁",
        "second": "二塁",
        "third": "三塁",
        "short": "遊撃"
    })

    # 守備・打撃・能力をマージ
    df_combined_all = pd.merge(
        top_players_all,
        df_def_info,
        on=["選手名", "team_name", "ポジション"],
        how="left"
    )
    df_combined_all = pd.merge(
        df_combined_all,
        df_bat_latest[["選手名", "team_name", "打率", "本塁打", "打点", "OPS"]],
        on=["選手名", "team_name"],
        how="left"
    )
    df_combined_all = pd.merge(
        df_combined_all,
        df_ability[ability_cols],
        on=["選手名", "team_name"],
        how="left"
    )
    # --- 表示用ポジション列を追加 ---
    def split_outfielder_position(row):
        if row["ポジション"] != "外野":
            return row["ポジション"]
        vals = {
            "左": pd.to_numeric(row.get("Left", 0), errors="coerce") or 0,
            "中": pd.to_numeric(row.get("center", 0), errors="coerce") or 0,
            "右": pd.to_numeric(row.get("Right", 0), errors="coerce") or 0
        }
        best_pos = max(vals, key=vals.get)
        # 1文字→フル日本語表記
        return {"左": "左", "中": "中", "右": "右"}[best_pos]
    df_combined_all["表示用ポジション"] = df_combined_all.apply(split_outfielder_position, axis=1)

    # OPS偏差値計算（全体ベース）
    if "OPS" in df_combined_all.columns:
        df_combined_all["OPS"] = pd.to_numeric(df_combined_all["OPS"], errors="coerce")
        ops_mean = df_combined_all["OPS"].mean()
        ops_std = df_combined_all["OPS"].std(ddof=0)
        df_combined_all["OPS偏差値"] = ((df_combined_all["OPS"] - ops_mean) / ops_std * 10 + 50).round(2)

    # ベストナイン抽出は df_combined_all から行う
    df_best_source = df_combined_all[df_combined_all["team_name"].isin(SE_TEAMS if selected_league_for_best9 == "セ・リーグ" else PA_TEAMS)]

    def get_best_nine(df):
        # ポジション列名を"ポジション"に統一
        df = df.dropna(subset=["OPS", "ポジション"])
        best_nine = []
        positions = ["捕手", "一塁", "二塁", "三塁", "遊撃", "左", "中", "右"]
        for pos in positions:
            df_pos = df[df["表示用ポジション"] == pos]
            if not df_pos.empty:
                best = df_pos.sort_values("OPS", ascending=False).iloc[0]
                best_nine.append(best)
        return pd.DataFrame(best_nine)

    df_best = get_best_nine(df_best_source)
    # 表示用: ポジション列名を"position"でなく"ポジション"に
    display_best_cols = ["ポジション", "選手名", "team_name", "OPS"]
    df_best_display = df_best[display_best_cols] if all(c in df_best.columns for c in display_best_cols) else df_best
    st.dataframe(df_best_display)


# --- 新規タブ: タイトル・順位 ---
with tabs[9]:
    st.write("### 🏆 各リーグタイトル & 順位表")

    # df_batterをここで再読み込み（必要な列が存在しないことへの対処）
    df_batter = load_batter_data()

    league = st.radio("リーグを選択", ["セ・リーグ", "パ・リーグ"], horizontal=True, key="league_rank_tab")

    SE_TEAMS = ["giants", "hanshin", "dragons", "baystars", "swallows", "carp"]
    PA_TEAMS = ["hawks", "lions", "eagles", "marines", "Buffaloes", "fighters"]

    league_teams = SE_TEAMS if league == "セ・リーグ" else PA_TEAMS

    # チーム名列の確認と補正
    if "チーム" in df_batter.columns and "team_name" not in df_batter.columns:
        df_batter = df_batter.rename(columns={"チーム": "team_name"})
    # debug print
    # print("=== df_batter columns ===")
    # print(df_batter.columns.tolist())

    # Ensure 'year' column exists and is numeric
    df_batter["year"] = pd.to_numeric(df_batter.get("year", pd.NA), errors="coerce")
    # チーム別打撃指標（OPSなど）
    df_bat_league = df_batter[(df_batter["year"] == selected_year) & (df_batter["team_name"].isin(league_teams))].copy()
    df_bat_league["OPS"] = pd.to_numeric(df_bat_league["OPS"], errors="coerce")
    df_bat_league["打数"] = pd.to_numeric(df_bat_league["打数"], errors="coerce")
    df_bat_league = df_bat_league.dropna(subset=["OPS", "打数"])
    df_bat_league["weighted_OPS"] = df_bat_league["OPS"] * df_bat_league["打数"]
    df_bat_team = df_bat_league.groupby("team_name").agg({
        "weighted_OPS": "sum",
        "打数": "sum"
    }).reset_index()
    df_bat_team["OPS（加重平均）"] = df_bat_team["weighted_OPS"] / df_bat_team["打数"]
    df_bat_team = df_bat_team[["team_name", "OPS（加重平均）"]].sort_values("OPS（加重平均）", ascending=False)
    df_bat_team.columns = ["チーム", "OPS（加重平均）"]

    # チーム別投手勝ち星
    df_pitch_league = df[(df["year"] == selected_year) & (df["team_name"].isin(league_teams))].copy()
    df_pitch_league["勝"] = pd.to_numeric(df_pitch_league["勝"], errors="coerce")
    df_win_team = df_pitch_league.groupby("team_name")["勝"].sum().dropna().sort_values(ascending=False).reset_index()
    df_win_team.columns = ["チーム", "勝利数"]
    # --- 敗北数・引き分け数追加 ---
    df_pitch_league["敗"] = pd.to_numeric(df_pitch_league["敗"], errors="coerce")
    df_lose_team = df_pitch_league.groupby("team_name")["敗"].sum().dropna().reset_index()
    df_lose_team.columns = ["チーム", "敗北数"]
    df_win_team = pd.merge(df_win_team, df_lose_team, on="チーム", how="left")
    df_win_team["引き分け"] = 143 - df_win_team["勝利数"] - df_win_team["敗北数"]
    # 表示カラム整理
    df_win_team = df_win_team[["チーム", "勝利数", "敗北数", "引き分け"]]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 打撃成績：OPS（加重平均）")
        st.dataframe(df_bat_team)

    with col2:
        st.markdown("#### 🥇順位表（チーム勝利数ベース）")
        st.dataframe(df_win_team)



# --- 新規タブ: 🧠 クラスタ分析（リーグ・チーム別） ---
with tabs[10]:
    st.write("### 🧠 クラスタ分析（リーグ・チーム別）")

    # 投手・野手で分岐
    if mode == "投手":
        league_tabs = st.tabs(["⚾ 全体（12球団）", "🔵 セ・リーグ", "🟡 パ・リーグ"])
        TEAM_SE = ["giants", "hanshin", "dragons", "baystars", "swallows", "carp"]
        TEAM_PA = ["hawks", "lions", "eagles", "marines", "Buffaloes", "fighters"]

        for idx, (tab, league_name, team_filter) in enumerate(zip(
            league_tabs,
            ["全体", "セ・リーグ", "パ・リーグ"],
            [None, TEAM_SE, TEAM_PA]
        )):
            with tab:
                st.write(f"#### {league_name} クラスタリング結果")

                # チームフィルタ適用
                df_cluster = df.copy()
                if team_filter:
                    df_cluster = df_cluster[df_cluster["team_name"].isin(team_filter)]

                # 前処理
                cluster_features = ["防御率", "奪三率", "四球率", "WHIP", "被本率", "被打率"]
                df_cluster["登板"] = pd.to_numeric(df_cluster["登板"], errors="coerce")
                df_cluster = df_cluster[df_cluster["登板"] > 0]
                cluster_data = df_cluster[cluster_features].apply(pd.to_numeric, errors="coerce").dropna()

                if cluster_data.shape[0] < 2:
                    st.warning("クラスタリングに必要なデータが不足しています。")
                    continue

                from sklearn.manifold import TSNE
                from sklearn.cluster import KMeans
                import matplotlib.pyplot as plt
                import numpy as np

                perplexity = min(30, max(5, len(cluster_data) // 3))
                tsne = TSNE(n_components=2, random_state=0, perplexity=perplexity)
                tsne_result = tsne.fit_transform(cluster_data)

                n_clusters = st.slider(f"{league_name}のクラスタ数", 2, 6, 3, key=f"tsne_n_clusters_{idx}")
                kmeans = KMeans(n_clusters=n_clusters, random_state=0)
                cluster_labels = kmeans.fit_predict(tsne_result)

                df_vis = df_cluster.loc[cluster_data.index].copy()
                df_vis["tsne_x"] = tsne_result[:, 0]
                df_vis["tsne_y"] = tsne_result[:, 1]
                df_vis["cluster"] = cluster_labels

                # 可視化
                fig, ax = plt.subplots()
                cmap = plt.get_cmap("tab10", n_clusters)
                for i in range(n_clusters):
                    d = df_vis[df_vis["cluster"] == i]
                    ax.scatter(d["tsne_x"], d["tsne_y"], label=f"クラスタ{i+1}", color=cmap(i), alpha=0.7)
                    for _, row in d.iterrows():
                        ax.text(row["tsne_x"], row["tsne_y"], row["選手名"], fontsize=7)
                ax.set_title(f"{league_name} クラスタリング（t-SNE + KMeans）")
                ax.legend()
                st.pyplot(fig)

                # クラスタ中心点の特徴表示
                st.markdown("#### 📊 各クラスタの平均成績（中心点特徴）")
                # 重複列を防ぐために df_vis 側の重複列を削除して結合
                df_vis_clean = df_vis.drop(columns=[col for col in cluster_data.columns if col in df_vis.columns], errors="ignore")
                df_vis_with_features = pd.concat([df_vis_clean.reset_index(drop=True), cluster_data.reset_index(drop=True)], axis=1)
                cluster_centers = df_vis_with_features.groupby("cluster")[cluster_features].mean().round(2)
                cluster_centers.index = [f"クラスタ{i+1}" for i in cluster_centers.index]
                st.dataframe(cluster_centers)

                # クラスタタイプ名称分類関数（z-score基準）
                def classify_cluster_type(row, z_df):
                    try:
                        z_row = z_df.loc[row.name]
                        if z_row["奪三率"] > 0.5 and z_row["四球率"] > 0.2:
                            return "パワー型"
                        elif z_row["四球率"] < -0.5 and z_row["奪三率"] > 0.5:
                            return "エース型"
                        elif z_row["WHIP"] < -0.5 and z_row["四球率"] < -0.3:
                            return "技巧型"
                        elif z_row["被打率"] > 0.5:
                            return "飛翔型"
                        elif z_row["防御率"] > 0.7:
                            return "2軍レベル"
                        else:
                            return "バランス型"
                    except:
                        return "未分類"

                # z-score計算
                cluster_centers_z = cluster_centers.apply(zscore)

                # クラスタタイプ名称分類
                cluster_type_names = [
                    classify_cluster_type(row, cluster_centers_z)
                    for _, row in cluster_centers.iterrows()
                ]

                st.markdown("#### 🧩 クラスタタイプ（仮称）")
                for i, style in zip(cluster_centers.index, cluster_type_names):
                    st.write(f"{i}: {style}")

                # チーム別クラスタ構成比
                st.markdown("#### 📈 チーム別クラスタ構成比")
                cluster_counts = df_vis.groupby(["team_name", "cluster"]).size().unstack(fill_value=0)
                cluster_counts_ratio = cluster_counts.div(cluster_counts.sum(axis=1), axis=0)

                fig2, ax2 = plt.subplots(figsize=(10, 4))
                cluster_counts_ratio.plot(kind="bar", stacked=True, ax=ax2, colormap="tab10")
                ax2.set_ylabel("割合")
                ax2.set_title(f"{league_name} チーム別クラスタ構成比")
                ax2.legend(title="クラスタ")
                st.pyplot(fig2)

    elif mode == "野手":
        # 野手クラスタリング
        st.write("#### 野手クラスタリング（t-SNE + KMeans）")
        league_tabs = st.tabs(["⚾ 全体（12球団）", "🔵 セ・リーグ", "🟡 パ・リーグ"])
        TEAM_SE = ["giants", "hanshin", "dragons", "baystars", "swallows", "carp"]
        TEAM_PA = ["hawks", "lions", "eagles", "marines", "Buffaloes", "fighters"]

        for idx, (tab, league_name, team_filter) in enumerate(zip(
            league_tabs,
            ["全体", "セ・リーグ", "パ・リーグ"],
            [None, TEAM_SE, TEAM_PA]
        )):
            with tab:
                st.write(f"#### {league_name} クラスタリング結果")

                # データロード
                df_bat = load_batter_data()
                df_bat["year"] = pd.to_numeric(df_bat["year"], errors="coerce")
                df_bat["打席"] = pd.to_numeric(df_bat["打席"], errors="coerce")
                # チームフィルタ適用
                if team_filter:
                    df_bat = df_bat[df_bat["team_name"].isin(team_filter)]
                # 年度フィルタ（最新年度のみ）
                df_bat = df_bat[df_bat["year"] == selected_year]
                # 打席100以上でフィルタ
                df_bat = df_bat[df_bat["打席"] >= 100]
                cluster_features = ["打率", "出塁率", "長打率", "本塁打", "三振"]
                # 必要なカラムを数値に
                for col in cluster_features:
                    df_bat[col] = pd.to_numeric(df_bat[col], errors="coerce")
                cluster_data = df_bat[cluster_features].dropna()
                if cluster_data.shape[0] < 2:
                    st.warning("クラスタリングに必要なデータが不足しています。")
                    continue
                from sklearn.manifold import TSNE
                from sklearn.cluster import KMeans
                import matplotlib.pyplot as plt
                import numpy as np

                perplexity = min(30, max(5, len(cluster_data) // 3))
                tsne = TSNE(n_components=2, random_state=0, perplexity=perplexity)
                tsne_result = tsne.fit_transform(cluster_data)

                n_clusters = st.slider(f"{league_name}のクラスタ数", 2, 6, 3, key=f"tsne_n_clusters_bat_{idx}")
                kmeans = KMeans(n_clusters=n_clusters, random_state=0)
                cluster_labels = kmeans.fit_predict(tsne_result)

                df_vis = df_bat.loc[cluster_data.index].copy()
                df_vis["tsne_x"] = tsne_result[:, 0]
                df_vis["tsne_y"] = tsne_result[:, 1]
                df_vis["cluster"] = cluster_labels

                # 可視化
                fig, ax = plt.subplots()
                cmap = plt.get_cmap("tab10", n_clusters)
                for i in range(n_clusters):
                    d = df_vis[df_vis["cluster"] == i]
                    ax.scatter(d["tsne_x"], d["tsne_y"], label=f"クラスタ{i+1}", color=cmap(i), alpha=0.7)
                    for _, row in d.iterrows():
                        ax.text(row["tsne_x"], row["tsne_y"], row["選手名"], fontsize=7)
                ax.set_title(f"{league_name} クラスタリング（t-SNE + KMeans）")
                ax.legend()
                st.pyplot(fig)

                # クラスタ中心点の特徴表示
                st.markdown("#### 📊 各クラスタの平均成績（中心点特徴）")
                # 重複列を防ぐために df_vis 側の重複列を削除して結合
                df_vis_clean = df_vis.drop(columns=[col for col in cluster_data.columns if col in df_vis.columns], errors="ignore")
                df_vis_with_features = pd.concat([df_vis_clean.reset_index(drop=True), cluster_data.reset_index(drop=True)], axis=1)
                cluster_centers = df_vis_with_features.groupby("cluster")[cluster_features].mean().round(2)
                cluster_centers.index = [f"クラスタ{i+1}" for i in cluster_centers.index]
                st.dataframe(cluster_centers)

                # クラスタタイプ名称分類関数（z-score基準, 指定ロジック）
                def classify_batter_type_all(cluster_centers_z):
                    # cluster_centers_z: DataFrame, index=f"クラスタ1" etc, rows=clusters, columns=features
                    cluster_names = [None] * len(cluster_centers_z)
                    used_types = set()

                    def get_type_name(center_z, used_types):
                        # center_z is a Series
                        obp = center_z.get("出塁率", 0)
                        avg = center_z.get("打率", 0)
                        slg = center_z.get("長打率", 0)
                        hr = center_z.get("本塁打", 0)
                        so = center_z.get("三振", 0)


                        if slg > 0.8 and obp > 0.8:
                            return "最強型"
                        elif  obp > 0.8:
                            return "1番型"
                        elif avg > 0.6 and obp < 0.6:
                            return "アヘ単型"
                        elif hr > 0.5 and so > 0.5:
                            return "ウホウホ本塁打型"
                        elif so >0.2:
                            return "三振マシン"
                        return "バランス型"

                    # 1周目: 最強型と1番型だけ使う
                    for i, (_, center_z) in enumerate(cluster_centers_z.iterrows()):
                        name = get_type_name(center_z, used_types)
                        if name in {"最強型", "1番型"} and name not in used_types:
                            cluster_names[i] = name
                            used_types.add(name)

                    # 2周目: アヘ単型、ウホウホ長打型を 1クラスタに限定して使う
                    for i, (_, center_z) in enumerate(cluster_centers_z.iterrows()):
                        if cluster_names[i] is not None:
                            continue
                        name = get_type_name(center_z, used_types)
                        if name in {"アヘ単型", "ウホウホ長打型"} and name not in used_types:
                            cluster_names[i] = name
                            used_types.add(name)

                    # 3周目: 残りはバランス型で埋める
                    for i in range(len(cluster_centers_z)):
                        if cluster_names[i] is None:
                            cluster_names[i] = "バランス型"

                    return cluster_names

                # z-score計算
                cluster_centers_z = cluster_centers.apply(zscore)
                # クラスタタイプ名称分類（優先度ルール）
                cluster_type_names = classify_batter_type_all(cluster_centers_z)

                st.markdown("#### 🧩 クラスタタイプ（仮称）")
                for i, style in zip(cluster_centers.index, cluster_type_names):
                    st.write(f"{i}: {style}")

                # チーム別クラスタ構成比
                st.markdown("#### 📈 チーム別クラスタ構成比")
                cluster_counts = df_vis.groupby(["team_name", "cluster"]).size().unstack(fill_value=0)
                cluster_counts_ratio = cluster_counts.div(cluster_counts.sum(axis=1), axis=0)

                fig2, ax2 = plt.subplots(figsize=(10, 4))
                cluster_counts_ratio.plot(kind="bar", stacked=True, ax=ax2, colormap="tab10")
                ax2.set_ylabel("割合")
                ax2.set_title(f"{league_name} チーム別クラスタ構成比")
                ax2.legend(title="クラスタ")
                st.pyplot(fig2)

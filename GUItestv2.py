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

# 野手データ読み込み
def load_batter_data():
    conn = sqlite3.connect("batting_stats.db")
    df = pd.read_sql_query("SELECT * FROM batting_stats", conn)
    conn.close()
    return df

df = load_data()
df_batter = pd.DataFrame()
# 「1」～「5」列を文字列型に変換（先頭ゼロや数値化防止のため）
df[["1", "2", "3", "4", "5"]] = df[["1", "2", "3", "4", "5"]].astype(str)

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
df_filtered = pd.DataFrame()  # 初期化
df_batter = pd.DataFrame()    # 初期化
if mode == "投手":
    df_filtered = df[(df["year"] == selected_year) & (df["team_name"].isin(selected_teams))]
else:
    df_batter = load_batter_data()
    for col in ["1", "2", "3", "4", "5"]:
        if col in df_batter.columns:
            df_batter[col] = df_batter[col].astype(str)
    df_batter["year"] = pd.to_numeric(df_batter["year"], errors="coerce")
    df_filtered = df_batter[(df_batter["year"] == selected_year) & (df_batter["team_name"].isin(selected_teams))]

# タブ定義（モードに関係なく共通）
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
    else:
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
        
    st.write("### 昨年→今年 比較ランキング（未実装）")

with tabs[2]:
    if mode == "野手":
        st.info("野手モードは現在未実装です。")
        
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
            df_player = df_batter[df_batter["選手名"] == selected_player].copy()
        except Exception:
            st.warning(f"{selected_player} のデータ取得でエラーが発生しました。")
            st.stop()

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
        if "year" in df_player.columns:
            df_player["year"] = pd.to_numeric(df_player["year"], errors="coerce")
            df_player = df_player.sort_values("year")

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
        df_player = df[df["選手名"] == selected_player].copy()

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
        # 年度別成績表示
        df_player["year"] = pd.to_numeric(df_player["year"], errors="coerce")
        df_player = df_player.sort_values("year")

        st.write(f"#### 年度別成績一覧（{selected_player}）")
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

    # 投打別内訳テーブル
    if mode == "投手":
        st.markdown("### 投打別内訳")
        throw_bat_summary = df_pos["投打分類"].value_counts().reset_index()
        throw_bat_summary.columns = ["投打", "人数"]
        st.dataframe(throw_bat_summary)
import streamlit as st
import plotly.graph_objects as go

# ページ設定
st.set_page_config(page_title="LDL管理目標計算システム", layout="centered")

st.title("🫀 LDLコレステロール管理目標値計算")
st.markdown("日本動脈硬化学会（JAS 2022）ガイドラインに基づく管理区分判定システム")

# --- サイドバー：ユーザー入力 ---
st.sidebar.header("患者データの入力")

# 1. 現在のLDL値
current_ldl = st.sidebar.number_input("現在のLDL値 (mg/dL)", min_value=0, max_value=500, value=140)

# 2. 病歴（二次予防か一次予防かの分岐）
st.sidebar.subheader("既往歴・合併症")
has_cad = st.sidebar.checkbox("冠動脈疾患の既往あり (二次予防)")

target_ldl = 0
risk_category = ""
description = ""

# --- ロジック判定 ---

if has_cad:
    # --- 二次予防（既往あり） ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("**二次予防の高リスク病態**")
    
    # 急性冠症候群, FH, 糖尿病, 複雑病変など
    is_very_high_risk = st.sidebar.checkbox("高リスク病態 (ACS, FH, 糖尿病合併など)")
    
    # 欧州基準などを考慮したExtreme Risk
    is_extreme_risk = st.sidebar.checkbox("再発・難治性 (Extreme Risk相当)")

    if is_extreme_risk:
        target_ldl = 55
        risk_category = "二次予防：Extreme Risk"
        description = "度重なる再発や多血管疾患など。JAS2022では到達努力、欧州では必須とされるレベル。"
    elif is_very_high_risk:
        target_ldl = 70
        risk_category = "二次予防：高リスク"
        description = "ACS、糖尿病、CKDなどを合併する冠動脈疾患既往者。"
    else:
        target_ldl = 100
        risk_category = "二次予防：一般"
        description = "冠動脈疾患の既往がある一般的な症例。"

else:
    # --- 一次予防（既往なし） ---
    # 簡易フローチャートに基づくロジック
    
    # 高リスク病態の確認
    has_dm = st.sidebar.checkbox("糖尿病")
    has_ckd = st.sidebar.checkbox("慢性腎臓病 (CKD)")
    has_pad = st.sidebar.checkbox("非心原性脳梗塞 / PAD")
    
    if has_dm or has_ckd or has_pad:
        target_ldl = 120
        risk_category = "高リスク (High Risk)"
        description = "糖尿病、CKD、または脳梗塞/PADの既往がある場合。"
    else:
        # その他のリスク因子（簡易スコアリング）
        st.sidebar.markdown("---")
        st.sidebar.markdown("**その他のリスク因子**")
        age = st.sidebar.number_input("年齢", 20, 100, 50)
        gender = st.sidebar.radio("性別", ["男性", "女性"])
        is_smoker = st.sidebar.checkbox("喫煙")
        is_ht = st.sidebar.checkbox("高血圧")
        is_low_hdl = st.sidebar.checkbox("低HDL血症 (<40)")
        has_fh_history = st.sidebar.checkbox("早発性冠動脈疾患の家族歴")
        
        # 簡易的なリスクカウント（厳密な吹田スコアではないが目安として実装）
        risk_count = 0
        if is_smoker: risk_count += 1
        if is_ht: risk_count += 1
        if is_low_hdl: risk_count += 1
        if has_fh_history: risk_count += 1
        # 年齢による加算（男性≧45, 女性≧55など簡易的に）
        if (gender == "男性" and age >= 45) or (gender == "女性" and age >= 55):
            risk_count += 1

        if risk_count >= 3:
            target_ldl = 140
            risk_category = "中リスク (Medium Risk)"
            description = "リスク因子が複数重積している状態 (吹田スコア等で評価推奨)。"
            # 注: 本来のJAS2022では中リスクは<140
        else:
            target_ldl = 160
            risk_category = "低リスク (Low Risk)"
            description = "主要なリスク因子が少ない状態。"

# --- 結果表示 ---

st.divider()

col1, col2 = st.columns([1, 2])

with col1:
    st.metric(label="あなたの管理目標値", value=f"{target_ldl} mg/dL未満")
    delta = current_ldl - target_ldl
    state = "normal" if delta <= 0 else "off"
    st.metric(label="現在の値との差", value=f"{current_ldl} mg/dL", delta=f"{delta} mg/dL", delta_color=state)

with col2:
    st.subheader(f"判定: {risk_category}")
    st.info(description)

# --- ゲージチャートによる可視化 ---
fig = go.Figure(go.Indicator(
    mode = "gauge+number+delta",
    value = current_ldl,
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': "LDL Status"},
    delta = {'reference': target_ldl, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
    gauge = {
        'axis': {'range': [None, 300], 'tickwidth': 1, 'tickcolor': "darkblue"},
        'bar': {'color': "darkblue"},
        'bgcolor': "white",
        'borderwidth': 2,
        'bordercolor': "gray",
        'steps': [
            {'range': [0, target_ldl], 'color': "lightgreen"},
            {'range': [target_ldl, target_ldl + 30], 'color': "yellow"},
            {'range': [target_ldl + 30, 300], 'color': "pink"}],
        'threshold': {
            'line': {'color': "red", 'width': 4},
            'thickness': 0.75,
            'value': target_ldl}}))

st.plotly_chart(fig, use_container_width=True)

# --- ガイドラインの参照表 ---
with st.expander("参考：JAS 2022 ガイドライン簡易表"):
    st.markdown("""
    | リスク区分 | 目標値 |
    | :--- | :--- |
    | **二次予防（冠動脈疾患既往）** | **< 100** (高リスク病態は **< 70**) |
    | **高リスク（糖尿病・CKD・脳梗塞など）** | **< 120** |
    | **中リスク** | **< 140** |
    | **低リスク** | **< 160** |
    """)

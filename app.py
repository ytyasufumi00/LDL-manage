import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# ページ設定
st.set_page_config(page_title="LDL Global Target Calculator", layout="wide")

st.title("🌐 LDLコレステロール管理目標：世界3極比較")
st.markdown("日本 (JAS 2022)、欧州 (ESC/EAS 2019/23)、米国 (ACC/ADA 2024) のガイドライン比較")

# --- サイドバー：患者データの入力 ---
st.sidebar.header("患者プロファイル")

# 1. 現在のLDL値
current_ldl = st.sidebar.number_input("現在のLDL値 (mg/dL)", min_value=0, max_value=500, value=140)

# 2. 病歴
st.sidebar.subheader("STEP 1: 既往歴")
has_cad = st.sidebar.checkbox("冠動脈疾患の既往あり (二次予防)")

# 変数初期化
targets = {
    "JP": {"val": 0, "desc": ""},
    "EU": {"val": 0, "desc": ""},
    "US": {"val": 0, "desc": ""}
}

# --- ロジック判定エンジン ---

if has_cad:
    # === 二次予防（すでに病気になった方） ===
    st.sidebar.markdown("---")
    st.sidebar.markdown("**二次予防の詳細**")
    st.sidebar.info("再発予防のため、より厳格な基準が適用されます。")
    
    is_extreme = st.sidebar.checkbox("再発・進行性 (Extreme Risk)")
    st.sidebar.caption("例: 適切な治療中に心血管イベントが再発、または他血管疾患の合併")
    
    is_very_high = st.sidebar.checkbox("高リスク病態 (ACS, 糖尿病, FH合併)")
    st.sidebar.caption("例: 急性冠症候群、糖尿病、家族性高コレステロール血症の合併")
    
    # --- 日本 (JAS 2022) ---
    if is_extreme:
        targets["JP"] = {"val": 55, "desc": "Extreme Risk (到達努力)"}
    elif is_very_high:
        targets["JP"] = {"val": 70, "desc": "高リスク二次予防"}
    else:
        targets["JP"] = {"val": 100, "desc": "一般的二次予防"}

    # --- 欧州 (ESC/EAS) ---
    if is_extreme:
         targets["EU"] = {"val": 40, "desc": "再発例 (2年以内) 推奨"}
    else:
         targets["EU"] = {"val": 55, "desc": "二次予防は一律 <55"}

    # --- 米国 (ACC/AHA/ADA) ---
    if is_very_high or is_extreme:
        targets["US"] = {"val": 55, "desc": "Very High Risk (ADA 2024)"}
    else:
        targets["US"] = {"val": 70, "desc": "High Risk (Threshold)"}

else:
    # === 一次予防（まだ病気になっていない方） ===
    st.sidebar.markdown("---")
    st.sidebar.subheader("STEP 2: リスク因子")
    
    # 主要リスク（強制的に高リスク判定になるもの）
    st.sidebar.markdown("**▼ 主要な病態（あればチェック）**")
    has_dm = st.sidebar.checkbox("糖尿病 (DM)")
    has_ckd = st.sidebar.checkbox("慢性腎臓病 (CKD)")
    has_fh = st.sidebar.checkbox("家族性高コレステロール血症 (FH)")
    has_pad = st.sidebar.checkbox("非心原性脳梗塞 / 末梢動脈疾患")

    # その他のリスク因子（加算方式）
    st.sidebar.markdown("**▼ その他の危険因子（個数を自動計算）**")
    
    # 年齢入力
    age = st.sidebar.number_input("年齢", 20, 100, 50)
    gender = st.sidebar.radio("性別", ["男性", "女性"], horizontal=True)
    
    # リスク因子のチェックボックス
    rf_ht = st.sidebar.checkbox("高血圧 (130/85mmHg以上)")
    rf_smoke = st.sidebar.checkbox("喫煙習慣あり")
    rf_low_hdl = st.sidebar.checkbox("低HDL血症 (40mg/dL未満)")
    rf_family = st.sidebar.checkbox("早発性冠動脈疾患の家族歴")
    st.sidebar.caption("※家族歴: 男性親族<55歳, 女性親族<65歳での発症")

    # リスク因子の自動カウント
    risk_factors = 0
    if rf_ht: risk_factors += 1
    if rf_smoke: risk_factors += 1
    if rf_low_hdl: risk_factors += 1
    if rf_family: risk_factors += 1
    # 年齢による加算 (日本のガイドライン準拠: 男性45歳以上, 女性55歳以上)
    if (gender == "男性" and age >= 45) or (gender == "女性" and age >= 55):
        risk_factors += 1
        st.sidebar.write(f"ℹ️ 年齢がリスク因子に含まれます (+1)")

    st.sidebar.markdown(f"**現在の累積リスク数: {risk_factors} 個**")

    # --- 日本 (JAS 2022) ---
    if has_fh or has_pad or (has_ckd) or (has_dm and (has_pad or has_ckd)): 
        # ※簡易ロジックです。厳密にはCKDの重症度などで細分化されます
        targets["JP"] = {"val": 120, "desc": "高リスク"}
    elif has_dm: # 糖尿病単独は条件によるが一旦中～高リスク
        targets["JP"] = {"val": 120, "desc": "高リスク(DM)"}
    elif risk_factors >= 2: # 吹田スコア等で高リスク寄り
        targets["JP"] = {"val": 140, "desc": "中リスク"}
    else:
        targets["JP"] = {"val": 160, "desc": "低リスク"}

    # --- 欧州 (ESC/EAS) ---
    if (has_dm and risk_factors >= 1) or has_ckd or (has_fh and risk_factors >= 1):
        targets["EU"] = {"val": 55, "desc": "超高リスク"}
    elif has_fh or has_dm:
        targets["EU"] = {"val": 70, "desc": "高リスク"}
    elif risk_factors >= 3: 
        targets["EU"] = {"val": 100, "desc": "中リスク"}
    else:
        targets["EU"] = {"val": 116, "desc": "低リスク"}

    # --- 米国 (ACC/AHA) ---
    if has_dm or has_fh:
        targets["US"] = {"val": 70, "desc": "DM/FHは厳格管理"}
    elif risk_factors >= 2:
        targets["US"] = {"val": 100, "desc": "中等度リスク"}
    else:
        targets["US"] = {"val": 130, "desc": "低リスク"}

# --- UI表示 ---

# 1. 3極比較カード
st.subheader("🏁 ガイドライン別 管理目標値")

col1, col2, col3 = st.columns(3)

def show_metric(col, region, flag, data):
    with col:
        st.markdown(f"### {flag} {region}")
        st.metric(label=data["desc"], value=f"< {data['val']}")
        diff = current_ldl - data['val']
        if diff > 0:
            st.error(f"あと {diff} 低下が必要")
        else:
            st.success("達成済み")

show_metric(col1, "日本 (JAS)", "🇯🇵", targets["JP"])
show_metric(col2, "欧州 (ESC)", "🇪🇺", targets["EU"])
show_metric(col3, "米国 (ACC/ADA)", "🇺🇸", targets["US"])

# 2. 比較チャート (Bar Chart)
st.divider()
st.subheader("📊 厳格度の比較")

df = pd.DataFrame({
    "Region": ["日本 (JAS)", "欧州 (ESC)", "米国 (ACC)"],
    "Target LDL": [targets["JP"]["val"], targets["EU"]["val"], targets["US"]["val"]],
    "Color": ["#d62728", "#1f77b4", "#2ca02c"]
})

fig = go.Figure()

fig.add_trace(go.Bar(
    x=df["Region"],
    y=df["Target LDL"],
    text=df["Target LDL"],
    textposition='auto',
    marker_color=['#FF9999', '#9999FF', '#99FF99'],
    name="目標値"
))

fig.add_shape(
    type="line",
    x0=-0.5, x1=2.5,
    y0=current_ldl, y1=current_ldl,
    line=dict(color="Red", width=4, dash="dash"),
)

fig.add_annotation(
    x=2.5, y=current_ldl,
    text=f"現在値: {current_ldl}",
    showarrow=True, arrowhead=1
)

fig.update_layout(
    title="あなたの現在値 vs 各国の目標値 (低いほど厳格)",
    yaxis_title="LDL-C (mg/dL)",
    yaxis_range=[0, max(current_ldl + 20, 180)]
)

st.plotly_chart(fig, use_container_width=True)

# 3. 解説
st.info(f"""
**解説:**
- **欧州 (ESC)** は世界で最も厳格で、二次予防では一律 **55mg/dL未満** を推奨しています。
- **米国** は近年欧州基準に近づいており、特に糖尿病や超高リスク群では **55mg/dL** を考慮します。
- **日本** は人種差（冠動脈疾患の少なさ）を考慮し、全体的にマイルドですが、リスクが高い場合は **70mg/dL** 未満への厳格化が進んでいます。
""")

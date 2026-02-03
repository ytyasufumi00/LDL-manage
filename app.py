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
st.sidebar.subheader("既往歴・リスク因子")
has_cad = st.sidebar.checkbox("冠動脈疾患の既往あり (二次予防)")

# 変数初期化
targets = {
    "JP": {"val": 0, "desc": ""},
    "EU": {"val": 0, "desc": ""},
    "US": {"val": 0, "desc": ""}
}

# --- ロジック判定エンジン ---

if has_cad:
    # === 二次予防 ===
    st.sidebar.markdown("---")
    st.sidebar.markdown("**二次予防の高リスク病態**")
    
    is_extreme = st.sidebar.checkbox("再発・進行性 (Extreme Risk)")
    is_very_high = st.sidebar.checkbox("高リスク病態 (ACS, 糖尿病, FH合併)")
    
    # --- 日本 (JAS 2022) ---
    if is_extreme:
        targets["JP"] = {"val": 55, "desc": "Extreme Risk (到達努力)"}
    elif is_very_high:
        targets["JP"] = {"val": 70, "desc": "高リスク二次予防"}
    else:
        targets["JP"] = {"val": 100, "desc": "一般的二次予防"}

    # --- 欧州 (ESC/EAS) ---
    # 欧州は二次予防は原則すべて「超高リスク」扱い
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
    # === 一次予防 ===
    st.sidebar.markdown("---")
    st.sidebar.markdown("**一次予防のリスク因子**")
    
    has_dm = st.sidebar.checkbox("糖尿病 (DM)")
    has_ckd = st.sidebar.checkbox("慢性腎臓病 (CKD)")
    has_fh = st.sidebar.checkbox("家族性高コレステロール血症 (FH)")
    
    # 簡易スコアリング用
    age = st.sidebar.number_input("年齢", 20, 100, 50)
    st.sidebar.caption("その他: 高血圧, 喫煙, 低HDL等は簡易判定に含みます")
    risk_factors = st.sidebar.slider("その他のリスク因子数", 0, 5, 1)
    
    # --- 日本 (JAS 2022) ---
    if has_fh or has_dm or has_ckd: # 本来はもっと細かい区分あり
        targets["JP"] = {"val": 120, "desc": "高リスク"}
    elif risk_factors >= 2:
        targets["JP"] = {"val": 140, "desc": "中リスク"}
    else:
        targets["JP"] = {"val": 160, "desc": "低リスク"}

    # --- 欧州 (ESC/EAS) ---
    # 欧州はFHや長期DMを「超高リスク(<55)」「高リスク(<70)」に分類する
    if (has_dm and risk_factors >= 1) or (has_ckd) or (has_fh and risk_factors >= 1):
        targets["EU"] = {"val": 55, "desc": "超高リスク (DM+合併症等)"}
    elif has_fh or has_dm:
        targets["EU"] = {"val": 70, "desc": "高リスク"}
    elif risk_factors >= 3: # SCOREチャートの代用
        targets["EU"] = {"val": 100, "desc": "中リスク"}
    else:
        targets["EU"] = {"val": 116, "desc": "低リスク"}

    # --- 米国 (ACC/AHA) ---
    # 米国は数値目標よりリスク低減率を重視するが、閾値として設定
    if has_dm or has_fh:
        targets["US"] = {"val": 70, "desc": "DM/FHは厳格管理"} # 実際は個別判断
    elif risk_factors >= 2:
        targets["US"] = {"val": 100, "desc": "中等度リスク"}
    else:
        targets["US"] = {"val": 130, "desc": "低リスク (生活習慣改善)"}

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

# データフレーム作成
df = pd.DataFrame({
    "Region": ["日本 (JAS)", "欧州 (ESC)", "米国 (ACC)"],
    "Target LDL": [targets["JP"]["val"], targets["EU"]["val"], targets["US"]["val"]],
    "Color": ["#d62728", "#1f77b4", "#2ca02c"] # Plotly colors
})

# 現在値のラインを追加したチャート
fig = go.Figure()

# 各国の目標値バー
fig.add_trace(go.Bar(
    x=df["Region"],
    y=df["Target LDL"],
    text=df["Target LDL"],
    textposition='auto',
    marker_color=['#FF9999', '#9999FF', '#99FF99'],
    name="目標値"
))

# 現在値のライン
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

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# ページ設定
st.set_page_config(page_title="LDL Global Target Calculator", layout="wide")

st.title("🌐 LDLコレステロール管理目標：世界3極比較")
st.markdown("日本 (JAS 2022)、欧州 (ESC/EAS 2019/23)、米国 (ACC/ADA 2024) のガイドライン比較")

# --- サイドバー：ユーザー入力 ---
st.sidebar.header("患者プロファイル")
current_ldl = st.sidebar.number_input("現在のLDL値 (mg/dL)", min_value=0, max_value=500, value=140)

# ==========================================
# STEP 1: 動脈硬化性疾患の既往 (History)
# ==========================================
st.sidebar.subheader("STEP 1: 動脈硬化性疾患の既往")

# 冠動脈疾患（これが日本の二次予防の定義）
has_cad = st.sidebar.checkbox("冠動脈疾患 (心筋梗塞・狭心症・PCI後)")

# 非心原性脳梗塞・PAD（欧米では二次予防、日本では高リスク一次予防扱い）
has_other_history = st.sidebar.checkbox("非心原性脳梗塞 または 末梢動脈疾患(PAD)")

st.sidebar.markdown("---")

# 二次予防の詳細オプション
is_extreme = False
is_very_high = False

if has_cad or has_other_history:
    st.sidebar.markdown("**既往歴あり：詳細リスク**")
    is_extreme = st.sidebar.checkbox("再発・進行性 (Extreme Risk)")
    st.sidebar.caption("例: 治療中の再発、多血管病変")
    
    is_very_high = st.sidebar.checkbox("高リスク病態 (糖尿病, FH, ACS合併)")

# ==========================================
# STEP 2: リスク因子 (Risk Factors)
# ==========================================
st.sidebar.subheader("STEP 2: リスク因子")

# 主要な病態
has_dm = st.sidebar.checkbox("糖尿病 (DM)")
has_ckd = st.sidebar.checkbox("慢性腎臓病 (CKD)")
has_fh = st.sidebar.checkbox("家族性高コレステロール血症 (FH)")

# その他の危険因子（個数カウント）
st.sidebar.markdown("**▼ その他の危険因子**")
age = st.sidebar.number_input("年齢", 20, 100, 50)
gender = st.sidebar.radio("性別", ["男性", "女性"], horizontal=True)

rf_ht = st.sidebar.checkbox("高血圧 (130/85mmHg以上)")
rf_smoke = st.sidebar.checkbox("喫煙習慣あり")
rf_low_hdl = st.sidebar.checkbox("低HDL血症 (40mg/dL未満)")
rf_family = st.sidebar.checkbox("早発性冠動脈疾患の家族歴")

# リスク因子の自動カウント
risk_factors = 0
if rf_ht: risk_factors += 1
if rf_smoke: risk_factors += 1
if rf_low_hdl: risk_factors += 1
if rf_family: risk_factors += 1

# 年齢による加算 (JAS2022準拠)
age_risk = False
if (gender == "男性" and age >= 45) or (gender == "女性" and age >= 55):
    risk_factors += 1
    age_risk = True

if age_risk:
    st.sidebar.caption(f"ℹ️ 年齢リスク加算あり (+1)")
st.sidebar.write(f"**累積リスク数: {risk_factors} 個**")


# ==========================================
# 判定ロジックエンジン
# ==========================================

targets = {
    "JP": {"val": 0, "desc": ""},
    "EU": {"val": 0, "desc": ""},
    "US": {"val": 0, "desc": ""}
}

# --- 1. 日本 (JAS 2022) ---
if has_cad: 
    # 純粋な二次予防
    if is_extreme: targets["JP"] = {"val": 55, "desc": "Extreme Risk"}
    elif is_very_high: targets["JP"] = {"val": 70, "desc": "高リスク二次予防"}
    else: targets["JP"] = {"val": 100, "desc": "二次予防(冠動脈)"}

elif has_other_history: 
    # 脳梗塞/PADのみ（日本ではカテゴリーIII 高リスク扱い）
    targets["JP"] = {"val": 120, "desc": "高リスク(脳/PAD)"} # ※ここが重要

elif has_fh or has_ckd or has_dm:
    # 糖尿病単独などは条件によるが便宜上カテゴリーIII
    targets["JP"] = {"val": 120, "desc": "高リスク(DM/CKD/FH)"}

elif risk_factors >= 2:
    targets["JP"] = {"val": 140, "desc": "中リスク"}
else:
    targets["JP"] = {"val": 160, "desc": "低リスク"}


# --- 2. 欧州 (ESC/EAS) ---
# 欧州では脳梗塞/PADもASCVDとして超高リスク扱い
has_ascvd = has_cad or has_other_history

if has_ascvd:
    if is_extreme: targets["EU"] = {"val": 40, "desc": "再発例 推奨"}
    else: targets["EU"] = {"val": 55, "desc": "超高リスク(ASCVD)"}
    
elif (has_dm and risk_factors >= 1) or has_ckd or (has_fh and risk_factors >= 1):
    targets["EU"] = {"val": 55, "desc": "超高リスク"}
elif has_fh or has_dm:
    targets["EU"] = {"val": 70, "desc": "高リスク"}
elif risk_factors >= 3: 
    targets["EU"] = {"val": 100, "desc": "中リスク"}
else:
    targets["EU"] = {"val": 116, "desc": "低リスク"}


# --- 3. 米国 (ACC/AHA) ---
if has_ascvd: # 米国もASCVDとして扱う
    if is_very_high or is_extreme: targets["US"] = {"val": 55, "desc": "Very High Risk"}
    else: targets["US"] = {"val": 70, "desc": "High Risk"}

elif has_dm or has_fh:
    targets["US"] = {"val": 70, "desc": "DM/FHは厳格管理"}
elif risk_factors >= 2:
    targets["US"] = {"val": 100, "desc": "中等度リスク"}
else:
    targets["US"] = {"val": 130, "desc": "低リスク"}


# ==========================================
# UI表示
# ==========================================

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

# チャート
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
    type="line", x0=-0.5, x1=2.5, y0=current_ldl, y1=current_ldl,
    line=dict(color="Red", width=4, dash="dash"),
)
fig.add_annotation(
    x=2.5, y=current_ldl, text=f"現在値: {current_ldl}",
    showarrow=True, arrowhead=1
)
fig.update_layout(
    title="あなたの現在値 vs 各国の目標値",
    yaxis_title="LDL-C (mg/dL)",
    yaxis_range=[0, max(current_ldl + 20, 180)]
)

st.plotly_chart(fig, use_container_width=True)

st.info("""
**💡 ガイドラインの違いについて:**
- **欧州 (ESC)** は世界で最も厳格で、二次予防では一律 **55mg/dL未満** を推奨しています。
- **米国** は近年欧州基準に近づいており、特に糖尿病や超高リスク群では **55mg/dL** を考慮します。
- **日本** は人種差（冠動脈疾患の少なさ）を考慮し、全体的にマイルドですが、リスクが高い場合は **70mg/dL** 未満への厳格化が進んでいます。
- **脳梗塞・PADの扱い:** ご指摘の通りこれらは「動脈硬化の既往」ですが、日本のガイドライン(JAS 2022)では、冠動脈疾患がない場合、原則として目標値は **<120 mg/dL** (高リスク) と設定されます。一方、欧米ではこれらも「二次予防」と同等とみなし、より厳しい **<55 mg/dL** や **<70 mg/dL** が推奨されます。
- **年齢リスク:** JAS 2022では、男性45歳以上・女性55歳以上をリスク因子としてカウントします。
""")

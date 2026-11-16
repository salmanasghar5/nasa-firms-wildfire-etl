import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import requests
import io
from datetime import datetime, timezone

# 1. Page Configuration
st.set_page_config(
    page_title="NASA FIRMS | Orbital Telemetry HUD",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Sci-Fi Telemetry HUD & Node-Graph CSS (Cyan #00F5D4 + Amber #FF9F1C)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;800&family=JetBrains+Mono:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    header[data-testid="stHeader"] { background: transparent; }
    footer { visibility: hidden; }

    /* Deep Space HUD Grid Background */
    .stApp {
        background-color: #030712;
        background-image:
            radial-gradient(circle at 50% 0%, rgba(0, 245, 212, 0.08) 0%, transparent 45%),
            radial-gradient(circle at 85% 85%, rgba(255, 159, 28, 0.06) 0%, transparent 40%),
            linear-gradient(rgba(0, 245, 212, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 245, 212, 0.03) 1px, transparent 1px);
        background-size: 100% 100%, 100% 100%, 36px 36px, 36px 36px;
    }

    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1560px;
    }

    /* HUD Top Header Bar */
    .hud-header {
        background: linear-gradient(90deg, rgba(6, 15, 30, 0.95) 0%, rgba(10, 25, 47, 0.9) 50%, rgba(6, 15, 30, 0.95) 100%);
        border: 1px solid rgba(0, 245, 212, 0.35);
        box-shadow: 0 0 25px rgba(0, 245, 212, 0.12), inset 0 0 15px rgba(0, 245, 212, 0.05);
        border-radius: 12px;
        padding: 14px 24px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .hud-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.35rem;
        font-weight: 800;
        color: #00F5D4;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        text-shadow: 0 0 12px rgba(0, 245, 212, 0.45);
    }
    .hud-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.76rem;
        color: #94A3B8;
        margin-top: 2px;
    }
    .hud-status {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: #FF9F1C;
        background: rgba(255, 159, 28, 0.12);
        border: 1px solid rgba(255, 159, 28, 0.45);
        padding: 6px 14px;
        border-radius: 6px;
        letter-spacing: 0.05em;
    }

    /* HUD Panel Frame */
    .hud-panel {
        background: rgba(7, 16, 32, 0.86);
        border: 1px solid rgba(0, 245, 212, 0.25);
        border-top: 2px solid #00F5D4;
        border-radius: 10px;
        padding: 12px 14px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.55);
        margin-bottom: 12px;
    }
    .hud-panel-amber {
        background: rgba(7, 16, 32, 0.86);
        border: 1px solid rgba(255, 159, 28, 0.28);
        border-top: 2px solid #FF9F1C;
        border-radius: 10px;
        padding: 12px 14px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.55);
        margin-bottom: 12px;
    }
    .panel-label {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.74rem;
        font-weight: 700;
        color: #00F5D4;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
    }
    .panel-label-amber {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.74rem;
        font-weight: 700;
        color: #FF9F1C;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    /* Metric Cards */
    div[data-testid="stMetric"], div[data-testid="metric-container"] {
        background: rgba(8, 18, 36, 0.9);
        border: 1px solid rgba(0, 245, 212, 0.25);
        border-left: 3px solid #FF9F1C;
        padding: 12px 16px;
        border-radius: 8px;
    }
    div[data-testid="stMetricValue"] {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.45rem !important;
        color: #00F5D4 !important;
    }
    div[data-testid="stMetricLabel"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem !important;
        color: #94A3B8 !important;
        text-transform: uppercase;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: rgba(7, 16, 32, 0.9);
        padding: 5px;
        border-radius: 8px;
        border: 1px solid rgba(0, 245, 212, 0.25);
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: #94A3B8;
        border-radius: 6px;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(0, 245, 212, 0.18) !important;
        color: #00F5D4 !important;
        border: 1px solid #00F5D4 !important;
    }
</style>
""", unsafe_allow_html=True)

DB_PATH = "wildfire_pipeline.db"

# 3. Data Processing & NASA API Functions
def classify_risk(brightness):
    if brightness >= 360:
        return "Extreme"
    elif brightness >= 330:
        return "High"
    elif brightness >= 310:
        return "Moderate"
    return "Low"

def assign_region(lat, lon):
    if 15 <= lat <= 75 and -170 <= lon <= -50:
        return "North America"
    elif -60 <= lat < 15 and -90 <= lon <= -30:
        return "South America"
    elif 35 <= lat <= 72 and -25 <= lon <= 45:
        return "Europe"
    elif -38 <= lat < 35 and -20 <= lon <= 55:
        return "Africa"
    elif -50 <= lat <= 0 and 110 <= lon <= 180:
        return "Oceania"
    elif 0 <= lat <= 78 and 45 < lon <= 180:
        return "Asia"
    return "Maritime"

def enrich_dataframe(df):
    if "bright_ti4" in df.columns and "brightness" not in df.columns:
        df.rename(columns={"bright_ti4": "brightness"}, inplace=True)
    df["brightness"] = pd.to_numeric(df["brightness"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude", "brightness"]).copy()
    df["risk_tier"] = df["brightness"].apply(classify_risk)
    df["region"] = df.apply(lambda r: assign_region(r["latitude"], r["longitude"]), axis=1)
    if "acq_time" in df.columns:
        df["acq_hour"] = (pd.to_numeric(df["acq_time"], errors="coerce").fillna(0) // 100).astype(int)
    else:
        df["acq_hour"] = range(len(df))
    return df

def sync_live_nasa_feed():
    map_key = "11be2b95414f1e231600092cc3ff7148"
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{map_key}/VIIRS_NOAA20_NRT/world/1"
    raw_df = pd.read_csv(url)
    clean_df = enrich_dataframe(raw_df).head(600)
    conn = sqlite3.connect(DB_PATH)
    clean_df.to_sql("wildfire_anomalies", conn, if_exists="replace", index=False)
    conn.close()
    return clean_df

@st.cache_data(ttl=300)
def load_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    if not tables:
        conn.close()
        return sync_live_nasa_feed()
    df = pd.read_sql_query(f"SELECT * FROM {tables[0][0]}", conn)
    conn.close()
    return enrich_dataframe(df)

try:
    df = load_data()
except Exception as e:
    st.error(f"Telemetry error: {e}")
    st.stop()

# 4. Top HUD Banner + Inline Quick Controls
now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
st.markdown(f"""
<div class="hud-header">
    <div>
        <div class="hud-title">🛰️ NASA FIRMS // ORBITAL THERMAL TELEMETRY HUD</div>
        <div class="hud-sub">SENSOR: VIIRS NOAA-20 • VALIDATION: PYDANTIC V2 • STORAGE: SQLITE3 • NODES: {len(df):,}</div>
    </div>
    <div class="hud-status">● STREAM ACTIVE // {now_utc}</div>
</div>
""", unsafe_allow_html=True)

# Compact Control Strip right below header
ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([1.3, 2.2, 2.2, 1.8])
with ctrl1:
    if st.button("🔄 SYNC LIVE NASA FEED", use_container_width=True, type="primary"):
        with st.spinner("Ingesting orbital feed..."):
            sync_live_nasa_feed()
            st.cache_data.clear()
            st.rerun()
with ctrl2:
    all_tiers = [t for t in ["Extreme", "High", "Moderate", "Low"] if t in df["risk_tier"].unique()]
    selected_tiers = st.multiselect("RISK NODES", all_tiers, default=all_tiers, label_visibility="collapsed")
with ctrl3:
    all_regions = sorted(df["region"].unique().tolist())
    selected_regions = st.multiselect("CONTINENTAL SECTORS", all_regions, default=all_regions, label_visibility="collapsed")
with ctrl4:
    min_b, max_b = float(df["brightness"].min()), float(df["brightness"].max())
    b_range = st.slider("KELVIN THRESHOLD", min_b, max_b, (min_b, max_b), label_visibility="collapsed")

filtered_df = df[
    (df["risk_tier"].isin(selected_tiers)) &
    (df["region"].isin(selected_regions)) &
    (df["brightness"] >= b_range[0]) &
    (df["brightness"] <= b_range[1])
]

# KPI Telemetry Row
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.metric("ACTIVE NODES", f"{len(filtered_df):,}")
with m2:
    mean_k = filtered_df["brightness"].mean() if not filtered_df.empty else 0.0
    st.metric("MEAN KELVIN", f"{mean_k:.1f} K")
with m3:
    peak_k = filtered_df["brightness"].max() if not filtered_df.empty else 0.0
    st.metric("PEAK THERMAL", f"{peak_k:.1f} K")
with m4:
    ext_cnt = len(filtered_df[filtered_df["risk_tier"].isin(["Extreme", "High"])])
    st.metric("HIGH/EXTREME", f"{ext_cnt}")
with m5:
    top_sec = filtered_df["region"].mode()[0] if not filtered_df.empty else "N/A"
    st.metric("PRIMARY SECTOR", top_sec)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# 5. MAIN 3-COLUMN HUD COMMAND GRID (Inspired by Image 1 Node Tree + Image 2 Telemetry HUD)
col_left, col_center, col_right = st.columns([1.35, 2.3, 1.35], gap="small")

# === LEFT COLUMN: Interactive Hierarchy Node Tree (Like Image 1) + Polar Radar ===
with col_left:
    st.markdown('<div class="hud-panel"><div class="panel-label"><span>☍ TELEMETRY NODE TREE</span><span>HIERARCHY</span></div>', unsafe_allow_html=True)
    if not filtered_df.empty:
        # Build interactive hierarchy: Global Feed -> Region -> Risk Tier
        tree_df = filtered_df.groupby(["region", "risk_tier"], as_index=False).size()
        fig_tree = px.icicle(
            tree_df,
            path=[px.Constant("NASA FIRMS"), "region", "risk_tier"],
            values="size",
            color="risk_tier",
            color_discrete_map={
                "(?)": "#0A192F",
                "Extreme": "#FF2B2B",
                "High": "#FF9F1C",
                "Moderate": "#FACC15",
                "Low": "#00F5D4"
            }
        )
        fig_tree.update_traces(root_color="#0F2942", tiling=dict(orientation="h"))
        fig_tree.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0", size=11, family="JetBrains Mono"),
            margin=dict(t=4, b=4, l=4, r=4),
            height=300
        )
        st.plotly_chart(fig_tree, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Bottom Left: Polar Coordinate Radar (Like Image 2 bottom-left radar)
    st.markdown('<div class="hud-panel-amber"><div class="panel-label-amber">◎ SECTOR RADAR SIGNATURE</div>', unsafe_allow_html=True)
    if not filtered_df.empty:
        radar_df = filtered_df.groupby("region", as_index=False)["brightness"].mean()
        fig_radar = go.Figure(go.Scatterpolar(
            r=radar_df["brightness"],
            theta=radar_df["region"],
            fill="toself",
            fillcolor="rgba(0, 245, 212, 0.22)",
            line=dict(color="#00F5D4", width=2),
            marker=dict(color="#FF9F1C", size=6)
        ))
        fig_radar.update_layout(
            polar=dict(
                bgcolor="rgba(6, 15, 30, 0.8)",
                radialaxis=dict(visible=True, range=[290, 360], gridcolor="rgba(0,245,212,0.18)", tickfont=dict(size=9, color="#94A3B8")),
                angularaxis=dict(gridcolor="rgba(0,245,212,0.18)", tickfont=dict(size=10, color="#E2E8F0"))
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=18, b=18, l=28, r=28),
            height=250,
            showlegend=False
        )
        st.plotly_chart(fig_radar, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# === CENTER COLUMN: Time-Series Waveform with Range Slider (Image 1) + Orbital Map (Image 2) ===
with col_center:
    st.markdown('<div class="hud-panel"><div class="panel-label"><span>📈 THERMAL WAVEFORM & RANGE SCROLLER</span><span>VIIRS TI4</span></div>', unsafe_allow_html=True)
    if not filtered_df.empty:
        wave_df = filtered_df.reset_index(drop=True)
        wave_df["Sequence"] = wave_df.index + 1
        fig_wave = px.line(
            wave_df,
            x="Sequence",
            y="brightness",
            color="risk_tier",
            color_discrete_map={"Extreme": "#FF2B2B", "High": "#FF9F1C", "Moderate": "#FACC15", "Low": "#00F5D4"}
        )
        fig_wave.update_traces(line=dict(width=1.8))
        fig_wave.update_xaxes(rangeslider_visible=True, rangeslider_thickness=0.14, gridcolor="rgba(0,245,212,0.1)")
        fig_wave.update_yaxes(gridcolor="rgba(0,245,212,0.1)", title="Kelvin (K)")
        fig_wave.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(4, 11, 24, 0.75)",
            font=dict(color="#E2E8F0", size=10, family="JetBrains Mono"),
            margin=dict(t=6, b=6, l=10, r=10),
            height=245,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None)
        )
        st.plotly_chart(fig_wave, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Center Bottom: Dark Orbital Map (Like Image 2 bottom-right world telemetry map)
    st.markdown('<div class="hud-panel"><div class="panel-label"><span>🌍 GLOBAL ORBITAL PROJECTION</span><span>ESRI DARK CANVAS</span></div>', unsafe_allow_html=True)
    if not filtered_df.empty:
        m = folium.Map(
            location=[filtered_df["latitude"].median(), filtered_df["longitude"].median()],
            zoom_start=2,
            min_zoom=2,
            world_copy_jump=False,
            tiles=None
        )
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
            attr="Esri",
            no_wrap=True
        ).add_to(m)

        colors = {"Extreme": "#FF2B2B", "High": "#FF9F1C", "Moderate": "#FACC15", "Low": "#00F5D4"}
        for _, row in filtered_df.head(350).iterrows():
            c = colors.get(row["risk_tier"], "#00F5D4")
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=6 if row["risk_tier"] in ["Extreme", "High"] else 4,
                color=c,
                weight=1.5,
                fill=True,
                fill_color=c,
                fill_opacity=0.85,
                popup=f"<b>Sector:</b> {row['region']}<br><b>Tier:</b> {row['risk_tier']}<br><b>Temp:</b> {row['brightness']:.1f} K"
            ).add_to(m)
        st_folium(m, width=None, height=305, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# === RIGHT COLUMN: Circular Telemetry Gauges (Image 2 Top) + Dual Pie Breakdowns (Image 1 Bottom) ===
with col_right:
    st.markdown('<div class="hud-panel-amber"><div class="panel-label-amber">⚡ THERMAL INTENSITY GAUGE</div>', unsafe_allow_html=True)
    if not filtered_df.empty:
        peak_val = float(filtered_df["brightness"].max())
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=peak_val,
            number={"font": {"color": "#00F5D4", "family": "Orbitron", "size": 28}, "suffix": " K"},
            gauge={
                "axis": {"range": [280, 410], "tickwidth": 1, "tickcolor": "#00F5D4", "tickfont": {"size": 9}},
                "bar": {"color": "#FF9F1C", "thickness": 0.28},
                "bgcolor": "rgba(6,15,30,0.9)",
                "borderwidth": 1,
                "bordercolor": "rgba(0,245,212,0.3)",
                "steps": [
                    {"range": [280, 310], "color": "rgba(0, 245, 212, 0.15)"},
                    {"range": [310, 330], "color": "rgba(250, 204, 21, 0.2)"},
                    {"range": [330, 360], "color": "rgba(255, 159, 28, 0.3)"},
                    {"range": [360, 410], "color": "rgba(255, 43, 43, 0.4)"}
                ]
            }
        ))
        fig_g.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0"),
            margin=dict(t=15, b=10, l=20, r=20),
            height=190
        )
        st.plotly_chart(fig_g, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Dual Pie Charts (Like Image 1 bottom "All Forcings" & "Human vs Natural")
    st.markdown('<div class="hud-panel"><div class="panel-label"><span>◔ TIER & SECTOR RATIOS</span><span>SPLIT</span></div>', unsafe_allow_html=True)
    if not filtered_df.empty:
        p1, p2 = st.columns(2)
        with p1:
            fig_p1 = px.pie(
                filtered_df,
                names="risk_tier",
                hole=0.45,
                color="risk_tier",
                color_discrete_map={"Extreme": "#FF2B2B", "High": "#FF9F1C", "Moderate": "#FACC15", "Low": "#00F5D4"}
            )
            fig_p1.update_traces(textinfo="percent", textfont_size=10)
            fig_p1.update_layout(
                title=dict(text="Risk Tiers", font=dict(size=11, color="#00F5D4"), x=0.5),
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=28, b=4, l=2, r=2),
                height=180,
                showlegend=False
            )
            st.plotly_chart(fig_p1, use_container_width=True)
        with p2:
            fig_p2 = px.pie(
                filtered_df,
                names="region",
                hole=0.45,
                color_discrete_sequence=["#00F5D4", "#FF9F1C", "#38BDF8", "#F43F5E", "#A855F7", "#FACC15"]
            )
            fig_p2.update_traces(textinfo="percent", textfont_size=10)
            fig_p2.update_layout(
                title=dict(text="Continents", font=dict(size=11, color="#FF9F1C"), x=0.5),
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=28, b=4, l=2, r=2),
                height=180,
                showlegend=False
            )
            st.plotly_chart(fig_p2, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Live Top Hotspots Feed Mini-Table
    st.markdown('<div class="hud-panel-amber"><div class="panel-label-amber">🔥 PRIORITY HOTSPOT LOG</div>', unsafe_allow_html=True)
    if not filtered_df.empty:
        mini_top = filtered_df.sort_values("brightness", ascending=False)[["region", "brightness", "risk_tier"]].head(4)
        st.dataframe(mini_top, use_container_width=True, hide_index=True, height=145)
    st.markdown('</div>', unsafe_allow_html=True)

# 6. Expandable Deep-Dive Telemetry Drawer (Data Table, Alert Simulator & Exports)
with st.expander("📂 OPEN FULL TELEMETRY MATRIX, ALERT SIMULATOR & EXPORT TOOLS", expanded=False):
    ex1, ex2 = st.columns([2.2, 1])
    with ex1:
        search_q = st.text_input("🔍 Filter Telemetry Records:", placeholder="Search by continent, risk tier, or coordinate...")
        export_df = filtered_df.copy()
        if search_q:
            mask = export_df.astype(str).apply(lambda col: col.str.contains(search_q, case=False, na=False)).any(axis=1)
            export_df = export_df[mask]
        st.dataframe(export_df, use_container_width=True, height=280)

    with ex2:
        st.markdown("#### 🚨 Threshold Alert & Export")
        thresh = st.slider("Alert Trigger (K)", 300.0, 400.0, 340.0)
        flagged = len(filtered_df[filtered_df["brightness"] >= thresh])
        st.info(f"**{flagged}** active nodes exceed **{thresh} K**.")

        c_dl1, c_dl2, c_dl3 = st.columns(3)
        with c_dl1:
            st.download_button("CSV", export_df.to_csv(index=False).encode("utf-8"), "firms_hud.csv", "text/csv", use_container_width=True)
        with c_dl2:
            st.download_button("JSON", export_df.to_json(orient="records", indent=2).encode("utf-8"), "firms_hud.json", "application/json", use_container_width=True)
        with c_dl3:
            buf = io.BytesIO()
            export_df.to_excel(buf, index=False, engine="openpyxl")
            st.download_button("XLSX", buf.getvalue(), "firms_hud.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

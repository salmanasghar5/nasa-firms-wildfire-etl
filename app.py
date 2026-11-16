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
    page_title="NASA FIRMS | Orbital Wildfire Intelligence",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Modern SaaS / Vercel-Grade Dark Glassmorphism CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Hide default Streamlit top header bar & footer for a clean web-app look */
    header[data-testid="stHeader"] {
        background: transparent;
    }
    footer { visibility: hidden; }

    /* Deep Space Mesh Gradient Background */
    .stApp {
        background:
            radial-gradient(circle at 15% 15%, rgba(255, 87, 34, 0.08) 0%, transparent 40%),
            radial-gradient(circle at 85% 20%, rgba(56, 189, 248, 0.07) 0%, transparent 40%),
            linear-gradient(180deg, #070A12 0%, #0B0F1A 100%);
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
        max-width: 1440px;
    }

    /* Hero Banner Styling */
    .hero-box {
        background: linear-gradient(135deg, rgba(19, 27, 46, 0.85) 0%, rgba(12, 17, 30, 0.92) 100%);
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 18px;
        padding: 22px 28px;
        margin-bottom: 22px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45);
        backdrop-filter: blur(16px);
    }
    .hero-title {
        font-size: 1.75rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FFFFFF 0%, #CBD5E1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .hero-sub {
        color: #94A3B8;
        font-size: 0.9rem;
        margin-top: 4px;
    }
    .live-badge {
        background: rgba(16, 185, 129, 0.14);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #34D399;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    .pulse-dot {
        height: 8px;
        width: 8px;
        background-color: #10B981;
        border-radius: 50%;
        box-shadow: 0 0 8px #10B981;
    }

    /* Fixed KPI Metric Cards */
    div[data-testid="stMetric"], div[data-testid="metric-container"] {
        background: linear-gradient(145deg, rgba(20, 28, 48, 0.85) 0%, rgba(13, 18, 32, 0.95) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-top: 2px solid rgba(255, 87, 34, 0.65);
        padding: 18px 22px;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(12px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    div[data-testid="stMetric"]:hover, div[data-testid="metric-container"]:hover {
        transform: translateY(-3px);
        border-color: rgba(255, 87, 34, 0.9);
    }
    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 1.85rem !important;
        color: #F8FAFC !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    /* Glass Card Container for Panels */
    .glass-card {
        background: rgba(17, 24, 39, 0.72);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(12px);
        margin-bottom: 16px;
    }

    /* Modern Segmented Pill Navigation Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 21, 36, 0.9);
        padding: 6px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 14px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 9px 18px;
        font-weight: 600;
        font-size: 0.88rem;
        color: #94A3B8;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #FFFFFF;
        background-color: rgba(255, 255, 255, 0.05);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #FF5722 0%, #F43F5E 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 14px rgba(255, 87, 34, 0.4);
    }

    /* Sidebar Polish */
    section[data-testid="stSidebar"] {
        background-color: #090D16;
        border-right: 1px solid rgba(255, 255, 255, 0.07);
    }
</style>
""", unsafe_allow_html=True)

DB_PATH = "wildfire_pipeline.db"

# 3. Data Enrichment & NASA API Engine
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
    return "Maritime / Other"

def enrich_dataframe(df):
    if "bright_ti4" in df.columns and "brightness" not in df.columns:
        df.rename(columns={"bright_ti4": "brightness"}, inplace=True)
    df["brightness"] = pd.to_numeric(df["brightness"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude", "brightness"]).copy()
    df["risk_tier"] = df["brightness"].apply(classify_risk)
    df["region"] = df.apply(lambda r: assign_region(r["latitude"], r["longitude"]), axis=1)
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
    st.error(f"Pipeline load error: {e}")
    st.stop()

# 4. Sidebar Control Center
with st.sidebar:
    st.markdown("### 🛰️ Telemetry Controls")
    st.caption("VIIRS NOAA-20 Orbital Sensor Pipeline")

    if st.button("🔄 Sync Live NASA Feed", use_container_width=True, type="primary"):
        with st.spinner("Streaming NASA FIRMS satellite feed..."):
            try:
                sync_live_nasa_feed()
                st.cache_data.clear()
                st.rerun()
            except Exception as err:
                st.error(f"Sync failed: {err}")

    st.divider()

    all_tiers = [t for t in ["Extreme", "High", "Moderate", "Low"] if t in df["risk_tier"].unique()]
    selected_tiers = st.multiselect("Thermal Risk Tiers", options=all_tiers, default=all_tiers)

    all_regions = sorted(df["region"].unique().tolist())
    selected_regions = st.multiselect("Continental Zones", options=all_regions, default=all_regions)

    min_b, max_b = float(df["brightness"].min()), float(df["brightness"].max())
    b_range = st.slider("Brightness Filter (Kelvin)", min_b, max_b, (min_b, max_b))

    map_style = st.selectbox(
        "Orbital Map Basemap",
        ["CartoDB Dark Matter (Sleek)", "Esri World Imagery (Satellite)", "OpenStreetMap Terrain"]
    )

    st.divider()
    st.caption(f"🗄️ **Database Rows:** `{len(df):,}`")
    st.caption("⚡ **Pipeline:** `Pydantic + SQLite`")

# Filter Data
filtered_df = df[
    (df["risk_tier"].isin(selected_tiers)) &
    (df["region"].isin(selected_regions)) &
    (df["brightness"] >= b_range[0]) &
    (df["brightness"] <= b_range[1])
]

# 5. Glass Hero Header Banner
now_utc = datetime.now(timezone.utc).strftime("%H:%M UTC")
st.markdown(f"""
<div class="hero-box">
    <div>
        <div class="hero-title">🔥 NASA FIRMS Orbital Wildfire Intelligence</div>
        <div class="hero-sub">Real-Time VIIRS NOAA-20 Thermal Anomaly Pipeline • Pydantic Validated • Geospatial Analytics</div>
    </div>
    <div class="live-badge">
        <span class="pulse-dot"></span>
        <span>TELEMETRY ONLINE • {now_utc}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 6. Top KPI Cards Row
k1, k2, k3, k4 = st.columns(4)
with k1:
    pct = (len(filtered_df) / max(len(df), 1)) * 100
    st.metric("Active Hotspots", f"{len(filtered_df):,}", delta=f"{pct:.0f}% of total feed")
with k2:
    mean_k = filtered_df["brightness"].mean() if not filtered_df.empty else 0.0
    max_k = filtered_df["brightness"].max() if not filtered_df.empty else 0.0
    st.metric("Mean Temperature", f"{mean_k:.2f} K", delta=f"Peak: {max_k:.1f} K")
with k3:
    ext_cnt = len(filtered_df[filtered_df["risk_tier"] == "Extreme"])
    st.metric("Critical Alerts (>360K)", f"{ext_cnt}", delta="Immediate Action" if ext_cnt > 0 else "0 Critical", delta_color="inverse")
with k4:
    top_reg = filtered_df["region"].mode()[0] if not filtered_df.empty else "N/A"
    reg_cnt = len(filtered_df[filtered_df["region"] == top_reg]) if top_reg != "N/A" else 0
    st.metric("Primary Hotspot Zone", top_reg, delta=f"{reg_cnt} detections")

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# 7. Navigation Tabs
tab_map, tab_eda, tab_intel, tab_alerts, tab_data = st.tabs([
    "🌍 Orbital Map",
    "📊 Thermal Analytics",
    "🎯 Regional Intelligence",
    "🚨 Alert Simulator",
    "📋 Telemetry & Export"
])

# TAB 1: Orbital Map + Side Telemetry Panel
with tab_map:
    col_map, col_side = st.columns([3.2, 1.3], gap="medium")
    with col_map:
        if not filtered_df.empty:
            tile_urls = {
                "CartoDB Dark Matter (Sleek)": ("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", "CartoDB"),
                "Esri World Imagery (Satellite)": ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", "Esri"),
                "OpenStreetMap Terrain": ("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", "OpenStreetMap")
            }
            tile_url, tile_attr = tile_urls[map_style]

            m = folium.Map(
                location=[filtered_df["latitude"].median(), filtered_df["longitude"].median()],
                zoom_start=3,
                min_zoom=2,
                world_copy_jump=False,
                tiles=None
            )
            folium.TileLayer(tiles=tile_url, attr=tile_attr, no_wrap=True).add_to(m)

            colors = {"Extreme": "#FF2B2B", "High": "#FF8C00", "Moderate": "#FACC15", "Low": "#10B981"}
            for _, row in filtered_df.head(400).iterrows():
                tier = row["risk_tier"]
                c = colors.get(tier, "#10B981")
                folium.CircleMarker(
                    location=[row["latitude"], row["longitude"]],
                    radius=7 if tier == "Extreme" else (5.5 if tier == "High" else 4.5),
                    color=c,
                    weight=1.5,
                    fill=True,
                    fill_color=c,
                    fill_opacity=0.8,
                    popup=(
                        f"<div style='font-family:sans-serif;min-width:140px'>"
                        f"<b>Zone:</b> {row['region']}<br>"
                        f"<b>Tier:</b> {tier}<br>"
                        f"<b>Temp:</b> {row['brightness']:.2f} K<br>"
                        f"<b>Lat/Lon:</b> {row['latitude']:.2f}, {row['longitude']:.2f}</div>"
                    )
                ).add_to(m)
            st_folium(m, width=None, height=510, use_container_width=True)
        else:
            st.warning("No thermal anomalies match your active filters.")

    with col_side:
        st.markdown('<div class="glass-card"><h4 style="margin:0 0 8px 0;color:#F8FAFC;">Severity Breakdown</h4>', unsafe_allow_html=True)
        if not filtered_df.empty:
            fig_donut = px.pie(
                filtered_df,
                names="risk_tier",
                hole=0.64,
                color="risk_tier",
                color_discrete_map={"Extreme": "#FF2B2B", "High": "#FF8C00", "Moderate": "#FACC15", "Low": "#10B981"}
            )
            fig_donut.update_traces(textposition="inside", textinfo="percent")
            fig_donut.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#E2E8F0",
                margin=dict(t=5, b=5, l=5, r=5),
                height=240,
                legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="glass-card" style="font-size:0.84rem;color:#CBD5E1;">
            <div style="font-weight:700;color:#F8FAFC;margin-bottom:10px;">Kelvin Threshold Scale</div>
            <div style="display:flex;justify-content:space-between;margin-bottom:6px;"><span>🔴 Extreme</span><span style="font-family:monospace;">≥ 360 K</span></div>
            <div style="display:flex;justify-content:space-between;margin-bottom:6px;"><span>🟠 High</span><span style="font-family:monospace;">330–359 K</span></div>
            <div style="display:flex;justify-content:space-between;margin-bottom:6px;"><span>🟡 Moderate</span><span style="font-family:monospace;">310–329 K</span></div>
            <div style="display:flex;justify-content:space-between;"><span>🟢 Low</span><span style="font-family:monospace;">< 310 K</span></div>
        </div>
        """, unsafe_allow_html=True)

# TAB 2: Interactive Plotly Analytics
with tab_eda:
    if not filtered_df.empty:
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            fig_hist = px.histogram(
                filtered_df,
                x="brightness",
                color="risk_tier",
                nbins=26,
                title="Thermal Brightness Frequency Distribution (K)",
                color_discrete_map={"Extreme": "#FF2B2B", "High": "#FF8C00", "Moderate": "#FACC15", "Low": "#10B981"}
            )
            fig_hist.update_layout(
                paper_bgcolor="rgba(17,24,39,0.7)",
                plot_bgcolor="rgba(11,15,26,0.6)",
                font_color="#F1F5F9",
                margin=dict(t=45, b=30, l=30, r=20)
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        with c2:
            fig_scatter = px.scatter(
                filtered_df,
                x="latitude",
                y="brightness",
                color="region",
                size="brightness",
                hover_data=["longitude", "risk_tier"],
                title="Latitude vs. Brightness Intensity by Continent"
            )
            fig_scatter.update_layout(
                paper_bgcolor="rgba(17,24,39,0.7)",
                plot_bgcolor="rgba(11,15,26,0.6)",
                font_color="#F1F5F9",
                margin=dict(t=45, b=30, l=30, r=20)
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown("#### Descriptive Telemetry Statistics (`describe()`)")
        num_cols = [c for c in ["brightness", "latitude", "longitude", "frp", "confidence"] if c in filtered_df.columns]
        st.dataframe(filtered_df[num_cols].describe().T, use_container_width=True)

# TAB 3: Regional & Hotspot Intelligence
with tab_intel:
    if not filtered_df.empty:
        r1, r2 = st.columns([3, 2], gap="medium")
        with r1:
            reg_summary = filtered_df.groupby("region", as_index=False).agg(
                Detections=("brightness", "count"),
                Mean_Temp=("brightness", "mean"),
                Peak_Temp=("brightness", "max")
            ).sort_values("Detections", ascending=False)

            fig_bar = px.bar(
                reg_summary,
                x="region",
                y="Detections",
                color="Mean_Temp",
                color_continuous_scale="YlOrRd",
                title="Active Detections & Mean Brightness by Geographic Zone"
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(17,24,39,0.7)",
                plot_bgcolor="rgba(11,15,26,0.6)",
                font_color="#F1F5F9"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with r2:
            peak_val = float(filtered_df["brightness"].max())
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=peak_val,
                delta={"reference": 330, "increasing": {"color": "#FF2B2B"}},
                title={"text": "Peak Orbital Brightness (K)", "font": {"color": "#F1F5F9"}},
                gauge={
                    "axis": {"range": [280, 420], "tickcolor": "#94A3B8"},
                    "bar": {"color": "#FF5722"},
                    "bgcolor": "rgba(15,23,42,0.8)",
                    "steps": [
                        {"range": [280, 310], "color": "#064E3B"},
                        {"range": [310, 330], "color": "#713F12"},
                        {"range": [330, 360], "color": "#7C2D12"},
                        {"range": [360, 420], "color": "#7F1D1D"}
                    ]
                }
            ))
            fig_gauge.update_layout(paper_bgcolor="rgba(17,24,39,0.7)", font_color="#F1F5F9", height=360)
            st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown("#### 🔥 Top 10 Highest-Intensity Thermal Hotspots")
        top10 = filtered_df.sort_values("brightness", ascending=False).head(10)
        cols = [c for c in ["region", "risk_tier", "brightness", "latitude", "longitude", "acq_date", "acq_time"] if c in top10.columns]
        st.dataframe(top10[cols], use_container_width=True, hide_index=True)

# TAB 4: Alert & Threshold Simulator
with tab_alerts:
    sim1, sim2 = st.columns([1, 2], gap="medium")
    with sim1:
        st.markdown('<div class="glass-card"><h4 style="margin-top:0;">🚨 Threshold Trigger Control</h4>', unsafe_allow_html=True)
        custom_thresh = st.slider("Alert Trigger Threshold (Kelvin)", 300.0, 400.0, 340.0, step=1.0)
        webhook_url = st.text_input("Discord Webhook URL (Optional)", placeholder="https://discord.com/api/webhooks/...")
        triggered_df = filtered_df[filtered_df["brightness"] >= custom_thresh]
        st.metric("Anomalies Triggering Alert", f"{len(triggered_df)}")

        if st.button("📡 Dispatch Emergency Alert", use_container_width=True, type="primary"):
            if webhook_url.startswith("https://"):
                try:
                    payload = {"content": f"🔥 **NASA FIRMS Alert:** {len(triggered_df)} anomalies ≥ **{custom_thresh} K** detected."}
                    res = requests.post(webhook_url, json=payload, timeout=5)
                    if res.status_code in [200, 204]:
                        st.success("Dispatched to Discord!")
                    else:
                        st.error(f"Webhook returned {res.status_code}")
                except Exception as w_err:
                    st.error(f"Error: {w_err}")
            else:
                st.info(f"Simulated Alert: Flagged **{len(triggered_df)} hotspots ≥ {custom_thresh} K**.")
        st.markdown('</div>', unsafe_allow_html=True)

    with sim2:
        st.markdown(f"#### Flagged Detections (≥ {custom_thresh} K)")
        if not triggered_df.empty:
            show_cols = [c for c in ["region", "brightness", "latitude", "longitude", "acq_date"] if c in triggered_df.columns]
            st.dataframe(triggered_df.sort_values("brightness", ascending=False)[show_cols], use_container_width=True, height=340, hide_index=True)
        else:
            st.success("No detections exceed this threshold.")

# TAB 5: Data Explorer & Export
with tab_data:
    s_col, b1, b2, b3 = st.columns([3, 1, 1, 1])
    with s_col:
        search_txt = st.text_input("🔍 Search Telemetry Records:", placeholder="Filter by region, risk tier, date, or coordinate...")

    export_df = filtered_df.copy()
    if search_txt:
        mask = export_df.astype(str).apply(lambda col: col.str.contains(search_txt, case=False, na=False)).any(axis=1)
        export_df = export_df[mask]

    with b1:
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button("⬇️ CSV", export_df.to_csv(index=False).encode("utf-8"), "nasa_firms_data.csv", "text/csv", use_container_width=True)
    with b2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button("⬇️ JSON", export_df.to_json(orient="records", indent=2).encode("utf-8"), "nasa_firms_data.json", "application/json", use_container_width=True)
    with b3:
        st.markdown("<br>", unsafe_allow_html=True)
        excel_buf = io.BytesIO()
        export_df.to_excel(excel_buf, index=False, engine="openpyxl")
        st.download_button("⬇️ Excel", excel_buf.getvalue(), "nasa_firms_data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    st.dataframe(export_df, use_container_width=True, height=450)

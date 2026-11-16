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

# 1. Page Setup
st.set_page_config(
    page_title="NASA FIRMS | Wildfire Intelligence Command",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom Glassmorphism & Executive UI Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 1.4rem; padding-bottom: 2rem; }

    /* Styled KPI Cards */
    div[data-testid="metric-container"] {
        background: linear-gradient(145deg, #131A2A 0%, #0F1523 100%);
        border: 1px solid rgba(255, 87, 34, 0.28);
        padding: 16px 20px;
        border-radius: 14px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
        transition: all 0.2s ease;
    }
    div[data-testid="metric-container"]:hover {
        border-color: #FF5722;
        transform: translateY(-2px);
    }

    /* Modern Pill Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #131A2A;
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        color: #94A3B8;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #FF5722 0%, #E91E63 100%) !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

DB_PATH = "wildfire_pipeline.db"

# 3. Helper Enrichment Functions
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
    return "Other / Maritime"

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

# 4. Sidebar Controls
with st.sidebar:
    st.markdown("### 🛰️ Satellite Telemetry Hub")
    st.caption("VIIRS NOAA-20 Global Thermal Anomaly Pipeline")

    if st.button("🔄 Sync Live NASA Satellite Data", use_container_width=True, type="primary"):
        with st.spinner("Ingesting & validating NASA FIRMS feed..."):
            try:
                sync_live_nasa_feed()
                st.cache_data.clear()
                st.rerun()
            except Exception as err:
                st.error(f"API Sync Error: {err}")

    st.divider()

    # Multi-select filters for deeper exploration
    all_tiers = [t for t in ["Extreme", "High", "Moderate", "Low"] if t in df["risk_tier"].unique()]
    selected_tiers = st.multiselect("Filter Risk Tiers", options=all_tiers, default=all_tiers)

    all_regions = sorted(df["region"].unique().tolist())
    selected_regions = st.multiselect("Filter Global Regions", options=all_regions, default=all_regions)

    min_b, max_b = float(df["brightness"].min()), float(df["brightness"].max())
    b_range = st.slider("Brightness Threshold (K)", min_b, max_b, (min_b, max_b))

    map_style = st.selectbox(
        "Satellite Map Layer",
        ["Esri World Imagery (Satellite)", "CartoDB Dark Matter", "OpenStreetMap Terrain"]
    )

    st.divider()
    st.caption(f"🗄️ **SQLite Records:** `{len(df):,}`")
    st.caption(f"🕒 **Updated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

# Apply Filters
filtered_df = df[
    (df["risk_tier"].isin(selected_tiers)) &
    (df["region"].isin(selected_regions)) &
    (df["brightness"] >= b_range[0]) &
    (df["brightness"] <= b_range[1])
]

# 5. Header Banner
st.markdown("## 🔥 NASA FIRMS Global Wildfire Intelligence")
st.caption("Real-Time Satellite ETL • Pydantic Schema Validation • Geospatial & Statistical Analytics")

# 6. Top Row: 4 Executive KPI Cards
k1, k2, k3, k4 = st.columns(4)
with k1:
    pct = (len(filtered_df) / max(len(df), 1)) * 100
    st.metric("Active Detections", f"{len(filtered_df):,}", delta=f"{pct:.0f}% of dataset")
with k2:
    mean_k = filtered_df["brightness"].mean() if not filtered_df.empty else 0.0
    max_k = filtered_df["brightness"].max() if not filtered_df.empty else 0.0
    st.metric("Mean Brightness", f"{mean_k:.2f} K", delta=f"Max: {max_k:.1f} K")
with k3:
    ext_cnt = len(filtered_df[filtered_df["risk_tier"] == "Extreme"])
    st.metric("Extreme Risk (>360K)", f"{ext_cnt}", delta="Critical Alert" if ext_cnt > 0 else "Nominal", delta_color="inverse")
with k4:
    top_reg = filtered_df["region"].mode()[0] if not filtered_df.empty else "N/A"
    st.metric("Most Active Region", top_reg, delta=f"{len(filtered_df[filtered_df['region']==top_reg])} hotspots" if top_reg != "N/A" else "")

st.markdown("<br>", unsafe_allow_html=True)

# 7. 5-Tab Workspace
tab_map, tab_eda, tab_intel, tab_alerts, tab_data = st.tabs([
    "🌍 Live Satellite Map",
    "📊 Interactive EDA",
    "🎯 Regional & Hotspot Intel",
    "🚨 Alert Simulator",
    "📋 Data & Export"
])

# TAB 1: Geospatial Satellite Map
with tab_map:
    col_map, col_side = st.columns([3, 1])
    with col_map:
        if not filtered_df.empty:
            tile_urls = {
                "Esri World Imagery (Satellite)": ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", "Esri"),
                "CartoDB Dark Matter": ("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", "CartoDB"),
                "OpenStreetMap Terrain": ("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", "OpenStreetMap")
            }
            tile_url, tile_attr = tile_urls[map_style]

            m = folium.Map(
                location=[filtered_df["latitude"].mean(), filtered_df["longitude"].mean()],
                zoom_start=2,
                tiles=tile_url,
                attr=tile_attr
            )
            colors = {"Extreme": "#FF2B2B", "High": "#FF8C00", "Moderate": "#FFD700", "Low": "#00E676"}
            for _, row in filtered_df.head(400).iterrows():
                tier = row["risk_tier"]
                folium.CircleMarker(
                    location=[row["latitude"], row["longitude"]],
                    radius=7 if tier == "Extreme" else (5 if tier == "High" else 4),
                    color=colors.get(tier, "#00E676"),
                    fill=True,
                    fill_opacity=0.85,
                    popup=(
                        f"<b>Region:</b> {row['region']}<br>"
                        f"<b>Risk Tier:</b> {tier}<br>"
                        f"<b>Brightness:</b> {row['brightness']:.2f} K<br>"
                        f"<b>Coords:</b> {row['latitude']:.3f}, {row['longitude']:.3f}"
                    )
                ).add_to(m)
            st_folium(m, width=None, height=500, use_container_width=True)
        else:
            st.warning("No thermal anomalies match the selected filters.")

    with col_side:
        st.markdown("#### Risk Distribution")
        if not filtered_df.empty:
            fig_donut = px.pie(
                filtered_df,
                names="risk_tier",
                hole=0.58,
                color="risk_tier",
                color_discrete_map={"Extreme": "#FF2B2B", "High": "#FF8C00", "Moderate": "#FFD700", "Low": "#00E676"}
            )
            fig_donut.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#F1F5F9",
                margin=dict(t=10, b=10, l=10, r=10),
                height=260
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        st.info("**Kelvin Risk Thresholds:**\n- 🔴 **Extreme:** ≥ 360 K\n- 🟠 **High:** 330 – 359 K\n- 🟡 **Moderate:** 310 – 329 K\n- 🟢 **Low:** < 310 K")

# TAB 2: Interactive Plotly EDA
with tab_eda:
    if not filtered_df.empty:
        c1, c2 = st.columns(2)
        with c1:
            fig_hist = px.histogram(
                filtered_df,
                x="brightness",
                color="risk_tier",
                nbins=28,
                title="Thermal Brightness Distribution (Kelvin)",
                color_discrete_map={"Extreme": "#FF2B2B", "High": "#FF8C00", "Moderate": "#FFD700", "Low": "#00E676"}
            )
            fig_hist.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(19,26,42,0.6)", font_color="#F1F5F9")
            st.plotly_chart(fig_hist, use_container_width=True)

        with c2:
            fig_scatter = px.scatter(
                filtered_df,
                x="latitude",
                y="brightness",
                color="region",
                size="brightness",
                hover_data=["longitude", "risk_tier"],
                title="Latitude vs. Thermal Intensity by Global Region"
            )
            fig_scatter.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(19,26,42,0.6)", font_color="#F1F5F9")
            st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown("#### Statistical Summary (`describe()`)")
        num_cols = [c for c in ["brightness", "latitude", "longitude", "frp", "confidence"] if c in filtered_df.columns]
        st.dataframe(filtered_df[num_cols].describe().T, use_container_width=True)
    else:
        st.warning("No data available to plot.")

# TAB 3: Regional & Hotspot Intelligence
with tab_intel:
    if not filtered_df.empty:
        r_col1, r_col2 = st.columns([3, 2])
        with r_col1:
            reg_summary = filtered_df.groupby("region", as_index=False).agg(
                Detections=("brightness", "count"),
                Avg_Brightness=("brightness", "mean"),
                Peak_Brightness=("brightness", "max")
            ).sort_values("Detections", ascending=False)

            fig_bar = px.bar(
                reg_summary,
                x="region",
                y="Detections",
                color="Avg_Brightness",
                color_continuous_scale="YlOrRd",
                title="Active Thermal Detections & Mean Intensity by Region"
            )
            fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(19,26,42,0.6)", font_color="#F1F5F9")
            st.plotly_chart(fig_bar, use_container_width=True)

        with r_col2:
            peak_val = float(filtered_df["brightness"].max())
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=peak_val,
                delta={"reference": 330, "increasing": {"color": "#FF2B2B"}},
                title={"text": "Peak Thermal Anomaly (K)"},
                gauge={
                    "axis": {"range": [280, 420]},
                    "bar": {"color": "#FF5722"},
                    "steps": [
                        {"range": [280, 310], "color": "#1E293B"},
                        {"range": [310, 330], "color": "#334155"},
                        {"range": [330, 360], "color": "#7C2D12"},
                        {"range": [360, 420], "color": "#991B1B"}
                    ]
                }
            ))
            fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#F1F5F9", height=320)
            st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown("#### 🔥 Top 10 Highest-Intensity Thermal Hotspots")
        top10 = filtered_df.sort_values("brightness", ascending=False).head(10)
        cols = [c for c in ["region", "risk_tier", "brightness", "latitude", "longitude", "acq_date", "acq_time"] if c in top10.columns]
        st.dataframe(top10[cols], use_container_width=True, hide_index=True)

# TAB 4: Alert & Threshold Simulator
with tab_alerts:
    st.markdown("#### 🚨 Automated Emergency Alert Simulator")
    st.caption("Test custom Kelvin trigger thresholds and dispatch real-time webhook notifications.")

    sim_col1, sim_col2 = st.columns([1, 2])
    with sim_col1:
        custom_thresh = st.slider("Custom Alert Trigger (Kelvin)", 300.0, 400.0, 345.0, step=1.0)
        webhook_url = st.text_input("Discord Webhook URL (Optional)", placeholder="https://discord.com/api/webhooks/...")
        triggered_df = filtered_df[filtered_df["brightness"] >= custom_thresh]
        st.metric("Detections Exceeding Threshold", f"{len(triggered_df)}")

        if st.button("📡 Dispatch Test Alert", use_container_width=True):
            if webhook_url.startswith("https://"):
                try:
                    payload = {
                        "content": f"🔥 **NASA FIRMS Alert:** {len(triggered_df)} thermal anomalies detected above **{custom_thresh} K** (Peak: {triggered_df['brightness'].max():.1f} K)."
                    }
                    res = requests.post(webhook_url, json=payload, timeout=5)
                    if res.status_code in [200, 204]:
                        st.success("Alert dispatched to Discord successfully!")
                    else:
                        st.error(f"Webhook returned status {res.status_code}")
                except Exception as w_err:
                    st.error(f"Webhook error: {w_err}")
            else:
                st.info(f"Simulated Alert Preview: **{len(triggered_df)} anomalies ≥ {custom_thresh} K** flagged for immediate response.")

    with sim_col2:
        st.markdown(f"**Flagged Hotspots (≥ {custom_thresh} K):**")
        if not triggered_df.empty:
            show_cols = [c for c in ["region", "brightness", "latitude", "longitude", "acq_date"] if c in triggered_df.columns]
            st.dataframe(triggered_df.sort_values("brightness", ascending=False)[show_cols], use_container_width=True, height=300, hide_index=True)
        else:
            st.success("No detections exceed this threshold.")

# TAB 5: Data Explorer & Multi-Format Export
with tab_data:
    s_col, b1, b2, b3 = st.columns([3, 1, 1, 1])
    with s_col:
        search_txt = st.text_input("🔍 Instant Search (Region, Risk Tier, Date, or Coordinate):", placeholder="e.g. Asia or High")

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

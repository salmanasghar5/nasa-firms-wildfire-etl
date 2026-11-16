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

    /* Fixed KPI Metric Cards (Targets both old & new Streamlit DOM classes) */
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
    st.caption(f"⚡ **Pipeline:** `Pydantic + SQLite`")

# Filter Data
filtered_df = df[
    (df["risk_tier"].isin(selected_tiers)) &
    (df["region"].isin(selected_regions)) &
    (df["brightness"] >= b_range[0]) &
    (df["brightness"] <= b_range[1])
]

# 5. Glass Hero Header Banner
now_utc = datetime.now(timezone

import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import seaborn as sns
import io

# 1. Force full-screen wide layout & clean page title
st.set_page_config(
    page_title="NASA FIRMS Wildfire Intelligence",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS for clean dark/modern KPI cards and spacing
st.markdown("""
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    div[data-testid="metric-container"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        padding: 16px 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# 3. Load Data & Automatically Detect Table Name from SQLite Database
@st.cache_data
def load_data():
    conn = sqlite3.connect("wildfire_pipeline.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    if not tables:
        conn.close()
        raise Exception("No tables found in SQLite database.")
    table_name = tables[0][0]  # Automatically picks the first table found
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Database load error: {e}")
    st.stop()

# 4. Sidebar Controls
with st.sidebar:
    st.header("🎛️ Pipeline Controls")
    st.markdown("Filter global satellite thermal detections by risk severity.")
    
    available_tiers = ["All"] + sorted(df["risk_tier"].dropna().unique().tolist()) if "risk_tier" in df.columns else ["All"]
    selected_tier = st.selectbox("Select Risk Tier", available_tiers, index=0)
    
    if "brightness" in df.columns:
        min_brightness = float(df["brightness"].min())
        max_brightness = float(df["brightness"].max())
        brightness_range = st.slider(
            "Brightness Threshold (Kelvin)",
            min_value=min_brightness,
            max_value=max_brightness,
            value=(min_brightness, max_brightness)
        )
    else:
        brightness_range = (0.0, 500.0)
    
    st.divider()
    st.caption("📡 **Data Source:** NASA FIRMS VIIRS NOAA-20")
    st.caption("🗄️ **Storage:** Validated SQLite DB")

# Apply filters safely
filtered_df = df.copy()
if "brightness" in filtered_df.columns:
    filtered_df = filtered_df[
        (filtered_df["brightness"] >= brightness_range[0]) &
        (filtered_df["brightness"] <= brightness_range[1])
    ]
if selected_tier != "All" and "risk_tier" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["risk_tier"] == selected_tier]

# 5. Header Section
st.title("🔥 NASA FIRMS Real-Time Wildfire Intelligence")
st.markdown("Automated ETL & Exploratory Data Analysis pipeline monitoring global thermal anomalies.")

# 6. Top Row: 4 Clean Styled KPI Cards
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Total Detections", f"{len(filtered_df):,}")
with kpi2:
    avg_b = filtered_df["brightness"].mean() if not filtered_df.empty and "brightness" in filtered_df.columns else 0
    st.metric("Mean Brightness", f"{avg_b:.2f} K")
with kpi3:
    extreme_cnt = len(filtered_df[filtered_df["risk_tier"] == "Extreme"]) if "risk_tier" in filtered_df.columns else 0
    st.metric("Extreme Risk Alerts", f"{extreme_cnt}")
with kpi4:
    high_cnt = len(filtered_df[filtered_df["risk_tier"] == "High"]) if "risk_tier" in filtered_df.columns else 0
    st.metric("High Risk Anomalies", f"{high_cnt}")

st.markdown("---")

# 7. Organized Tabbed Workspace
tab_map, tab_eda, tab_data = st.tabs([
    "🌍 Geospatial Satellite Map",
    "📊 Statistical EDA Plots",
    "📋 Telemetry Records & Export"
])

# TAB 1: Map
with tab_map:
    map_col, summary_col = st.columns([3, 1])
    
    with map_col:
        st.subheader("Esri Satellite Thermal Overlay")
        if not filtered_df.empty and "latitude" in filtered_df.columns and "longitude" in filtered_df.columns:
            center_lat = filtered_df["latitude"].mean()
            center_lon = filtered_df["longitude"].mean()
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=3,
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri"
            )
            color_map = {"Extreme": "#ff2b2b", "High": "#ff8c00", "Moderate": "#ffd700", "Low": "#00cc66"}
            
            for _, row in filtered_df.head(300).iterrows():
                tier = row.get("risk_tier", "Low")
                folium.CircleMarker(
                    location=[row["latitude"], row["longitude"]],
                    radius=6,
                    color=color_map.get(tier, "#00cc66"),
                    fill=True,
                    fill_opacity=0.85,
                    popup=f"<b>Tier:</b> {tier}<br><b>Brightness:</b> {row.get('brightness', 'N/A')} K<br><b>Date:</b> {row.get('acq_date', 'N/A')}"
                ).add_to(m)
            
            st_folium(m, width=None, height=480, use_container_width=True)
        else:
            st.warning("No geographic coordinates found to render map.")

    with summary_col:
        st.subheader("Risk Breakdown")
        if "risk_tier" in filtered_df.columns:
            tier_counts = filtered_df["risk_tier"].value_counts().reset_index()
            tier_counts.columns = ["Risk Tier", "Count"]
            st.dataframe(tier_counts, use_container_width=True, hide_index=True)
        else:
            st.info("No risk tier column found.")
        
        st.info(
            "**Legend:**\n"
            "- 🔴 **Extreme:** > 360 K\n"
            "- 🟠 **High:** 330 – 360 K\n"
            "- 🟡 **Moderate:** 310 – 330 K\n"
            "- 🟢 **Low:** < 310 K"
        )

# TAB 2: EDA Plots
with tab_eda:
    st.subheader("Exploratory Data Analysis (EDA)")
    if not filtered_df.empty and "brightness" in filtered_df.columns:
        plt.style.use("dark_background")
        fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))
        fig.patch.set_facecolor("#0E1117")
        
        # Chart 1
        sns.histplot(filtered_df["brightness"], bins=20, kde=True, color="#ff6b6b", ax=axes[0])
        axes[0].set_title("Brightness Temperature Distribution", fontsize=11, fontweight="bold")
        axes[0].set_facecolor("#161B22")
        
        # Chart 2
        if "risk_tier" in filtered_df.columns:
            order = [t for t in ["Extreme", "High", "Moderate", "Low"] if t in filtered_df["risk_tier"].unique()]
            sns.countplot(data=filtered_df, x="risk_tier", order=order, hue="risk_tier", palette="rocket", legend=False, ax=axes[1])
        axes[1].set_title("Detections by Risk Tier", fontsize=11, fontweight="bold")
        axes[1].set_facecolor("#161B22")
        
        # Chart 3
        if "latitude" in filtered_df.columns:
            sns.scatterplot(data=filtered_df, x="latitude", y="brightness", hue="risk_tier" if "risk_tier" in filtered_df.columns else None, palette="viridis", ax=axes[2])
        axes[2].set_title("Brightness vs. Latitude Correlation", fontsize=11, fontweight="bold")
        axes[2].set_facecolor("#161B22")
        
        plt.tight_layout()
        st.pyplot(fig)
        
        st.subheader("Statistical Summary (`describe()`)")
        numeric_cols = [c for c in ["brightness", "latitude", "longitude"] if c in filtered_df.columns]
        if numeric_cols:
            st.dataframe(filtered_df[numeric_cols].describe().T, use_container_width=True)
    else:
        st.warning("No numeric data available to plot.")

# TAB 3: Data Table & Downloads
with tab_data:
    st.subheader("Validated SQLite Telemetry Records")
    
    dl1, dl2, _ = st.columns([1, 1, 4])
    with dl1:
        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", data=csv_data, file_name="wildfire_telemetry.csv", mime="text/csv", use_container_width=True)
    with dl2:
        json_data = filtered_df.to_json(orient="records", indent=2).encode("utf-8")
        st.download_button("⬇️ Download JSON", data=json_data, file_name="wildfire_telemetry.json", mime="application/json", use_container_width=True)
        
    st.dataframe(filtered_df, use_container_width=True, height=450)

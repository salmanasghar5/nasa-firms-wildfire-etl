import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Set professional seaborn theme
sns.set_theme(style="whitegrid")

st.set_page_config(
    page_title="NASA FIRMS Wildfire Monitoring Dashboard",
    page_icon="🔥",
    layout="wide"
)

st.title("🔥 NASA FIRMS Real-Time Global Wildfire Monitoring Dashboard")
st.markdown("Production-grade data engineering pipeline tracking thermal anomalies, risk tiers, and telemetry.")

# --- LOAD DATA FROM SQLITE DATABASE ---
@st.cache_data
def load_data():
    if not os.path.exists("wildfire_pipeline.db"):
        return pd.DataFrame()
    conn = sqlite3.connect("wildfire_pipeline.db")
    df = pd.read_sql("SELECT * FROM wildfire_events", conn)
    conn.close()
    return df

df = load_data()

if df.empty:
    st.warning("⚠️ No wildfire data found in 'wildfire_pipeline.db'. Please run your master pipeline cell first to populate the database!")
else:
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Dashboard Controls")
    selected_risk = st.sidebar.selectbox(
        "Filter by Risk Tier",
        ["All", "Extreme", "High", "Moderate", "Low"]
    )

    if selected_risk != "All":
        filtered_df = df[df['risk_tier'] == selected_risk]
    else:
        filtered_df = df

    # --- TOP METRICS ROW ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Records Processed", len(df))
    col2.metric("Average Brightness", f"{round(df['brightness'].mean(), 2)} K")
    col3.metric("Extreme Risk Count", len(df[df['risk_tier'] == 'Extreme']))
    col4.metric("High Risk Count", len(df[df['risk_tier'] == 'High']))

    st.markdown("----")

    # --- MAP & DATA TABLE LAYOUT ---
    map_col, table_col = st.columns([1.2, 1])

    with map_col:
        st.subheader("🌍 Geospatial Satellite Map (Esri Imagery)")
        map_center = [filtered_df['latitude'].mean(), filtered_df['longitude'].mean()] if not filtered_df.empty else [0, 0]
        live_map = folium.Map(location=map_center, zoom_start=3, tiles='esri.worldimagery')

        for _, row in filtered_df.iterrows():
            tier = row['risk_tier']
            color = "red" if tier == "Extreme" else "orange" if tier == "High" else "yellow" if tier == "Moderate" else "green"

            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=6,
                popup=f"Risk: {tier}<br>Brightness: {row['brightness']}<br>Date: {row['acq_date']}",
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8
            ).add_to(live_map)

        st_folium(live_map, width=650, height=450)

    with table_col:
        st.subheader("📊 Filtered Telemetry Records")
        st.dataframe(filtered_df[['latitude', 'longitude', 'brightness', 'risk_tier', 'acq_date']], height=450)

    # --- EXPLORATORY DATA ANALYSIS (EDA) CHARTS SECTION ---
    st.markdown("----")
    st.subheader("📈 Statistical EDA & Visual Reports")
    st.markdown("Academic visualizations analyzing brightness distributions, risk categories, and geospatial correlations.")

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # --- Chart 1: Brightness Temperature Distribution ---
    sns.histplot(df['brightness'], kde=True, ax=axes[0], color='crimson')
    axes[0].set_title("Brightness Temperature Distribution")
    axes[0].set_xlabel("Brightness (Kelvin)")
    axes[0].set_ylabel("Frequency")

    # --- Chart 2: Wildfire Count by Risk Tier ---
    risk_order = ['Extreme', 'High', 'Moderate', 'Low']
    sns.countplot(x='risk_tier', data=df, ax=axes[1], order=[r for r in risk_order if r in df['risk_tier'].unique()], palette='rocket')
    axes[1].set_title("Thermal Anomalies by Risk Tier")
    axes[1].set_xlabel("Risk Tier")
    axes[1].set_ylabel("Record Count")

    # --- Chart 3: Brightness vs. Latitude Correlation Scatter Plot ---
    if 'latitude' in df.columns and 'brightness' in df.columns:
        sns.scatterplot(x='latitude', y='brightness', hue='risk_tier', data=df, ax=axes[2], palette='deep')
        axes[2].set_title("Brightness vs. Latitude Correlation")
        axes[2].set_xlabel("Latitude (°)")
        axes[2].set_ylabel("Brightness (Kelvin)")
    else:
        axes[2].text(0.5, 0.5, "Data Unavailable", horizontalalignment='center', verticalalignment='center')
        axes[2].set_title("Correlation Plot Unavailable")

    plt.tight_layout()
    st.pyplot(fig)

    # --- DOWNLOAD SECTION ---
    st.markdown("----")
    st.subheader("📥 Export & Reports")

    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Full Dataset as CSV",
            data=csv_data,
            file_name="wildfire_export.csv",
            mime="text/csv"
        )

    with col_dl2:
        report_summary = {
            "total_records": len(df),
            "average_brightness": round(df['brightness'].mean(), 2),
            "risk_breakdown": df['risk_tier'].value_counts().to_dict()
        }
        json_data = json.dumps(report_summary, indent=4)
        st.download_button(
            label="Download Summary Report as JSON",
            data=json_data,
            file_name="wildfire_report.json",
            mime="application/json"
        )

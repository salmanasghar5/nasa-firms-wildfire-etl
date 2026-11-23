# NASA FIRMS Wildfire ETL & Orbital Control Intelligence

An end-to-end geospatial data engineering and monitoring pipeline for **NASA FIRMS (VIIRS NOAA-20 Near-Real-Time)** thermal anomaly telemetry. It validates records with **Pydantic**, stores them in **SQLite**, generates **JSON / CSV / XLSX** exports, dispatches **Discord** and **ntfy.sh** alerts for extreme thermal events, and visualizes hotspots via **Streamlit + Folium** and a standalone **Leaflet + Chart.js** web dashboard.

## Project Structure

- `wildfire_etl_pipeline.ipynb` — Colab/Jupyter pipeline for ingestion, Pydantic validation, SQLite persistence, batch exports, alert dispatch, EDA charts, and Streamlit/tunnel launch.
- `app.py` — Interactive Streamlit monitoring dashboard with risk filtering, Esri satellite map, telemetry table, EDA plots, and file downloads.
- `index.html` — Standalone Orbital Control Intelligence web UI with Esri satellite maps, Chart.js analytics, CSV export, and a browser `localStorage` vault for Discord webhooks and `ntfy.sh` topics.
- `wildfire_pipeline.db` — SQLite database containing the `wildfire_events` table.

## Risk Tier Thresholds

- **Pipeline (`app.py` & notebook)**: `Extreme` (`> 350 K`), `High` (`> 325 K`), `Moderate` (`> 300 K`), `Low` (`<= 300 K`).
- **Web Dashboard (`index.html`)**: `Extreme` (`>= 360 K`), `High` (`>= 330 K`), `Moderate` (`>= 310 K`), `Low` (`< 310 K`).

## Running Locally

### Streamlit Dashboard
```bash
pip install streamlit streamlit-folium pandas folium requests pydantic openpyxl matplotlib seaborn
streamlit run app.py

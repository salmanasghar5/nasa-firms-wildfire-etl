# NASA FIRMS Wildfire ETL & Orbital Control Intelligence

An end-to-end geospatial data engineering and wildfire monitoring system built on **NASA FIRMS** (Fire Information for Resource Management System) near-real-time satellite thermal anomaly telemetry (`VIIRS_SNPP_NRT`, `VIIRS_NOAA20_NRT`, `VIIRS_NOAA21_NRT`, and `MODIS_NRT`). The pipeline validates and stores records in **SQLite**, serves live telemetry and risk classifications through **Vercel Serverless Functions**, dispatches automated and manual **Discord** alerts, and visualizes global hotspots in an interactive **Leaflet + Chart.js** web dashboard.

## Project Structure

- `Nasa_WildFire.ipynb` — Python/Jupyter ETL pipeline for NASA FIRMS data ingestion, schema validation, SQLite persistence, and batch exports (JSON / CSV / XLSX).
- `wildfire_pipeline.db` — SQLite database storing validated wildfire detection records.
- `index.html` — Interactive Orbital Control Intelligence web dashboard featuring Esri satellite maps, Leaflet hotspot visualization, Chart.js analytics, filtering, and manual/automatic alert controls.
- `api/firms.js` — Vercel serverless endpoint that fetches multi-sensor NASA FIRMS CSV telemetry, parses and validates coordinates, classifies FRP risk tiers, caches responses, and returns structured JSON.
- `api/satellites.js` — Vercel serverless endpoint that streams live `VIIRS_NOAA20_NRT` CSV telemetry from NASA FIRMS.
- `api/alert.js` — Vercel serverless endpoint that sends validated manual and automatic wildfire alerts to Discord with origin verification, payload sanitization, and cooldown rate-limiting.

## Risk Tier Thresholds

Fire risk severity is classified in `api/firms.js` using **Fire Radiative Power (FRP)** measured in megawatts (MW):

- **Extreme:** `FRP >= 100 MW`
- **High:** `30 MW <= FRP < 100 MW`
- **Moderate:** `10 MW <= FRP < 30 MW`
- **Low:** `FRP < 10 MW`

## Deployment & Environment Variables (Vercel)

All sensitive credentials are stored server-side in **Vercel Environment Variables** and accessed via `process.env` inside `api/`:

- `FIRMS_MAP_KEY` — NASA FIRMS API map key used by `api/firms.js` and `api/satellites.js`.
- `DISCORD_WEBHOOK_URL` — Discord channel webhook URL used by `api/alert.js`.

### API Endpoints

- `GET /api/firms?source=VIIRS_SNPP_NRT&days=1` — Returns validated JSON detections with FRP risk classifications.
- `GET /api/satellites` — Returns raw `VIIRS_NOAA20_NRT` CSV telemetry.
- `POST /api/alert` — Dispatches manual or automatic high/extreme-risk alerts to Discord.

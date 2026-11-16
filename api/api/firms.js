
export default async function handler(req, res) {
  res.setHeader("Cache-Control", "s-maxage=240, stale-while-revalidate=60");

  if (req.method !== "GET") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const key = process.env.NASA_FIRMS_MAP_KEY;

  if (!key) {
    return res.status(500).json({
      error: "NASA FIRMS key is not configured in Vercel."
    });
  }

  const allowedSources = [
    "VIIRS_SNPP_NRT",
    "VIIRS_NOAA20_NRT",
    "VIIRS_NOAA21_NRT",
    "MODIS_NRT"
  ];

  const source = allowedSources.includes(req.query.source)
    ? req.query.source
    : "VIIRS_SNPP_NRT";

  const requestedDays = Number(req.query.days || 1);
  const days = Math.min(5, Math.max(1,
    Number.isFinite(requestedDays) ? requestedDays : 1
  ));

  const url =
    `https://firms.modaps.eosdis.nasa.gov/api/area/csv/` +
    `${encodeURIComponent(key)}/${source}/world/${days}`;

  try {
    const response = await fetch(url, {
      signal: AbortSignal.timeout(45000)
    });

    if (!response.ok) {
      return res.status(502).json({
        error: "NASA FIRMS could not provide the requested data.",
        status: response.status
      });
    }

    const csv = await response.text();

    if (csv.toLowerCase().includes("invalid map key")) {
      return res.status(401).json({
        error: "NASA FIRMS rejected the configured map key."
      });
    }

    function parseCSV(text) {
      const lines = text.trim().split(/\r?\n/);
      if (lines.length < 2) return [];

      function splitLine(line) {
        const result = [];
        let value = "";
        let quoted = false;

        for (let i = 0; i < line.length; i++) {
          const char = line[i];

          if (char === '"') {
            if (quoted && line[i + 1] === '"') {
              value += '"';
              i++;
            } else {
              quoted = !quoted;
            }
          } else if (char === "," && !quoted) {
            result.push(value);
            value = "";
          } else {
            value += char;
          }
        }

        result.push(value);
        return result;
      }

      const headers = splitLine(lines[0]).map(h =>
        h.trim().toLowerCase()
      );

      return lines.slice(1).map(line => {
        const values = splitLine(line);
        const row = {};

        headers.forEach((header, index) => {
          row[header] = values[index] ?? "";
        });

        return row;
      });
    }

    const rows = parseCSV(csv);

    const records = rows.map(row => {
      const lat = Number(row.latitude);
      const lon = Number(row.longitude);

      const brightness = Number(
        row.bright_ti4 || row.brightness || row.bright_ti5 || 0
      );

      const frp = Number(row.frp || 0);

      if (
        !Number.isFinite(lat) ||
        !Number.isFinite(lon) ||
        lat < -90 || lat > 90 ||
        lon < -180 || lon > 180
      ) return null;

      const confidence = String(row.confidence || "unknown").toLowerCase();

      let risk = "Low";

      if (frp >= 100) risk = "Extreme";
      else if (frp >= 30) risk = "High";
      else if (frp >= 10) risk = "Moderate";

      return {
        latitude: lat,
        longitude: lon,
        brightness,
        frp,
        confidence,
        risk,
        date: row.acq_date || "",
        time: row.acq_time || "",
        satellite: row.satellite || source,
        instrument: row.instrument || "",
        daynight: row.daynight || "",
        scan: Number(row.scan || 0),
        track: Number(row.track || 0)
      };
    }).filter(Boolean);

    // Limit the browser payload for global data.
    const maxRecords = 15000;
    const total = records.length;

    let output = records;

    if (records.length > maxRecords) {
      const step = records.length / maxRecords;
      output = Array.from(
        { length: maxRecords },
        (_, i) => records[Math.floor(i * step)]
      );
    }

    return res.status(200).json({
      success: true,
      source,
      days,
      totalDetections: total,
      displayedDetections: output.length,
      truncated: total > output.length,
      updatedAt: new Date().toISOString(),
      data: output
    });

  } catch (error) {
    console.error("FIRMS API error:", error);

    return res.status(500).json({
      error: "Unable to connect to NASA FIRMS.",
      details: error.message
    });
  }
}

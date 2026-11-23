export default async function handler(req, res) {
  const apiKey = process.env.FIRMS_MAP_KEY || process.env.NASA_API_KEY;

  if (!apiKey) {
    return res.status(500).json({ error: "FIRMS_MAP_KEY not configured on server." });
  }

  try {
    const response = await fetch(
      `https://firms.modaps.eosdis.nasa.gov/api/area/csv/${encodeURIComponent(apiKey)}/VIIRS_NOAA20_NRT/world/1`
    );

    if (!response.ok) {
      throw new Error("NASA upstream error: " + response.status);
    }

    const data = await response.text();

    res.setHeader("Content-Type", "text/plain");
    return res.status(200).send(data);
  } catch (error) {
    return res.status(500).json({ error: "Failed to fetch satellite telemetry." });
  }
}

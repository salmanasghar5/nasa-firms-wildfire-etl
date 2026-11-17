export default async function handler(req, res) {
  const apiKey = process.env.NASA_API_KEY; // Secured on the server environment
  
  if (!apiKey) {
    return res.status(500).json({ error: "NASA API key not configured on server." });
  }

  try {
    const response = await fetch(`https://firms.modaps.eosdis.nasa.gov/api/area/csv/${apiKey}/VIIRS_NOAA20_NRT/world/1`);
    if (!response.ok) throw new Error("NASA upstream error: " + response.status);
    
    const data = await response.text();
    
    res.setHeader('Content-Type', 'text/plain');
    res.status(200).send(data);
  } catch (error) {
    res.status(500).json({ error: "Failed to fetch satellite telemetry." });
  }
}


export default async function handler(req, res) {
  if (req.method !== "GET") {
    return res.status(405).send("Method not allowed");
  }

  const mapKey = process.env.FIRMS_MAP_KEY;

  if (!mapKey) {
    return res.status(500).send("NASA MAP KEY is not configured in Vercel");
  }

  const allowedDatasets = [
    "VIIRS_NOAA20_NRT",
    "VIIRS_NOAA21_NRT",
    "VIIRS_SNPP_NRT",
    "MODIS_NRT"
  ];

  const dataset = req.query.dataset || "VIIRS_NOAA20_NRT";
  const days = Number(req.query.days || 3);

  if (!allowedDatasets.includes(dataset)) {
    return res.status(400).send("Invalid satellite dataset");
  }

  if (![1, 2, 3].includes(days)) {
    return res.status(400).send("Invalid date range");
  }

  try {
    const url =
      `https://firms.modaps.eosdis.nasa.gov/api/area/csv/` +
      `${encodeURIComponent(mapKey)}/${dataset}/world/${days}`;

    const response = await fetch(url);

    if (!response.ok) {
      return res.status(502).send("NASA FIRMS data request failed");
    }

    const csv = await response.text();

    if (!csv || csv.toLowerCase().includes("invalid map key")) {
      return res.status(502).send("NASA returned invalid data");
    }

    res.setHeader("Content-Type", "text/csv; charset=utf-8");
    res.setHeader("Cache-Control", "s-maxage=300, stale-while-revalidate=60");

    return res.status(200).send(csv);

  } catch (error) {
    return res.status(500).send("Unable to connect to NASA FIRMS");
  }
}

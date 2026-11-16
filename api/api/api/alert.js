
let lastAlertTime = 0;

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({
      error: "Method not allowed"
    });
  }

  const webhook = process.env.DISCORD_WEBHOOK_URL;

  if (!webhook) {
    return res.status(500).json({
      error: "Discord webhook is not configured."
    });
  }

  // Reject requests originating from other websites.
  const origin = req.headers.origin;
  const host = req.headers.host;

  if (
    origin &&
    host &&
    new URL(origin).host !== host
  ) {
    return res.status(403).json({
      error: "Invalid request origin."
    });
  }

  // Best-effort cooldown for this serverless instance.
  const now = Date.now();

  if (now - lastAlertTime < 15000) {
    return res.status(429).json({
      error: "Please wait before sending another alert."
    });
  }

  const { type, message, detections } = req.body || {};

  if (!["manual", "automatic"].includes(type)) {
    return res.status(400).json({
      error: "Invalid alert type."
    });
  }

  if (type === "manual" && (
    typeof message !== "string" ||
    !message.trim() ||
    message.length > 1500
  )) {
    return res.status(400).json({
      error: "Enter an alert message under 1500 characters."
    });
  }

  if (
    type === "automatic" &&
    (!Array.isArray(detections) || detections.length === 0)
  ) {
    return res.status(400).json({
      error: "No wildfire detections provided."
    });
  }

  let content = "";

  if (type === "manual") {
    content =
      "🚨 **SATELLITE LIVE — MANUAL ALERT**\n" +
      message.trim();
  } else {
    const safe = detections.slice(0, 5);

    content =
      "🔥 **SATELLITE LIVE — AUTOMATIC WILDFIRE ALERT**\n" +
      `New high/extreme-risk detections: ${safe.length}\n\n` +
      safe.map((fire, index) => {
        const lat = Number(fire.latitude);
        const lon = Number(fire.longitude);
        const frp = Number(fire.frp);

        if (
          !Number.isFinite(lat) ||
          !Number.isFinite(lon) ||
          !Number.isFinite(frp) ||
          Math.abs(lat) > 90 ||
          Math.abs(lon) > 180
        ) return null;

        return (
          `**${index + 1}. ${String(fire.risk || "High")} Risk**\n` +
          `Location: ${lat.toFixed(3)}, ${lon.toFixed(3)}\n` +
          `FRP: ${frp.toFixed(2)} MW\n` +
          `Satellite: ${String(fire.satellite || "VIIRS").slice(0, 30)}`
        );
      }).filter(Boolean).join("\n\n");
  }

  if (!content.trim()) {
    return res.status(400).json({
      error: "No valid alert content."
    });
  }

  try {
    const response = await fetch(webhook, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        content: content.slice(0, 1900),
        allowed_mentions: {
          parse: []
        }
      }),
      signal: AbortSignal.timeout(15000)
    });

    if (!response.ok) {
      return res.status(502).json({
        error: "Discord rejected the alert.",
        status: response.status
      });
    }

    lastAlertTime = now;

    return res.status(200).json({
      success: true,
      message: "Discord alert sent successfully."
    });

  } catch (error) {
    return res.status(500).json({
      error: "Unable to send Discord alert."
    });
  }
}

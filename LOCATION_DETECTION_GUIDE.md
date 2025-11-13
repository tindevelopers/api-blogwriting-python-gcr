# Location Detection Guide

## Overview

The enhanced keyword analysis endpoint (`/api/v1/keywords/enhanced`) now supports automatic location detection from the client's IP address when location is not explicitly specified.

## How It Works

### 1. Location Priority

The API uses the following priority order for determining location:

1. **Explicitly Specified**: If `location` is provided in the request body and is not the default "United States", it will be used
2. **IP-Based Detection**: If location is not specified (or is default "United States"), the API attempts to detect location from the client's IP address
3. **Default Fallback**: Falls back to "United States" if IP detection fails or is unavailable

### 2. IP-Based Detection

The API uses the free `ip-api.com` service to detect the country from the client's IP address:

- **Service**: `http://ip-api.com/json/{ip}?fields=country`
- **Timeout**: 2 seconds (non-blocking)
- **Fallback**: Gracefully falls back to default if detection fails

### 3. Supported Countries

The following countries are mapped to DataForSEO-compatible location names:

- United States
- United Kingdom
- Canada
- Australia
- Germany
- France
- Spain
- Italy
- Netherlands
- Sweden
- Norway
- Denmark
- Finland
- Poland
- Brazil
- Mexico
- India
- Japan
- South Korea
- China
- Singapore

*Note: Other countries will be returned as-is if detected, but may need to match DataForSEO's location format.*

## API Usage

### Request Without Location (Auto-Detection)

```json
POST /api/v1/keywords/enhanced
{
  "keywords": ["digital marketing"],
  "language": "en"
  // location not specified - will be detected from IP
}
```

**Response**:
```json
{
  "enhanced_analysis": { ... },
  "location": {
    "used": "United Kingdom",
    "detected_from_ip": true,
    "specified": false
  }
}
```

### Request With Explicit Location

```json
POST /api/v1/keywords/enhanced
{
  "keywords": ["digital marketing"],
  "location": "Canada",
  "language": "en"
}
```

**Response**:
```json
{
  "enhanced_analysis": { ... },
  "location": {
    "used": "Canada",
    "detected_from_ip": false,
    "specified": true
  }
}
```

## Response Fields

The response includes a `location` object with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `used` | string | The location actually used for the analysis |
| `detected_from_ip` | boolean | Whether location was detected from IP address |
| `specified` | boolean | Whether location was explicitly specified in request |

## IP Detection Details

### How IP is Extracted

1. **Direct Client IP**: `request.client.host`
2. **Proxy Headers**: Checks `X-Forwarded-For` header (takes first IP if multiple)
3. **Localhost Handling**: Skips detection for localhost IPs (`127.0.0.1`, `localhost`, `::1`)

### Privacy & Performance

- **Privacy**: IP addresses are only used for geolocation lookup, not stored
- **Performance**: Detection has a 2-second timeout and is non-blocking
- **Fallback**: Gracefully falls back to default if detection fails
- **Logging**: Detection results are logged at INFO level for debugging

## Use Cases

### 1. Automatic Localization

Perfect for applications that want to automatically provide location-relevant keyword data:

```typescript
// Frontend doesn't need to detect location
const response = await fetch('/api/v1/keywords/enhanced', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keywords: ['your keyword'],
    language: 'en'
    // No location needed - auto-detected!
  })
});

const data = await response.json();
console.log(`Analysis used location: ${data.location.used}`);
console.log(`Detected from IP: ${data.location.detected_from_ip}`);
```

### 2. Override Detection

Applications can still explicitly specify location when needed:

```typescript
// Explicitly request data for a specific country
const response = await fetch('/api/v1/keywords/enhanced', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keywords: ['your keyword'],
    location: 'Germany',  // Override auto-detection
    language: 'en'
  })
});
```

### 3. Multi-Region Analysis

Compare keyword data across regions:

```typescript
const regions = ['United States', 'United Kingdom', 'Canada'];
const results = await Promise.all(
  regions.map(location =>
    fetch('/api/v1/keywords/enhanced', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        keywords: ['your keyword'],
        location: location,
        language: 'en'
      })
    }).then(r => r.json())
  )
);
```

## Limitations

1. **IP Detection Accuracy**: IP-based geolocation is approximate and may not always reflect the user's actual location
2. **VPN/Proxy**: Users behind VPNs or proxies may have incorrect location detection
3. **DataForSEO Format**: Detected countries must match DataForSEO's location format
4. **Rate Limits**: The free `ip-api.com` service has rate limits (45 requests/minute)

## Best Practices

1. **Always Specify Location**: For production applications, explicitly specify location when known
2. **Use IP Detection as Fallback**: Use IP detection only when location cannot be determined from user preferences
3. **Handle Detection Failures**: Always check `detected_from_ip` to know if detection succeeded
4. **Cache Results**: Consider caching location detection results per IP to reduce API calls

## Troubleshooting

### Location Always Returns "United States"

- Check if IP detection is working: Look for log messages like `"Detected location from IP: {country}"`
- Verify client IP is not localhost: Localhost IPs skip detection
- Check geolocation service: The `ip-api.com` service may be rate-limited or unavailable

### Incorrect Location Detected

- User may be behind VPN/proxy
- IP geolocation databases may be outdated
- Solution: Allow users to manually override location

### Detection Slow

- The geolocation API has a 2-second timeout
- Consider caching results per IP address
- Use explicit location when possible to avoid detection overhead

## Implementation Details

### Code Location

- **Function**: `detect_location_from_ip()` in `main.py`
- **Endpoint**: `/api/v1/keywords/enhanced`
- **Geolocation Service**: `ip-api.com` (free tier)

### Future Enhancements

Potential improvements:
- Use Cloud Run's request headers for more accurate location
- Add caching for IP-to-location mappings
- Support for more granular location detection (city/region)
- Integration with premium geolocation services for better accuracy


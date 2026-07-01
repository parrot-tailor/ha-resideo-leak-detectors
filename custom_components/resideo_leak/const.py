"""Constants for the Resideo Leak Detectors integration."""

DOMAIN = "resideo_leak"

# OAuth2 endpoints (shared with the official Honeywell Lyric cloud).
OAUTH2_AUTHORIZE = "https://api.honeywellhome.com/oauth2/authorize"
OAUTH2_TOKEN = "https://api.honeywellhome.com/oauth2/token"

# REST API base.
API_BASE = "https://api.honeywellhome.com/v2"

# deviceClass value the API uses for water leak / freeze detectors.
DEVICE_CLASS_LEAK = "LeakDetector"

# Alarm type that duplicates the connectivity binary sensor; excluded from the
# "problem" sensor so offline isn't double-reported.
ALARM_DEVICE_OFFLINE = "DeviceOffline"

# Sensor check-in is user-configurable to 1, 2, or 3 times per day
# (deviceSettings.checkinPeriod = 24/12/8 hours), so temp/humidity/battery
# readings update slowly. Polling more often is still cheap and catches leak
# and alarm state changes sooner. 300s matches the official lyric integration.
DEFAULT_UPDATE_INTERVAL = 300

MANUFACTURER = "Resideo"

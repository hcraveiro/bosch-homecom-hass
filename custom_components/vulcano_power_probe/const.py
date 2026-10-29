"""Constants for the read-only power probe."""

DOMAIN = "vulcano_power_probe"

# Candidate paths are read only; unsupported resources return empty values.
PATHS = (
    "/system",
    "/system/info",
    "/system/healthStatus",
    "/system/appliance",
    "/system/appliance/enabled",
    "/system/appliance/status",
    "/system/appliance/operationMode",
    "/system/operatingState",
    "/system/status",
    "/system/state",
    "/dhwCircuits",
    "/dhwCircuits/dhw1/operationMode",
    "/dhwCircuits/dhw1/sensor/fanSpeed",
    "/dhwCircuits/dhw1/sensor/waterFlow",
    "/heatSources/hs1/powerPercentage",
)

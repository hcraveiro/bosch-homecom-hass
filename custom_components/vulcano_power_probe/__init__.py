"""Read-only diagnostics for Bosch/Vulcano WDDW2 power state."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, PATHS

BOSCH_DOMAIN = "bosch_homecom"
BOSCH_READ_SERVICE = "get_recordings_service"


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    """Flatten nested values for an exact field-by-field comparison."""
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for key, item in value.items():
            output.update(_flatten(item, f"{prefix}.{key}" if prefix else str(key)))
        return output
    if isinstance(value, list):
        output = {}
        for index, item in enumerate(value):
            output.update(_flatten(item, f"{prefix}[{index}]"))
        return output
    return {prefix: value}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Register read-only snapshot services."""
    snapshots: dict[str, Any] = {}
    hass.data[DOMAIN] = snapshots

    async def capture(call: ServiceCall) -> dict[str, Any]:
        """Capture the selected gateway's resource values without writing."""
        device_id = str(call.data["device_id"]).strip()
        label = str(call.data["label"]).strip().lower()
        if label not in ("on", "off"):
            raise HomeAssistantError("label must be 'on' or 'off'")
        if not device_id.isdecimal():
            raise HomeAssistantError("device_id must contain only digits")
        if not hass.services.has_service(BOSCH_DOMAIN, BOSCH_READ_SERVICE):
            raise HomeAssistantError("Bosch HomeCom read service is not available")

        result = await hass.services.async_call(
            BOSCH_DOMAIN,
            BOSCH_READ_SERVICE,
            {"device_id": device_id, "paths": list(PATHS)},
            blocking=True,
            return_response=True,
        )
        if not isinstance(result, dict):
            raise HomeAssistantError("Bosch HomeCom returned an invalid response")

        # The upstream bulk response may include unsupported paths; do not
        # interpret missing paths as 'off'.
        payload = {
            path: deepcopy(result[path])
            for path in PATHS
            if path in result
        }
        snapshots[label] = {
            "device_id": device_id,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "values": payload,
        }
        return {
            "label": label,
            "captured_at": snapshots[label]["captured_at"],
            "supported_paths": list(payload),
            "unsupported_or_empty_paths": [p for p in PATHS if p not in payload],
            "values": payload,
        }

    async def compare(call: ServiceCall) -> dict[str, Any]:
        """Compare two physical power states without assuming their meaning."""
        if "on" not in snapshots or "off" not in snapshots:
            raise HomeAssistantError("Capture both 'on' and 'off' first")
        if snapshots["on"]["device_id"] != snapshots["off"]["device_id"]:
            raise HomeAssistantError("Snapshots belong to different devices")

        on_flat = _flatten(snapshots["on"]["values"])
        off_flat = _flatten(snapshots["off"]["values"])
        changes = {
            key: {"on": on_flat.get(key), "off": off_flat.get(key)}
            for key in sorted(on_flat.keys() | off_flat.keys())
            if on_flat.get(key) != off_flat.get(key)
        }
        return {
            "device_id": snapshots["on"]["device_id"],
            "on_captured_at": snapshots["on"]["captured_at"],
            "off_captured_at": snapshots["off"]["captured_at"],
            "changed_fields": changes,
            "changed_count": len(changes),
            "note": "Changes are candidates only; temperature and flow changes do not prove power status.",
        }

    hass.services.async_register(
        DOMAIN, "capture", capture, supports_response=SupportsResponse.ONLY
    )
    hass.services.async_register(
        DOMAIN, "compare", compare, supports_response=SupportsResponse.ONLY
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Remove diagnostic services and captured data."""
    hass.services.async_remove(DOMAIN, "capture")
    hass.services.async_remove(DOMAIN, "compare")
    hass.data.pop(DOMAIN, None)
    return True

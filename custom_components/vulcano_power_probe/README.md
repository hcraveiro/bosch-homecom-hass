# Vulcano Power Probe (experimental)

Independent, **read-only** Home Assistant integration with domain `vulcano_power_probe`.
It coexists with the original `bosch_homecom` and uses the original integration's
`get_recordings_service` to query multiple Bosch API paths in a single bulk request.

## Install

1. Install and configure the official/custom Bosch HomeCom integration first.
2. Copy the complete `custom_components/vulcano_power_probe` folder into
   `/config/custom_components/vulcano_power_probe` on your Home Assistant instance.
   Do **not** replace or rename the existing `bosch_homecom` folder.
3. Restart Home Assistant.
4. Settings -> Devices & services -> Add integration -> **Vulcano Power Probe**.

**This is a manual install.** The fork retains both components; do not assume HACS
will select the experimental folder automatically from the repository.

## Capture & compare

Developer Tools -> Actions, with the appliance physically powered **on**:

```yaml
action: vulcano_power_probe.capture
data:
  device_id: "101397765"
  label: "on"
```

Switch the appliance **off physically**, wait for readings to settle, then:

```yaml
action: vulcano_power_probe.capture
data:
  device_id: "101397765"
  label: "off"
```

Compare the two snapshots:

```yaml
action: vulcano_power_probe.compare
```

The compare action returns `changed_fields`. Missing paths are listed separately
as `unsupported_or_empty_paths` in each capture. A field changing is only a
candidate power-state indicator; confirm across multiple cycles before using it.

The snapshots are held in memory and disappear on integration unload/restart.
Only GET-style bulk reads are issued. No PUT, control entity, or on/off command
is implemented. Avoid sharing raw responses without checking for sensitive data.

## v0.2.0 discovery

Capture now explores references advertised by the device. Discovery is read-only, at most 90 paths, 20 paths per request and three expansion rounds. The response includes `queried_count` and all supported and unsupported paths. Re-capture both physical states after upgrading; old captures are not retained across restarts.

# NIBE Energy Conversion (nibe_enery_conversion)

Custom Home Assistant integration that converts NIBE “past hour” energy sensors (kWh) into cumulative totals and COP metrics.

## Features
- UI configuration for 8 input sensors (past-hour kWh)
- UI options for update schedule (minute past hour) and run-on-start
- 8 cumulative energy totals (total_increasing)
- 2 cumulative sums (produced/used)
- 4 COP sensors for last hour (total, hot water, heating, cooling)
- No helper entities; state stored internally

## Installation (local)
1) Copy `custom_components/nibe_enery_conversion` into your Home Assistant config directory under `custom_components/`.
2) Restart Home Assistant.
3) Add integration: Settings → Devices & Services → Add Integration → “NIBE Energy Conversion”.

## Configuration
### Inputs (GUI)
Select these 8 “past hour” sensors:
- Produced: cooling, heating, hot water
- Used: cooling, heating, hot water
- Auxiliary used: heating, hot water

### Options (GUI)
- `update_minute`: minute past the hour to process the last hour (default 15)
- `run_on_start`: run once on HA start (only if the minute has passed)

## Outputs
### Energy totals (kWh, total_increasing)
- Produced cooling/heating/hot water
- Used cooling/heating/hot water
- Auxiliary used heating/hot water

### Sums (kWh, total_increasing)
- Produced total
- Used total

### COP (last hour)
- COP total
- COP hot water
- COP heating
- COP cooling

## Notes
- Aggregation runs only at the scheduled time (and optionally at start).
- Double-count protection uses the hour-end timestamp internally.
- COP is computed from the same last-hour inputs and updated on schedule.

## Support
This is a local custom integration. No GitHub publishing required.

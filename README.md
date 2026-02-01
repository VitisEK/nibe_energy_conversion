[![](https://img.shields.io/github/release/VitisEK/nibe_energy_conversion/all.svg?style=for-the-badge)](https://github.com/VitisEK/nibe_energy_conversion/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![](https://img.shields.io/github/license/VitisEK/nibe_energy_conversion?style=for-the-badge)](LICENSE)
[![](https://img.shields.io/badge/MAINTAINER-%40VitisEK-red?style=for-the-badge)](https://github.com/VitisEK)
[![](https://img.shields.io/badge/GitHub%20Sponsors-SUPPORT-EA4AAA?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/VitisEK)
[![](https://img.shields.io/badge/COMMUNITY-FORUM-success?style=for-the-badge)](https://community.home-assistant.io)

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

## rebuild_history_stats_and_storage.py
### Purpose
A one-time rebuild tool that recalculates historical energy totals from hourly “past hour” sensors and then patches Home Assistant storage so the integration’s internal totals match the rebuilt history.

### What it does
- Reads hourly long-term statistics from `home-assistant_v2.db`.
- Rebuilds cumulative totals for all output sensors and writes them to `statistics` and (optionally) `statistics_short_term`.
- Updates the integration storage file (`.storage/nibe_enery_conversion_data_<entry_id>`) with the latest cumulative totals and `last_processed`.
- Stops Home Assistant Core before writing, makes backups, then starts Core again.

### How to use
1) Run the script on the Home Assistant host (or in the container) with access to `/config`.
2) Follow the wizard prompts (DB path, `.storage` dir, input/output statistic_ids).
3) Confirm stopping HA Core when asked.
4) After it finishes, HA is started again and totals should match the rebuilt history.

Notes:
- The script creates backups of the DB and the selected storage file.
- Default paths: `/config/home-assistant_v2.db` and `/config/.storage`.


## Changelog

### v1.0.0 

*   Initial release

## Support
This is a local custom integration. No GitHub publishing required.



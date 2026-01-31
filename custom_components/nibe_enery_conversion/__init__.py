from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from .const import (
    CONF_RUN_ON_START,
    CONF_UPDATE_MINUTE,
    DEFAULT_RUN_ON_START,
    DEFAULT_UPDATE_MINUTE,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import NibeEnergyCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = NibeEnergyCoordinator(hass, entry)
    await coordinator.async_initialize()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "unsub_time": None,
    }

    async def _run_tick(now):
        await coordinator.async_process_tick()

    def _schedule_time_listener() -> None:
        minute = int(entry.options.get(CONF_UPDATE_MINUTE, DEFAULT_UPDATE_MINUTE))
        unsub = async_track_time_change(hass, _run_tick, minute=minute, second=0)
        hass.data[DOMAIN][entry.entry_id]["unsub_time"] = unsub

    _schedule_time_listener()

    async def _on_start(event):
        run_on_start = entry.options.get(CONF_RUN_ON_START, DEFAULT_RUN_ON_START)
        minute = int(entry.options.get(CONF_UPDATE_MINUTE, DEFAULT_UPDATE_MINUTE))
        if not run_on_start:
            return
        if dt_util.now().minute < minute:
            return
        await coordinator.async_process_tick()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_start)

    entry.async_on_unload(
        entry.add_update_listener(_async_update_listener)
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not data:
        return

    unsub = data.get("unsub_time")
    if unsub:
        unsub()

    coordinator: NibeEnergyCoordinator = data["coordinator"]

    async def _run_tick(now):
        await coordinator.async_process_tick()

    minute = int(entry.options.get(CONF_UPDATE_MINUTE, DEFAULT_UPDATE_MINUTE))
    data["unsub_time"] = async_track_time_change(hass, _run_tick, minute=minute, second=0)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if data and data.get("unsub_time"):
        data["unsub_time"]()

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

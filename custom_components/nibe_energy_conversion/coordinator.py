from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_AUX_USED_HEATING,
    CONF_AUX_USED_HOT_WATER,
    CONF_PROD_COOLING,
    CONF_PROD_HEATING,
    CONF_PROD_HOT_WATER,
    CONF_USED_COOLING,
    CONF_USED_HEATING,
    CONF_USED_HOT_WATER,
    COP_COOLING,
    COP_HEATING,
    COP_HOT_WATER,
    COP_LAST_HOUR,
    COP_TOTAL,
    STORAGE_KEY,
    STORAGE_VERSION,
    SUM_PRODUCED,
    SUM_USED,
    TOTAL_AUX_USED_HEATING,
    TOTAL_AUX_USED_HOT_WATER,
    TOTAL_PROD_COOLING,
    TOTAL_PROD_HEATING,
    TOTAL_PROD_HOT_WATER,
    TOTAL_USED_COOLING,
    TOTAL_USED_HEATING,
    TOTAL_USED_HOT_WATER,
)

_LOGGER = logging.getLogger(__name__)


TOTAL_KEYS = [
    TOTAL_PROD_COOLING,
    TOTAL_PROD_HEATING,
    TOTAL_PROD_HOT_WATER,
    TOTAL_USED_COOLING,
    TOTAL_USED_HEATING,
    TOTAL_USED_HOT_WATER,
    TOTAL_AUX_USED_HEATING,
    TOTAL_AUX_USED_HOT_WATER,
]


INPUT_TO_TOTAL = {
    CONF_PROD_COOLING: TOTAL_PROD_COOLING,
    CONF_PROD_HEATING: TOTAL_PROD_HEATING,
    CONF_PROD_HOT_WATER: TOTAL_PROD_HOT_WATER,
    CONF_USED_COOLING: TOTAL_USED_COOLING,
    CONF_USED_HEATING: TOTAL_USED_HEATING,
    CONF_USED_HOT_WATER: TOTAL_USED_HOT_WATER,
    CONF_AUX_USED_HEATING: TOTAL_AUX_USED_HEATING,
    CONF_AUX_USED_HOT_WATER: TOTAL_AUX_USED_HOT_WATER,
}


@dataclass
class NibeEnergyData:
    totals: dict[str, float]
    last_processed: str | None
    last_cop: float
    last_cop_total: float
    last_cop_hot_water: float
    last_cop_heating: float
    last_cop_cooling: float


class NibeEnergyCoordinator(DataUpdateCoordinator[NibeEnergyData]):
    def __init__(self, hass: HomeAssistant, entry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="NIBE Energy Conversion",
            update_interval=None,
        )
        self.entry = entry
        self.store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry.entry_id}")
        self.data = NibeEnergyData(
            totals={key: 0.0 for key in TOTAL_KEYS},
            last_processed=None,
            last_cop=0.0,
            last_cop_total=0.0,
            last_cop_hot_water=0.0,
            last_cop_heating=0.0,
            last_cop_cooling=0.0,
        )

    async def async_initialize(self) -> None:
        stored: dict[str, Any] | None = await self.store.async_load()
        if stored:
            totals = {key: float(stored.get("totals", {}).get(key, 0.0)) for key in TOTAL_KEYS}
            self.data = NibeEnergyData(
                totals=totals,
                last_processed=stored.get("last_processed"),
                last_cop=float(stored.get("last_cop", 0.0)),
                last_cop_total=float(stored.get("last_cop_total", 0.0)),
                last_cop_hot_water=float(stored.get("last_cop_hot_water", 0.0)),
                last_cop_heating=float(stored.get("last_cop_heating", 0.0)),
                last_cop_cooling=float(stored.get("last_cop_cooling", 0.0)),
            )
        self.async_set_updated_data(self.data)

    def _state_as_float(self, entity_id: str) -> float:
        state = self.hass.states.get(entity_id)
        if state is None:
            return 0.0
        try:
            return float(state.state)
        except (TypeError, ValueError):
            return 0.0

    def _get_inputs(self) -> dict[str, float]:
        inputs: dict[str, float] = {}
        for conf_key, total_key in INPUT_TO_TOTAL.items():
            entity_id = self.entry.data.get(conf_key)
            if not entity_id:
                inputs[total_key] = 0.0
                continue
            inputs[total_key] = self._state_as_float(entity_id)
        return inputs

    async def async_process_tick(self) -> None:
        hour_end_local = dt_util.now().replace(minute=0, second=0, microsecond=0)
        hour_end_utc = dt_util.as_utc(hour_end_local)
        hour_end_key = hour_end_utc.isoformat()

        if self.data.last_processed == hour_end_key:
            return

        inputs = self._get_inputs()
        totals = {**self.data.totals}
        for key, value in inputs.items():
            totals[key] = round(totals.get(key, 0.0) + value, 3)

        prod_cooling = inputs[TOTAL_PROD_COOLING]
        prod_heating = inputs[TOTAL_PROD_HEATING]
        prod_hot_water = inputs[TOTAL_PROD_HOT_WATER]
        used_cooling = inputs[TOTAL_USED_COOLING]
        used_heating = inputs[TOTAL_USED_HEATING]
        used_hot_water = inputs[TOTAL_USED_HOT_WATER]
        used_aux_heating = inputs[TOTAL_AUX_USED_HEATING]
        used_aux_hot_water = inputs[TOTAL_AUX_USED_HOT_WATER]

        produced_last = prod_cooling + prod_heating + prod_hot_water
        used_last = (
            used_cooling
            + used_heating
            + used_hot_water
            + used_aux_heating
            + used_aux_hot_water
        )
        last_cop = round(produced_last / used_last, 2) if used_last > 0 else 0.0
        last_cop_total = last_cop
        last_cop_hot_water = (
            round(prod_hot_water / (used_hot_water + used_aux_hot_water), 2)
            if (used_hot_water + used_aux_hot_water) > 0
            else 0.0
        )
        last_cop_heating = (
            round(prod_heating / (used_heating + used_aux_heating), 2)
            if (used_heating + used_aux_heating) > 0
            else 0.0
        )
        last_cop_cooling = (
            round(prod_cooling / used_cooling, 2) if used_cooling > 0 else 0.0
        )

        data = NibeEnergyData(
            totals=totals,
            last_processed=hour_end_key,
            last_cop=last_cop,
            last_cop_total=last_cop_total,
            last_cop_hot_water=last_cop_hot_water,
            last_cop_heating=last_cop_heating,
            last_cop_cooling=last_cop_cooling,
        )

        await self.store.async_save(
            {
                "totals": data.totals,
                "last_processed": data.last_processed,
                "last_cop": data.last_cop,
                "last_cop_total": data.last_cop_total,
                "last_cop_hot_water": data.last_cop_hot_water,
                "last_cop_heating": data.last_cop_heating,
                "last_cop_cooling": data.last_cop_cooling,
            }
        )

        self.async_set_updated_data(data)

    def get_total(self, key: str) -> float:
        return float(self.data.totals.get(key, 0.0))

    def get_sum(self, key: str) -> float:
        totals = self.data.totals
        if key == SUM_PRODUCED:
            return round(
                totals.get(TOTAL_PROD_COOLING, 0.0)
                + totals.get(TOTAL_PROD_HEATING, 0.0)
                + totals.get(TOTAL_PROD_HOT_WATER, 0.0),
                3,
            )
        if key == SUM_USED:
            return round(
                totals.get(TOTAL_USED_COOLING, 0.0)
                + totals.get(TOTAL_USED_HEATING, 0.0)
                + totals.get(TOTAL_USED_HOT_WATER, 0.0)
                + totals.get(TOTAL_AUX_USED_HEATING, 0.0)
                + totals.get(TOTAL_AUX_USED_HOT_WATER, 0.0),
                3,
            )
        return 0.0

    def get_cop(self) -> float:
        return float(self.data.last_cop)

    def get_cop_kind(self, key: str) -> float:
        if key == COP_TOTAL:
            return float(self.data.last_cop_total)
        if key == COP_HOT_WATER:
            return float(self.data.last_cop_hot_water)
        if key == COP_HEATING:
            return float(self.data.last_cop_heating)
        if key == COP_COOLING:
            return float(self.data.last_cop_cooling)
        return float(self.data.last_cop)

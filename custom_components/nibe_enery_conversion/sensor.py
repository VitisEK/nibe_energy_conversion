from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    COP_COOLING,
    COP_HEATING,
    COP_HOT_WATER,
    COP_TOTAL,
    DOMAIN,
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
from .coordinator import NibeEnergyCoordinator


@dataclass(frozen=True, kw_only=True)
class NibeEnergySensorDescription(SensorEntityDescription):
    data_key: str
    kind: str


SENSOR_DESCRIPTIONS = [
    NibeEnergySensorDescription(
        key=TOTAL_PROD_COOLING,
        translation_key=TOTAL_PROD_COOLING,
        data_key=TOTAL_PROD_COOLING,
        kind="total",
        name="Produced cooling (kWh)",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NibeEnergySensorDescription(
        key=TOTAL_PROD_HEATING,
        translation_key=TOTAL_PROD_HEATING,
        data_key=TOTAL_PROD_HEATING,
        kind="total",
        name="Produced heating (kWh)",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NibeEnergySensorDescription(
        key=TOTAL_PROD_HOT_WATER,
        translation_key=TOTAL_PROD_HOT_WATER,
        data_key=TOTAL_PROD_HOT_WATER,
        kind="total",
        name="Produced hot water (kWh)",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NibeEnergySensorDescription(
        key=TOTAL_USED_COOLING,
        translation_key=TOTAL_USED_COOLING,
        data_key=TOTAL_USED_COOLING,
        kind="total",
        name="Used cooling (kWh)",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NibeEnergySensorDescription(
        key=TOTAL_USED_HEATING,
        translation_key=TOTAL_USED_HEATING,
        data_key=TOTAL_USED_HEATING,
        kind="total",
        name="Used heating (kWh)",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NibeEnergySensorDescription(
        key=TOTAL_USED_HOT_WATER,
        translation_key=TOTAL_USED_HOT_WATER,
        data_key=TOTAL_USED_HOT_WATER,
        kind="total",
        name="Used hot water (kWh)",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NibeEnergySensorDescription(
        key=TOTAL_AUX_USED_HEATING,
        translation_key=TOTAL_AUX_USED_HEATING,
        data_key=TOTAL_AUX_USED_HEATING,
        kind="total",
        name="Auxiliary heating (kWh)",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NibeEnergySensorDescription(
        key=TOTAL_AUX_USED_HOT_WATER,
        translation_key=TOTAL_AUX_USED_HOT_WATER,
        data_key=TOTAL_AUX_USED_HOT_WATER,
        kind="total",
        name="Auxiliary hot water (kWh)",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NibeEnergySensorDescription(
        key=SUM_PRODUCED,
        translation_key=SUM_PRODUCED,
        data_key=SUM_PRODUCED,
        kind="sum",
        name="Produced total (kWh)",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NibeEnergySensorDescription(
        key=SUM_USED,
        translation_key=SUM_USED,
        data_key=SUM_USED,
        kind="sum",
        name="Used total (kWh)",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NibeEnergySensorDescription(
        key=COP_TOTAL,
        translation_key=COP_TOTAL,
        data_key=COP_TOTAL,
        kind="cop",
        name="COP total (last hour)",
        native_unit_of_measurement="COP",
        icon="mdi:alpha-c-circle",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NibeEnergySensorDescription(
        key=COP_HOT_WATER,
        translation_key=COP_HOT_WATER,
        data_key=COP_HOT_WATER,
        kind="cop",
        name="COP hot water (last hour)",
        native_unit_of_measurement="COP",
        icon="mdi:alpha-c-circle",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NibeEnergySensorDescription(
        key=COP_HEATING,
        translation_key=COP_HEATING,
        data_key=COP_HEATING,
        kind="cop",
        name="COP heating (last hour)",
        native_unit_of_measurement="COP",
        icon="mdi:alpha-c-circle",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NibeEnergySensorDescription(
        key=COP_COOLING,
        translation_key=COP_COOLING,
        data_key=COP_COOLING,
        kind="cop",
        name="COP cooling (last hour)",
        native_unit_of_measurement="COP",
        icon="mdi:alpha-c-circle",
        state_class=SensorStateClass.MEASUREMENT,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator: NibeEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        NibeEnergySensor(coordinator, entry, description) for description in SENSOR_DESCRIPTIONS
    )


class NibeEnergySensor(CoordinatorEntity[NibeEnergyCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NibeEnergyCoordinator,
        entry: ConfigEntry,
        description: NibeEnergySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Energy Conversion",
        )

    @property
    def native_value(self):
        if self.entity_description.kind == "total":
            return self.coordinator.get_total(self.entity_description.data_key)
        if self.entity_description.kind == "sum":
            return self.coordinator.get_sum(self.entity_description.data_key)
        return self.coordinator.get_cop_kind(self.entity_description.data_key)

    @property
    def extra_state_attributes(self):
        last_processed = self.coordinator.data.last_processed
        if not last_processed:
            return None
        dt = dt_util.parse_datetime(last_processed)
        if dt is None:
            return None
        return {"last_processed_hour_end": dt_util.as_local(dt).isoformat()}

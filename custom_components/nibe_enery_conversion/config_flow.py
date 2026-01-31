from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_AUX_USED_HEATING,
    CONF_AUX_USED_HOT_WATER,
    CONF_PROD_COOLING,
    CONF_PROD_HEATING,
    CONF_PROD_HOT_WATER,
    CONF_RUN_ON_START,
    CONF_UPDATE_MINUTE,
    CONF_USED_COOLING,
    CONF_USED_HEATING,
    CONF_USED_HOT_WATER,
    DEFAULT_RUN_ON_START,
    DEFAULT_UPDATE_MINUTE,
    DOMAIN,
)


SENSOR_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor")
)


class NibeEnergyConversionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="NIBE Energy Conversion",
                data=user_input,
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_PROD_COOLING): SENSOR_SELECTOR,
                vol.Required(CONF_PROD_HEATING): SENSOR_SELECTOR,
                vol.Required(CONF_PROD_HOT_WATER): SENSOR_SELECTOR,
                vol.Required(CONF_USED_COOLING): SENSOR_SELECTOR,
                vol.Required(CONF_USED_HEATING): SENSOR_SELECTOR,
                vol.Required(CONF_USED_HOT_WATER): SENSOR_SELECTOR,
                vol.Required(CONF_AUX_USED_HEATING): SENSOR_SELECTOR,
                vol.Required(CONF_AUX_USED_HOT_WATER): SENSOR_SELECTOR,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )

    async def async_step_import(self, user_input):
        return await self.async_step_user(user_input)

    @staticmethod
    def async_get_options_flow(config_entry):
        return NibeEnergyConversionOptionsFlow()


class NibeEnergyConversionOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        update_minute = self.config_entry.options.get(
            CONF_UPDATE_MINUTE, DEFAULT_UPDATE_MINUTE
        )
        run_on_start = self.config_entry.options.get(
            CONF_RUN_ON_START, DEFAULT_RUN_ON_START
        )

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_UPDATE_MINUTE, default=update_minute
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=59,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_RUN_ON_START, default=run_on_start
                ): selector.BooleanSelector(),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )

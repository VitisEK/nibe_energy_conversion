DOMAIN = "nibe_enery_conversion"
PLATFORMS = ["sensor"]

CONF_PROD_COOLING = "prod_cooling_sensor"
CONF_PROD_HEATING = "prod_heating_sensor"
CONF_PROD_HOT_WATER = "prod_hot_water_sensor"

CONF_USED_COOLING = "used_cooling_sensor"
CONF_USED_HEATING = "used_heating_sensor"
CONF_USED_HOT_WATER = "used_hot_water_sensor"

CONF_AUX_USED_HEATING = "aux_used_heating_sensor"
CONF_AUX_USED_HOT_WATER = "aux_used_hot_water_sensor"

CONF_UPDATE_MINUTE = "update_minute"
CONF_RUN_ON_START = "run_on_start"

DEFAULT_UPDATE_MINUTE = 15
DEFAULT_RUN_ON_START = True

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_data"

TOTAL_PROD_COOLING = "prod_cooling_total"
TOTAL_PROD_HEATING = "prod_heating_total"
TOTAL_PROD_HOT_WATER = "prod_hot_water_total"

TOTAL_USED_COOLING = "used_cooling_total"
TOTAL_USED_HEATING = "used_heating_total"
TOTAL_USED_HOT_WATER = "used_hot_water_total"

TOTAL_AUX_USED_HEATING = "aux_used_heating_total"
TOTAL_AUX_USED_HOT_WATER = "aux_used_hot_water_total"

SUM_PRODUCED = "produced_total"
SUM_USED = "used_total"
COP_LAST_HOUR = "cop_last_hour"
COP_TOTAL = "cop_total"
COP_HOT_WATER = "cop_hot_water"
COP_HEATING = "cop_heating"
COP_COOLING = "cop_cooling"

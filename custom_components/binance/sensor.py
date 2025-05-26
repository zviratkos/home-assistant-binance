"""sensor"""

import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from .const import CONF_SYMBOLS, CONF_DECIMALS, CONF_UPDATE_INVERVAL
from .binance_ticker_sensor import BinanceTickerSensor, BinanceDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_SYMBOLS): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_DECIMALS, default=8): cv.positive_int,
    vol.Optional(CONF_UPDATE_INVERVAL, default=60): cv.positive_int,
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    symbols = config[CONF_SYMBOLS]
    decimals = config[CONF_DECIMALS]
    interval = config[CONF_UPDATE_INVERVAL]

    sensors = []
    for symbol in symbols:
        coordinator = BinanceDataCoordinator(hass, symbol, interval)
        await coordinator.async_refresh()
        sensors.append(BinanceTickerSensor(symbol, decimals, interval, coordinator))

    async_add_entities(sensors, update_before_add=True)


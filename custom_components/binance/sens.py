import logging
from datetime import timedelta
import decimal
import aiohttp
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import STATE_UNKNOWN
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import CONF_SYMBOLS, CONF_DECIMALS, CONF_UPDATE_INVERVAL

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
        await coordinator.async_config_entry_first_refresh()
        sensors.append(BinanceTickerSensor(symbol, decimals, coordinator))

    async_add_entities(sensors, update_before_add=True)

class BinanceDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, symbol, interval):
        self.symbol = symbol
        super().__init__(
            hass,
            _LOGGER,
            name=f"Binance Ticker {symbol}",
            update_interval=timedelta(seconds=interval),
        )

    async def _async_update_data(self):
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={self.symbol}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"Failed to fetch data: {response.status}")
                    return await response.json()
        except Exception as err:
            raise UpdateFailed(f"Error fetching Binance data: {err}")

class BinanceTickerSensor(SensorEntity):
    def __init__(self, symbol, decimals, coordinator):
        self.coordinator = coordinator
        self._symbol = symbol
        self._decimals = decimals
        self._attr_name = f"Binance Ticker {symbol.upper()}"
        self._attr_unique_id = f"binance_unique_{symbol.lower()}"
        self._attr_device_class = "monetary"
        self._attr_native_unit_of_measurement = "USD"

    @property
    def native_value(self):
        try:
            price = self.coordinator.data.get("price")
            return round(decimal.Decimal(price), self._decimals)
        except Exception as e:
            _LOGGER.error("Error parsing price for %s: %s", self._symbol, e)
            return STATE_UNKNOWN

    @property
    def extra_state_attributes(self):
        return self.coordinator.data

    async def async_update(self):
        await self.coordinator.async_request_refresh()

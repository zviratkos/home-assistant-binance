import logging
import decimal
import aiohttp
from datetime import timedelta
from homeassistant.const import STATE_UNKNOWN
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class BinanceDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, symbol, interval):
        self.symbol = symbol
        self._interval_seconds = interval
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
    def __init__(self, symbol, decimals, update_interval, coordinator):
        self.coordinator = coordinator
        self._symbol = symbol
        self._decimals = decimals
        self._update_interval = update_interval
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
        attrs = dict(self.coordinator.data or {})
        attrs["update_interval"] = self._update_interval
        return attrs

    async def async_update(self):
        await self.coordinator.async_request_refresh()


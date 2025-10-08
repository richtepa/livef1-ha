import logging
import threading
import importlib.util
import asyncio
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_UPDATE_DELAY, DEFAULT_UPDATE_DELAY

_LOGGER = logging.getLogger(__name__)

WEBSOCKET_URL = "wss://livetiming.formula1.com/signalrcore"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Live F1 switch from a config entry."""
    async_add_entities([LiveF1Switch(hass, config_entry)], True)

        
class LiveF1Switch(SwitchEntity):
    def __init__(self, hass, config_entry):
        self._attr_name = "Live F1"
        self._attr_unique_id = f"{DOMAIN}_switch"
        self._is_on = False
        self._attr_extra_state_attributes = {}
        self.hass = hass
        self._config_entry = config_entry

        # Store reference to this switch in hass.data
        if DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]:
            hass.data[DOMAIN][config_entry.entry_id]["switch_entity"] = self

        # Get delay from config or options
        delay = config_entry.options.get(
            CONF_UPDATE_DELAY,
            config_entry.data.get(CONF_UPDATE_DELAY, DEFAULT_UPDATE_DELAY)
        )

        from .livef1dataservice import LiveF1DataService
        self.service = LiveF1DataService(
            url=WEBSOCKET_URL,
            driver_count=20,
            callback=self._on_data,
            logger=_LOGGER,
            update_delay=delay
        )

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, "live_f1")},
            "name": "Live F1",
            "manufacturer": "Live F1 Integration",
        }

    @property
    def is_on(self):
        return self._is_on

    async def _on_data(self, data):
        self._attr_extra_state_attributes.update(data)
        self.schedule_update_ha_state()
        
    async def async_turn_on(self, **kwargs):
        if not self._is_on:
            self._is_on = True
            _LOGGER.info("Starting LiveF1DataService...")
            self.hass.loop.create_task(self.service.run_forever())
            self.async_schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        if self._is_on:
            _LOGGER.info("Stopping LiveF1DataService...")
            await self.service.disconnect()
            self._is_on = False
            self.async_schedule_update_ha_state()

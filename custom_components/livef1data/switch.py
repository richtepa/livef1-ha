import logging
import threading
import importlib.util
import asyncio
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant

from .const import DOMAIN, SWITCH_NAME

_LOGGER = logging.getLogger(__name__)

WEBSOCKET_URL = "wss://livetiming.formula1.com/signalrcore"


def setup_platform(hass: HomeAssistant, config, add_entities, discovery_info=None):
    add_entities([LiveF1Switch(hass)], True)

        
class LiveF1Switch(SwitchEntity):
    def __init__(self, hass):
        self._attr_name = "Live F1 Data"
        self._is_on = False
        self._attr_extra_state_attributes = {}
        self.hass = hass

        from .livef1dataservice import LiveF1DataService
        self.service = LiveF1DataService(
            url=WEBSOCKET_URL,
            driver_count=20,
            callback=self._on_data,
            logger=_LOGGER
        )

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

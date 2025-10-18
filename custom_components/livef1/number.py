"""Number entity for Live F1 integration."""
import logging
from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_UPDATE_DELAY, DEFAULT_UPDATE_DELAY

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Live F1 number entity from a config entry."""
    async_add_entities([LiveF1UpdateDelayNumber(hass, config_entry)], True)


class LiveF1UpdateDelayNumber(NumberEntity):
    """Number entity for controlling the update delay."""
    
    def __init__(self, hass, config_entry):
        """Initialize the number entity."""
        self.hass = hass
        self._config_entry = config_entry
        self._attr_name = "Live F1 Update Delay"
        self._attr_unique_id = f"{DOMAIN}_update_delay"
        self._attr_icon = "mdi:timer"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 600
        self._attr_native_step = 0.1
        self._attr_native_unit_of_measurement = "s"
        
        # Get initial value from config or options
        self._attr_native_value = config_entry.options.get(
            CONF_UPDATE_DELAY,
            config_entry.data.get(CONF_UPDATE_DELAY, DEFAULT_UPDATE_DELAY)
        )

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, "live_f1")},
            "name": "Live F1",
            "manufacturer": "Live F1 Integration",
        }

    async def async_set_native_value(self, value: float) -> None:
        """Update the delay value."""
        self._attr_native_value = value
        
        # Get the switch entity from hass.data and update its service delay
        if (DOMAIN in self.hass.data 
            and self._config_entry.entry_id in self.hass.data[DOMAIN]):
            switch_entity = self.hass.data[DOMAIN][self._config_entry.entry_id].get("switch_entity")
            if switch_entity and hasattr(switch_entity, 'service'):
                switch_entity.service.set_update_delay(value)
                _LOGGER.info(f"Updated Live F1 service delay to {value}s")
        
        # Also update the config entry options
        options = dict(self._config_entry.options)
        options[CONF_UPDATE_DELAY] = value
        self.hass.config_entries.async_update_entry(
            self._config_entry, options=options
        )
        
        self.async_write_ha_state()
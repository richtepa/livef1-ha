from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol

from .const import DOMAIN, CONF_UPDATE_DELAY, DEFAULT_UPDATE_DELAY


class LiveF1DataConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            # user_input is already validated by voluptuous
            return self.async_create_entry(title="Live F1", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_UPDATE_DELAY, default=DEFAULT_UPDATE_DELAY
                ): vol.All(vol.Coerce(float), vol.Range(min=0, max=600))
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return LiveF1OptionsFlowHandler(config_entry)


class LiveF1OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Live F1 options flow."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # user_input is already validated by voluptuous
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_UPDATE_DELAY,
            self.config_entry.data.get(CONF_UPDATE_DELAY, DEFAULT_UPDATE_DELAY),
        )

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_UPDATE_DELAY, default=current
                ): vol.All(vol.Coerce(float), vol.Range(min=0, max=600))
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
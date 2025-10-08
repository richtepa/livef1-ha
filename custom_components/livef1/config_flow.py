from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_UPDATE_DELAY, DEFAULT_UPDATE_DELAY

class LiveF1DataConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        # Create the data schema once
        data_schema = {
            CONF_UPDATE_DELAY: {
                "type": "float",
                "default": DEFAULT_UPDATE_DELAY,
                "required": False
            }
        }
        
        if user_input is not None:
            # Validate update_delay if provided
            if CONF_UPDATE_DELAY in user_input:
                try:
                    delay = float(user_input[CONF_UPDATE_DELAY])
                    if delay < 0 or delay > 600:
                        errors[CONF_UPDATE_DELAY] = "value_out_of_range"
                    else:
                        user_input[CONF_UPDATE_DELAY] = delay
                except (ValueError, TypeError):
                    errors[CONF_UPDATE_DELAY] = "invalid_number"
            
            # If no errors, create the entry
            if not errors:
                return self.async_create_entry(title="Live F1", data=user_input)
        
        # Show form (either initial load or with validation errors)
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )

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
        errors = {}
        
        # Create the data schema once to avoid duplication
        data_schema = {
            CONF_UPDATE_DELAY: {
                "type": "float",
                "default": self.config_entry.options.get(
                    CONF_UPDATE_DELAY, 
                    self.config_entry.data.get(CONF_UPDATE_DELAY, DEFAULT_UPDATE_DELAY)
                ),
                "required": False
            }
        }
        
        if user_input is not None:
            # Validate update_delay if provided
            if CONF_UPDATE_DELAY in user_input:
                try:
                    delay = float(user_input[CONF_UPDATE_DELAY])
                    if delay < 0 or delay > 600:
                        errors[CONF_UPDATE_DELAY] = "value_out_of_range"
                    else:
                        user_input[CONF_UPDATE_DELAY] = delay
                except (ValueError, TypeError):
                    errors[CONF_UPDATE_DELAY] = "invalid_number"
            
            # If no errors, create the entry
            if not errors:
                return self.async_create_entry(title="", data=user_input)

        # Show form (either initial load or with validation errors)
        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors
        )
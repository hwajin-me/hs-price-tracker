import logging

import voluptuous as vol
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class Lang:
    _hass: HomeAssistant
    _lang: str

    def __init__(self, hass):
        self._hass = hass
        self._lang = hass.config.language

    def select(self, user_input: dict = None):
        if user_input is not None and "lang" in user_input:
            self._lang = user_input["lang"]

        return self

    def selector(self, user_input: dict = None):
        return {
            vol.Required(
                "lang",
                description="Select Option",
                default=self._lang if user_input is None else user_input.get("lang"),
            ): vol.In(
                {
                    "en": "English",
                    "ja": "Japanese",
                    "ko": "Korean",
                }
            )
        }

    def f(self, key: str, items: dict):
        lang = self._lang
        if lang in items:
            _LOGGER.debug(f"Language: {lang} - {key}: {items[lang]}")

            return {key: items[lang]}

        return {key: "Undefined"}

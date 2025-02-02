import logging
from copy import deepcopy

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers import selector

from custom_components.price_tracker.components.error import (
    NotFoundError,
    InvalidItemUrlError,
)
from custom_components.price_tracker.components.id import IdGenerator
from custom_components.price_tracker.components.lang import Lang
from custom_components.price_tracker.consts.confs import (
    CONF_TYPE,
    CONF_TARGET,
    CONF_ITEM_MANAGEMENT_CATEGORIES,
)
from custom_components.price_tracker.datas.unit import ItemUnitType
from custom_components.price_tracker.services.factory import (
    create_service_item_url_parser,
    create_service_item_target_parser,
)
from custom_components.price_tracker.utilities.list import Lu

_LOGGER = logging.getLogger(__name__)


class PriceTrackerSetup:
    _step_setup: str = "setup"  # static variable
    _config_flow: config_entries.ConfigFlow
    _option_flow: config_entries.OptionsFlow
    const_option_setup_select: str = "option_setup_select"
    const_option_proxy_select: str = "option_proxy_select"
    const_option_selenium_select: str = "option_selenium_select"
    const_option_personal_select: str = "option_personal_select"
    const_option_modify_select: str = "option_modify_select"
    const_option_add_select: str = "option_add_select"
    const_option_entity_select: str = "option_entity_select"
    const_option_entity_delete: str = "option_entity_delete"

    const_option_select_device: str = "service_device"
    const_option_select_entity: str = "service_entity"

    conf_target: str = "target"
    conf_proxy = "proxy"
    conf_selenium = "selenium"
    conf_selenium_proxy = "selenium_proxy"
    conf_proxy_opensource_use = "proxy_opensource"
    conf_proxy_list = "proxy_list"
    # (private) conf for select
    conf_item_unique_id: str = "item_unique_id"
    conf_item_device_id: str = "item_device_id"
    conf_item_url: str = "item_url"
    conf_item_management_category: str = "item_management_category"
    conf_item_unit_type: str = "item_unit_type"
    conf_item_unit: str = "item_unit"
    conf_item_refresh_interval: str = "item_refresh_interval"
    conf_item_price_change_interval_hour: str = "item_price_change_interval_hour"
    conf_item_debug: str = "item_debug"

    def __init__(
        self,
        config_flow: config_entries.ConfigFlow = None,
        option_flow: config_entries.OptionsFlow = None,
        config_entry=None,
    ):
        self._config_flow = config_flow
        self._option_flow = option_flow
        self._config_entry = config_entry

    async def setup(self, user_input: dict = None):
        _LOGGER.debug("Setup(configuration): %s", user_input)

        if user_input is None:
            return None

        await self._config_flow.async_set_unique_id(
            self._async_set_unique_id(user_input)
        )
        # @ignore
        self._config_flow._abort_if_unique_id_configured(
            updates={
                CONF_TARGET: user_input["service_type"],
            }
        )  # Ignore the warning

        return self._config_flow.async_create_entry(
            title=self.setup_name(), data={**self.setup_config_data(user_input)}
        )

    async def option_setup(self, user_input: dict = None):
        _LOGGER.debug("Setup(option): %s", user_input)

        return self._option_flow.async_show_form(
            step_id=self._step_setup,
            description_placeholders={
                **Lang(self._option_flow.hass).f(
                    key="title",
                    items={"en": "Select Settings", "ja": "設定", "ko": "설정"},
                ),
                **Lang(self._option_flow.hass).f(
                    key="description",
                    items={
                        "en": "Select the menu where you want to add or modify.",
                        "ja": "エンティティを生成または修正します。",
                        "ko": "원하는 설정을 선택합니다.",
                    },
                ),
            },
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        self.const_option_setup_select
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                self.const_option_personal_select,
                                self.const_option_proxy_select,
                                self.const_option_selenium_select,
                                self.const_option_modify_select,
                                self.const_option_add_select,
                            ],
                            mode=selector.SelectSelectorMode.LIST,
                            translation_key=self.const_option_setup_select,
                        )
                    ),
                },
                **self._schema_user_input_option_service_device(user_input),
            ),
            errors={},
        )

    async def option_proxy(self, user_input: dict = None):
        # Get items if the user_input is None
        if user_input is None or self.conf_proxy not in user_input:
            # Fetch original items
            proxies = dict(self._config_entry.data).get(self.conf_proxy, [])

            return self._option_flow.async_show_form(
                step_id=self._step_setup,
                description_placeholders={
                    **Lang(self._option_flow.hass).f(
                        key="title",
                        items={
                            "en": "Proxy configuration",
                            "ja": "プロキシ設定",
                            "ko": "프록시 설정",
                        },
                    ),
                    **Lang(self._option_flow.hass).f(
                        key="description",
                        items={
                            "en": "Set the proxy server to use when connecting to the site.",
                            "ja": "サイトへの接続時に使用するプロキシ サーバーを設定します。",
                            "ko": "사이트에 연결할 때 사용할 프록시 서버를 설정합니다.",
                        },
                    ),
                },
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            self.const_option_setup_select,
                            default=self.const_option_proxy_select,
                        ): vol.In(
                            {
                                self.const_option_proxy_select: self.const_option_proxy_select
                            }
                        ),
                        vol.Optional(
                            self.conf_proxy,
                            description={"suggested_value": ",".join(proxies)},
                            default="",
                        ): cv.string,
                    }
                ),
            )

        config = dict(self._config_entry.data)
        options = dict(self._config_entry.options)
        proxies = (
            user_input[self.conf_proxy] if self.conf_proxy in user_input else ""
        ).strip()
        config[self.conf_proxy] = (
            Lu.map(str(proxies).split(","), lambda x: x.strip())
            if proxies != ""
            else []
        )
        # Filtering
        config[self.conf_proxy] = list(
            filter(lambda x: x != "", config[self.conf_proxy])
        )

        _LOGGER.debug("Proxy configuration with %s (original: %s)", config, user_input)

        flag = self._option_flow.hass.config_entries.async_update_entry(
            entry=self._config_entry,
            data={
                **config,
            },
            options=options if options is not None else {},
        )

        return self._option_flow.async_abort(
            reason="proxy_updated" if flag else "proxy_not_updated"
        )

    async def option_selenium(self, user_input: dict = None):
        # Get items if the user_input is None
        if user_input is None or self.conf_selenium not in user_input:
            selenium = dict(self._config_entry.data).get(self.conf_selenium, None)
            selenium_proxy = dict(self._config_entry.data).get(
                self.conf_selenium_proxy, []
            )

            return self._option_flow.async_show_form(
                step_id=self._step_setup,
                description_placeholders={
                    **Lang(self._option_flow.hass).f(
                        key="title",
                        items={
                            "en": "Selenium configuration",
                            "ja": "Selenium設定",
                            "ko": "Selenium 설정",
                        },
                    ),
                    **Lang(self._option_flow.hass).f(
                        key="description",
                        items={
                            "en": "Set the Selenium server to use when connecting to the site.",
                            "ja": "サイトへの接続時に使用するSelenium サーバーを設定します。",
                            "ko": "사이트에 연결할 때 사용할 Selenium 서버를 설정합니다.",
                        },
                    ),
                },
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            self.const_option_setup_select,
                            default=self.const_option_selenium_select,
                        ): vol.In(
                            {
                                self.const_option_selenium_select: self.const_option_selenium_select
                            }
                        ),
                        vol.Optional(
                            self.conf_selenium,
                            description={
                                "suggested_value": selenium
                                if selenium is not None
                                else ""
                            },
                            default="",
                        ): cv.string,
                        vol.Optional(
                            self.conf_selenium_proxy,
                            description={
                                "suggested_value": ",".join(selenium_proxy)
                                if len(selenium_proxy) > 0
                                else ""
                            },
                            default="",
                        ): cv.string,
                    }
                ),
            )

        config = dict(self._config_entry.data)
        options = dict(self._config_entry.options)
        selenium = (
            user_input[self.conf_selenium] if self.conf_selenium in user_input else ""
        )
        proxies = (
            user_input[self.conf_selenium_proxy]
            if self.conf_selenium_proxy in user_input
            else ""
        ).strip()
        if selenium == "":
            selenium = None

        config[self.conf_selenium] = selenium
        config[self.conf_selenium_proxy] = (
            Lu.map(str(proxies).split(","), lambda x: x.strip())
            if proxies != ""
            else []
        )
        # Filtering
        config[self.conf_selenium_proxy] = list(
            filter(lambda x: x != "", config[self.conf_selenium_proxy])
        )

        _LOGGER.debug(
            "Selenium configuration with %s (original: %s)", config, user_input
        )

        flag = self._option_flow.hass.config_entries.async_update_entry(
            entry=self._config_entry,
            data={
                **config,
            },
            options=options if options is not None else {},
        )

        return self._option_flow.async_abort(
            reason="selenium_updated" if flag else "selenium_not_updated"
        )

    async def option_modify(self, device, entity, user_input: dict = None):
        """Modify an existing entry."""
        _LOGGER.debug("Setup Modify(option): %s", user_input)

        if (
            user_input is not None
            and self.const_option_entity_delete in user_input
            and user_input[self.const_option_entity_delete] is True
        ):
            data = deepcopy(self._config_entry.options.get(self.conf_target, []))
            target_entity = (er.async_get(self._option_flow.hass)).async_get(
                user_input[self.const_option_select_entity]
            )

            for item in data[:]:
                if target_entity.unique_id == item[self.conf_item_unique_id]:
                    data.remove(item)

            _LOGGER.debug("Setup Modify(option) / Delete data: %s", user_input)

            return self._option_flow.async_create_entry(
                title="Deleted", data={self.conf_target: data}
            )

        return await self.option_upsert(
            device=device,
            user_input={
                **user_input,
                self.const_option_select_device: device,
                self.const_option_select_entity: entity,
            },
        )

    async def option_upsert(self, device=None, user_input: dict = None):
        """Add a new entry."""
        _LOGGER.debug("Setup Upsert(option): %s", user_input)

        errors = {}

        try:
            if user_input is not None:
                """Add a new entry."""
                if (
                    self.conf_item_url in user_input
                    and self.conf_item_management_category in user_input
                    and CONF_ITEM_MANAGEMENT_CATEGORIES in user_input
                    and self.conf_item_unit_type in user_input
                    and self.conf_item_unit in user_input
                    and self.conf_item_refresh_interval in user_input
                    and self.conf_item_price_change_interval_hour in user_input
                ):
                    _LOGGER.debug(
                        "Setup Upsert(option) / Creation from: %s", user_input
                    )

                    data = deepcopy(
                        self._config_entry.options.get(self.conf_target, [])
                    )
                    service_type = self._config_entry.data["type"]
                    entity_id = IdGenerator.generate_entity_id(
                        service_type=service_type,
                        entity_target=create_service_item_target_parser(service_type)(
                            create_service_item_url_parser(service_type)(
                                user_input[self.conf_item_url]
                            )
                        ),
                        device_id=Lu.get(user_input, self.const_option_select_device),
                    )

                    for item in data[:]:
                        if entity_id == item[self.conf_item_unique_id]:
                            data.remove(item)

                    data_input = {
                        self.conf_item_unique_id: entity_id,
                        self.conf_item_device_id: Lu.get(
                            user_input, self.const_option_select_device
                        ),
                        **user_input,
                    }

                    if self.const_option_select_device in user_input:
                        del data_input[self.const_option_select_device]

                    if self.const_option_setup_select in user_input:
                        del data_input[self.const_option_setup_select]

                    if self.const_option_select_entity in user_input:
                        del data_input[self.const_option_select_entity]

                    data.append(data_input)

                    return self._option_flow.async_create_entry(
                        title=user_input[self.conf_item_url],
                        data={self.conf_target: data},
                    )
        except InvalidItemUrlError:
            errors["invalid_item_url"] = user_input[self.conf_item_url]

        schema = {
            vol.Required(self.conf_item_url, default=None): cv.string,
            vol.Optional(self.conf_item_management_category, default=""): cv.string,
            vol.Optional(CONF_ITEM_MANAGEMENT_CATEGORIES, default=""): cv.string,
            vol.Optional(self.conf_item_unit_type, default="auto"): vol.In(
                ["auto"] + ItemUnitType.list()
            ),
            vol.Optional(self.conf_item_unit, default=0): cv.positive_int,
            vol.Required(self.conf_item_refresh_interval, default=30): cv.positive_int,
            vol.Required(
                self.conf_item_price_change_interval_hour, default=24
            ): cv.positive_int,
            vol.Optional(self.conf_item_debug, default=False): cv.boolean,
        }

        # If the device and entity are selected
        if (
            user_input is not None
            and self.const_option_select_entity in user_input
            and Lu.get(user_input, self.const_option_select_entity) is not None
            and errors == {}
        ):
            """Change default variables"""
            entity = (er.async_get(self._option_flow.hass)).async_get(
                user_input[self.const_option_select_entity]
            )
            item = Lu.find(
                self._config_entry.options.get(self.conf_target, []),
                self.conf_item_unique_id,
                entity.unique_id,
            )

            _LOGGER.debug(
                "Setup Upsert(option), modification - Entity: %s / UI : %s",
                entity,
                user_input,
            )

            if item is None:
                raise NotFoundError(
                    "Selected entity not found {} in {}.".format(
                        entity.entity_id,
                        self._config_entry.options.get(self.conf_target, []),
                    )
                )
            else:
                schema = {
                    vol.Required(
                        self.conf_item_url, default=item[self.conf_item_url]
                    ): cv.string,
                    vol.Optional(
                        self.conf_item_management_category,
                        default=Lu.get(item, self.conf_item_management_category, ""),
                    ): cv.string,
                    vol.Optional(
                        CONF_ITEM_MANAGEMENT_CATEGORIES,
                        default=Lu.get(item, CONF_ITEM_MANAGEMENT_CATEGORIES, ""),
                    ): cv.string,
                    vol.Optional(
                        self.conf_item_unit_type,
                        default=Lu.get_or_default(
                            item, self.conf_item_unit_type, "auto"
                        ),
                    ): vol.In(["auto"] + ItemUnitType.list()),
                    vol.Optional(
                        self.conf_item_unit,
                        default=Lu.get_or_default(item, self.conf_item_unit, 0),
                    ): cv.positive_int,
                    vol.Required(
                        self.conf_item_refresh_interval,
                        default=Lu.get_or_default(
                            item, self.conf_item_refresh_interval, 30
                        ),
                    ): cv.positive_int,
                    vol.Required(
                        self.conf_item_price_change_interval_hour,
                        default=Lu.get_or_default(
                            item, self.conf_item_price_change_interval_hour, 24
                        ),
                    ): cv.positive_int,
                    vol.Optional(
                        self.conf_item_debug,
                        default=Lu.get_or_default(item, self.conf_item_debug, False),
                    ): cv.boolean,
                }

        return self._option_flow.async_show_form(
            step_id=self._step_setup,
            description_placeholders={
                **Lang(self._option_flow.hass).f(
                    key="title",
                    items={"en": "Item", "ja": "エンティティ", "ko": "엔티티"},
                ),
                **Lang(self._option_flow.hass).f(
                    key="description",
                    items={
                        "en": "Add or modify a new item to track the price.",
                        "ja": "エンティティ プロパティを定義します。 一部の値は必須であり、item_urlを通じて商品固有の値を抽出します。",
                        "ko": "엔티티 속성을 정의합니다. 일부 값은 필수이며 item_url을 통해 상품 고유의 값을 추출합니다.",
                    },
                ),
            },
            data_schema=vol.Schema(
                {
                    **self._schema_user_input_option_select(user_input),
                    **self._schema_user_input_option_service_device(user_input),
                    **self._schema_user_input_option_service_entity(user_input),
                    **schema,
                }
            ),
            errors=errors,
        )

    async def option_select_device(self, user_input: dict = None):
        _LOGGER.debug("Setup Select Device(option): %s", user_input)

        device_entities = []

        for d in dr.async_entries_for_config_entry(
            dr.async_get(self._option_flow.hass), self._config_entry.entry_id
        ):
            device_entities.append(d.serial_number)

        if device_entities is None or len(device_entities) == 0:
            return None

        return self._option_flow.async_show_form(
            step_id=self._step_setup,
            description_placeholders={
                **Lang(self._option_flow.hass).f(
                    key="title",
                    items={
                        "en": "Select Device",
                        "ja": "デバイスを選択",
                        "ko": "기기를 선택",
                    },
                ),
                **Lang(self._option_flow.hass).f(
                    key="description",
                    items={
                        "en": "Select the device to include or be included in the entity.",
                        "ja": "エンティティを含む、または含まれている機器を選択します。",
                        "ko": "엔티티를 생성, 수정할 기기를 선택합니다.",
                    },
                ),
            },
            data_schema=vol.Schema(
                {
                    **self._schema_user_input_option_select(user_input),
                    vol.Optional(self.const_option_select_device): vol.In(
                        device_entities
                    ),
                }
            ),
            errors={},
        )

    async def option_select_entity(self, device=None, user_input: dict = None):
        _LOGGER.debug("Setup Select Entity(option): %s", user_input)

        option_entities = []

        entities = er.async_entries_for_config_entry(
            er.async_get(self._option_flow.hass), self._config_entry.entry_id
        )

        for e in entities:
            if IdGenerator.is_device_id(e.unique_id):
                continue

            if device is not None:
                device_id = IdGenerator.get_entity_device_target_from_id(e.unique_id)

                if device_id != device:
                    continue

            option_entities.append(e.entity_id)

        schema = {
            vol.Optional(self.const_option_select_entity): selector.EntitySelector(
                selector.EntitySelectorConfig(include_entities=option_entities)
            ),
            vol.Optional(self.const_option_entity_delete): selector.BooleanSelector(
                selector.BooleanSelectorConfig()
            ),
        }

        if device is not None:
            schema = {
                vol.Required(self.const_option_select_device, default=device): vol.In(
                    {device: device}
                ),
                **schema,
            }

        return self._option_flow.async_show_form(
            step_id=self._step_setup,
            description_placeholders={
                **Lang(self._option_flow.hass).f(
                    key="title",
                    items={
                        "en": "Select Entity",
                        "ja": "エンティティを選択",
                        "ko": "엔티티를 선택",
                    },
                ),
                **Lang(self._option_flow.hass).f(
                    key="description",
                    items={
                        "en": "Select the entity to manage.",
                        "ja": "管理するエンティティを選択します。",
                        "ko": "관리할 엔티티를 선택합니다.",
                    },
                ),
            },
            data_schema=vol.Schema(
                {**self._schema_user_input_option_select(user_input), **schema}
            ),
            errors={},
        )

    def setup_config_data(self, user_input: dict = None) -> dict:
        return {
            CONF_TYPE: user_input["service_type"],
        }

    @staticmethod
    def setup_code() -> str:
        pass

    @staticmethod
    def setup_name() -> str:
        pass

    def _get_data(self):
        return self._config_flow.hass.config_entries.async_entry_for_domain_unique_id(
            self._config_flow.handler, self._config_flow.unique_id
        )

    def _async_set_unique_id(self, user_input: dict) -> str:
        return "price-tracker-{}".format(user_input["service_type"])

    def _schema_user_input_service_type(self, user_input: dict = None):
        if user_input is None or "service_type" not in user_input:
            return {}
        return {
            vol.Required(
                "service_type",
                description="Service Type",
                default=user_input["service_type"],
            ): vol.In({user_input["service_type"]: user_input["service_type"]})
        }

    def _schema_user_input_option_service_device(self, user_input: dict = None):
        if (
            user_input is None
            or self.const_option_select_device not in user_input
            or user_input[self.const_option_select_device] is None
        ):
            return {}
        return {
            vol.Required(
                self.const_option_select_device,
                description="Target Device",
                default=user_input[self.const_option_select_device],
            ): vol.In(
                {
                    user_input[self.const_option_select_device]: user_input[
                        "service_device"
                    ]
                }
            )
        }

    def _schema_user_input_option_service_entity(self, user_input: dict = None):
        if user_input is None or self.const_option_select_entity not in user_input:
            return {}
        return {
            vol.Required(
                self.const_option_select_entity,
                description="Target entity",
                default=user_input[self.const_option_select_entity],
            ): vol.In(
                {
                    user_input[self.const_option_select_entity]: user_input[
                        self.const_option_select_entity
                    ]
                }
            )
        }

    def _schema_user_input_option_select(self, user_input: dict = None):
        if user_input is None or self.const_option_setup_select not in user_input:
            return {}

        return {
            vol.Required(
                self.const_option_setup_select,
                description="Select Option",
                default=user_input[self.const_option_setup_select],
            ): vol.In(
                {
                    user_input[self.const_option_setup_select]: user_input[
                        self.const_option_setup_select
                    ]
                }
            )
        }

    def _option_device(self, user_input: dict = None):
        if user_input is None:
            return None
        if "service_device" not in user_input:
            return None
        return user_input["service_device"]

    def _form_i18n_description(self, lang: str, description: str) -> dict:
        return {"description_{}".format(lang): description}

    def _form_i18n_title(self, lang: str, item: str) -> dict:
        return {"title_{}".format(lang): item}

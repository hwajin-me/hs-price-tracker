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

from custom_components.price_tracker.components.error import NotFoundError
from custom_components.price_tracker.components.forms import Forms
from custom_components.price_tracker.components.id import IdGenerator
from custom_components.price_tracker.const import CONF_TYPE
from custom_components.price_tracker.datas.unit import ItemUnitType
from custom_components.price_tracker.services.factory import (
    create_service_item_url_parser,
)
from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utils import find_item

_LOGGER = logging.getLogger(__name__)


class PriceTrackerSetup:
    _step_setup: str = "setup"  # static variable
    _config_flow: config_entries.ConfigFlow
    _option_flow: config_entries.OptionsFlow
    const_option_setup_select: str = "option_setup_select"
    const_option_modify_select: str = "option_modify_select"
    const_option_add_select: str = "option_add_select"
    const_option_entity_select: str = "option_entity_select"
    const_option_entity_delete: str = "option_entity_delete"

    const_option_select_device: str = "service_device"
    const_option_select_entity: str = "service_entity"

    conf_target: str = "target"
    # (private) conf for select
    conf_item_unique_id: str = "item_unique_id"
    conf_item_device_id: str = "item_device_id"
    conf_item_url: str = "item_url"
    conf_item_management_category: str = "item_management_category"
    conf_item_unit_type: str = "item_unit_type"
    conf_item_unit: str = "item_unit"
    conf_item_refresh_interval: str = "item_refresh_interval"
    conf_item_price_change_interval_hour: str = "item_price_change_interval_hour"

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
        self._config_flow._abort_if_unique_id_configured()  # Ignore the warning

        return self._config_flow.async_create_entry(
            title=self.setup_name(), data={**self.setup_config_data(user_input)}
        )

    async def option_setup(self, user_input: dict = None):
        _LOGGER.debug("Setup(option): %s", user_input)

        return self._option_flow.async_show_form(
            step_id=self._step_setup,
            description_placeholders={
                **self._form_i18n_title("en", "Select Settings"),
                **self._form_i18n_description(
                    "en", "Select the menu where you want to add or modify."
                ),
                **self._form_i18n_title("ja", "設定"),
                **self._form_i18n_description(
                    "ja", "エンティティを生成または修正します。"
                ),
                **self._form_i18n_title("ko", "설정"),
                **self._form_i18n_description(
                    "ko", "원하는 설정을 선택합니다."
                ),
            },
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        self.const_option_setup_select
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
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

    async def option_modify(self, device, entity, user_input: dict = None):
        """Modify an existing entry."""
        _LOGGER.debug("Setup Modify(option): %s", user_input)

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

        if user_input is not None:
            """Add a new entry."""
            if (
                self.conf_item_url in user_input
                and self.conf_item_management_category in user_input
                and self.conf_item_unit_type in user_input
                and self.conf_item_unit in user_input
                and self.conf_item_refresh_interval in user_input
                and self.conf_item_price_change_interval_hour in user_input
                and self.conf_item_url != ""
                and self.conf_item_management_category != ""
                and self.conf_item_unit_type != ""
                and self.conf_item_unit != ""
                and self.conf_item_refresh_interval != ""
                and self.conf_item_price_change_interval_hour != ""
            ):
                data = deepcopy(self._config_entry.options.get(self.conf_target, []))

                for item in data[:]:
                    if item[self.conf_item_url] == user_input[self.conf_item_url]:
                        if self.const_option_select_device in user_input:
                            if (
                                self.const_option_select_device in item
                                and item[self.const_option_select_device]
                                == user_input[self.const_option_select_device]
                            ):
                                data.remove(item)
                        else:
                            data.remove(item)

                data_input = {
                    self.conf_item_unique_id: IdGenerator.generate_entity_id(
                        service_type=self._config_entry.data["type"],
                        entity_target=create_service_item_url_parser(
                            self._config_entry.data["type"]
                        )(user_input[self.conf_item_url]),
                        device_id=Lu.get(user_input, self.const_option_select_device),
                    ),
                    self.conf_item_device_id: Lu.get(
                        user_input, self.const_option_select_device
                    ),
                    **user_input,
                }

                if self.const_option_select_device in user_input:
                    del data_input[self.const_option_setup_select]

                data.append(data_input)

                return self._option_flow.async_create_entry(
                    title=user_input[self.conf_item_url], data={self.conf_target: data}
                )

        schema = {
            vol.Required(self.conf_item_url, default=None): cv.string,
            vol.Optional(self.conf_item_management_category, default=""): cv.string,
            vol.Optional(self.conf_item_unit_type, default="auto"): vol.In(
                ["auto"] + ItemUnitType.list()
            ),
            vol.Optional(self.conf_item_unit, default=0): cv.positive_int,
            vol.Required(self.conf_item_refresh_interval, default=10): cv.positive_int,
            vol.Required(
                self.conf_item_price_change_interval_hour, default=24
            ): cv.positive_int,
        }

        # If the device and entity are selected
        if (
            user_input is not None
            and self.const_option_select_entity in user_input
            and Lu.get(user_input, self.const_option_select_entity) is not None
        ):
            """Change default variables"""
            entity = (er.async_get(self._option_flow.hass)).async_get(
                user_input[self.const_option_select_entity]
            )
            item = find_item(
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
                        self.conf_item_management_category, default=Lu.get(item, self.conf_item_management_category)
                    ): cv.string,
                    vol.Optional(self.conf_item_unit_type, default=Lu.get_or_default(item, self.conf_item_unit_type, 'auto')): vol.In(
                        ["auto"] + ItemUnitType.list()
                    ),
                    vol.Optional(self.conf_item_unit, default=Lu.get_or_default(item, self.conf_item_unit, 0)): cv.positive_int,
                    vol.Required(
                        self.conf_item_refresh_interval, default=Lu.get_or_default(item, self.conf_item_refresh_interval, 10)
                    ): cv.positive_int,
                    vol.Required(
                        self.conf_item_price_change_interval_hour, default=Lu.get_or_default(item, self.conf_item_price_change_interval_hour, 24)
                    ): cv.positive_int,
                }

        return self._option_flow.async_show_form(
            step_id=self._step_setup,
            description_placeholders={
                **self._form_i18n_title("en", "Item"),
                **self._form_i18n_description(
                    "en", "Add or modify a new item to track the price."
                ),
                **self._form_i18n_title("ja", "エンティティの生成/変更"),
                **self._form_i18n_description(
                    "ja", "エンティティ プロパティを定義します。 一部の値は必須であり、item_urlを通じて商品固有の値を抽出します。"
                ),
                **self._form_i18n_title("ko", "엔티티 생성 또는 변경"),
                **self._form_i18n_description(
                    "ko", "엔티티 속성을 정의합니다. 일부 값은 필수이며 item_url을 통해 상품 고유의 값을 추출합니다."
                ),
                **Forms.t('en', self.conf_item_url, 'Item URL or Product (e.g. https://www.idus.com/v2/product/400876fb-fd26-4290-abb7-589d60bbceb2)'),
                **Forms.t('ja', self.conf_item_url, '商品のURLアドレス(e.g. https://www.amazon.co.jp/%E3%82%AA%E3%83%A0%E3%83%AD%E3%83%B3-OMRON-KRD-703T-%E4%BD%93%E9%87%8D%E4%BD%93%E7%B5%84%E6%88%90%E8%A8%88KRD-703T-%E3%82%AB%E3%83%A9%E3%83%80%E3%82%B9%E3%82%AD%E3%83%A3%E3%83%B3/dp/B07YLPHPHB/ref=s9_acsd_al_ot_c2_x_3_t?_encoding=UTF8&pf_rd_m=A1VC38T7YXB528&pf_rd_s=merchandised-search-5&pf_rd_r=ANYP8XE2V2F8GCA21MWJ&pf_rd_p=626c9cca-d8de-4403-beb8-5fdcd3cfeea1&pf_rd_t=&pf_rd_i=3534638051)'),
                **Forms.t('ko', self.conf_item_url, '상품 URL 주소(e.g. https://www.coupang.com/vp/products/123456)'),
                **Forms.t('en', self.conf_item_management_category, 'Management Category'),
                **Forms.t('ja', self.conf_item_management_category, '管理カテゴリ'),
                **Forms.t('ko', self.conf_item_management_category, '관리 카테고리'),
                **Forms.t('en', self.conf_item_unit_type, 'Unit Type'),
                **Forms.t('ja', self.conf_item_unit_type, '単位タイプ'),
                **Forms.t('ko', self.conf_item_unit_type, '단위 유형'),
                **Forms.t('en', self.conf_item_unit, 'Volume (e.g. unit type > ml, unit > 300)'),
                **Forms.t('ja', self.conf_item_unit, '容量(e.g. unit type > ml, unit > 300)'),
                **Forms.t('ko', self.conf_item_unit, '용량 (e.g. unit type > ml, unit > 300)'),
                **Forms.t('en', self.conf_item_refresh_interval, 'Refresh Interval (minutes)'),
                **Forms.t('ja', self.conf_item_refresh_interval, '更新間隔(分)'),
                **Forms.t('ko', self.conf_item_refresh_interval, '새로 고침 간격(분)'),
                **Forms.t('en', self.conf_item_price_change_interval_hour, 'Price Change Interval (hours)'),
                **Forms.t('ja', self.conf_item_price_change_interval_hour, '価格変更間隔(時間)'),
                **Forms.t('ko', self.conf_item_price_change_interval_hour, '가격 변경 간격(시간)'),
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
                **self._form_i18n_title("en", "Select Device"),
                **self._form_i18n_description(
                    "en", "Select the device."
                ),
                **self._form_i18n_title("ja", "デバイスを選択"),
                **self._form_i18n_description(
                    "ja", "エンティティを含む、または含まれている機器を選択します。"
                ),
                **self._form_i18n_title("ko", "기기를 선택"),
                **self._form_i18n_description(
                    "ko", "엔티티를 생성, 수정할 기기를 선택합니다."
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
        hass = er.async_get(self._option_flow.hass)

        for e in entities:
            if device is not None:
                for d in dr.async_entries_for_config_entry(
                    dr.async_get(self._option_flow.hass), self._config_entry.entry_id
                ):
                    if d.serial_number != device:
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
                **self._form_i18n_title("en", "Select Entity"),
                **self._form_i18n_description(
                    "en", "Select the entity."
                ),
                **self._form_i18n_title("ja", "エンティティ"),
                **self._form_i18n_description(
                    "ja", "管理するエンティティを選択します。"
                ),
                **self._form_i18n_title("ko", "엔티티"),
                **self._form_i18n_description(
                    "ko", "관리할 엔티티를 선택합니다."
                ),
            },
            data_schema=vol.Schema(
                {**self._schema_user_input_option_select(user_input), **schema}
            ),
            errors={},
        )

    def setup_config_data(self, user_input: dict = None) -> dict:
        return {CONF_TYPE: user_input["service_type"]}

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

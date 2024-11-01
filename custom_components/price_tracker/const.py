from logging import Logger, getLogger

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

LOGGER: Logger = getLogger(__package__)

DOMAIN = "price_tracker"
NAME = "E-Commerce Price Tracker"
VERSION = "0.1.0"
PLATFORMS = ["sensor"]
_KIND = {
    'idus': '아이디어스',
    'coupang': '쿠팡',
    'ssg': '이마트 쓱(SSG)',
    'smartstore': '네이버 스마트스토어',
    'kurly': '마켓컬리',
    'oliveyoung': '올리브영',
    'ncnc': '니콘내콘',
    'amazon_jp': 'Amazom (日本)',
    'rakuten': '楽天',
    'yodobashi': 'ヨドバシカメラ',
    'mercari': 'メルカリ',
}
ENTITY_ID_FORMAT = DOMAIN + ".price_{}_{}"

CONF_OPTION_MODIFY = "option_modify"
CONF_OPTION_ADD = "option_add"
CONF_OPTION_ENTITIES = "option_entities"
CONF_OPTION_DELETE = "option_delete"
CONF_OPTION_SELECT = "option_select"
CONF_OPTIONS = [
    CONF_OPTION_MODIFY,
    CONF_OPTION_ADD
]
CONF_TYPE = "type"
CONF_ITEM_URL = "item_url"
CONF_ITEM_REFRESH_INTERVAL = "item_refresh_interval"
CONF_ITEM_MANAGEMENT_CATEGORY = "item_management_category"
CONF_TARGET = "target"
CONF_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_TYPE, default=None): vol.In(_KIND)
})
CONF_OPTION_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_ITEM_URL, default=None): cv.string,
    vol.Optional(CONF_ITEM_MANAGEMENT_CATEGORY, default=None): cv.string,
    vol.Required(CONF_ITEM_REFRESH_INTERVAL, default=10): cv.positive_int
})

REQUEST_DEFAULT_HEADERS = {
    'Accept': 'text/html,application/json,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    'Connection': 'close'
}

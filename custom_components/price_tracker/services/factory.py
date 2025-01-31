from custom_components.price_tracker.services.coupang.engine import CoupangEngine
from custom_components.price_tracker.services.daiso_kr.engine import DaisoKrEngine
from custom_components.price_tracker.services.gsthefresh.device import GsTheFreshDevice
from custom_components.price_tracker.services.gsthefresh.engine import GsTheFreshEngine
from custom_components.price_tracker.services.homeplus.engine import HomeplusEngine
from custom_components.price_tracker.services.idus.engine import IdusEngine
from custom_components.price_tracker.services.kurly.engine import KurlyEngine
from custom_components.price_tracker.services.lotte_kr.engine import LotteOnEngine
from custom_components.price_tracker.services.ncnc.engine import NcncEngine
from custom_components.price_tracker.services.oasis.engine import OasisEngine
from custom_components.price_tracker.services.oliveyoung.engine import OliveyoungEngine
from custom_components.price_tracker.services.rankingdak.engine import RankingdakEngine
from custom_components.price_tracker.services.smartstore.engine import SmartstoreEngine
from custom_components.price_tracker.services.ssg.engine import SsgEngine

_SERVICE_ITEM_URL_PARSER = {
    CoupangEngine.engine_code(): lambda cfg: CoupangEngine.parse_id(cfg),
    GsTheFreshEngine.engine_code(): lambda cfg: GsTheFreshEngine.parse_id(cfg),
    IdusEngine.engine_code(): lambda cfg: IdusEngine.parse_id(cfg),
    KurlyEngine.engine_code(): lambda cfg: KurlyEngine.parse_id(cfg),
    NcncEngine.engine_code(): lambda cfg: NcncEngine.parse_id(cfg),
    OasisEngine.engine_code(): lambda cfg: OasisEngine.parse_id(cfg),
    OliveyoungEngine.engine_code(): lambda cfg: OliveyoungEngine.parse_id(cfg),
    SmartstoreEngine.engine_code(): lambda cfg: SmartstoreEngine.parse_id(cfg),
    SsgEngine.engine_code(): lambda cfg: SsgEngine.parse_id(cfg),
    RankingdakEngine.engine_code(): lambda cfg: RankingdakEngine.parse_id(cfg),
    LotteOnEngine.engine_code(): lambda cfg: LotteOnEngine.parse_id(cfg),
    HomeplusEngine.engine_code(): lambda cfg: HomeplusEngine.parse_id(cfg),
    DaisoKrEngine.engine_code(): lambda cfg: DaisoKrEngine.parse_id(cfg),
}

_SERVICE_ITEM_TARGET_PARSER = {
    CoupangEngine.engine_code(): lambda cfg: CoupangEngine.target_id(cfg),
    GsTheFreshEngine.engine_code(): lambda cfg: GsTheFreshEngine.target_id(cfg),
    IdusEngine.engine_code(): lambda cfg: IdusEngine.target_id(cfg),
    KurlyEngine.engine_code(): lambda cfg: KurlyEngine.target_id(cfg),
    NcncEngine.engine_code(): lambda cfg: NcncEngine.target_id(cfg),
    OasisEngine.engine_code(): lambda cfg: OasisEngine.target_id(cfg),
    OliveyoungEngine.engine_code(): lambda cfg: OliveyoungEngine.target_id(cfg),
    SmartstoreEngine.engine_code(): lambda cfg: SmartstoreEngine.target_id(cfg),
    SsgEngine.engine_code(): lambda cfg: SsgEngine.target_id(cfg),
    RankingdakEngine.engine_code(): lambda cfg: RankingdakEngine.target_id(cfg),
    LotteOnEngine.engine_code(): lambda cfg: LotteOnEngine.target_id(cfg),
    HomeplusEngine.engine_code(): lambda cfg: HomeplusEngine.target_id(cfg),
    DaisoKrEngine.engine_code(): lambda cfg: DaisoKrEngine.target_id(cfg),
}

_SERVICE_ITEM_ENGINE = {
    CoupangEngine.engine_code(): lambda **cfg: CoupangEngine(**cfg),
    GsTheFreshEngine.engine_code(): lambda **cfg: GsTheFreshEngine(**cfg),
    IdusEngine.engine_code(): lambda **cfg: IdusEngine(**cfg),
    KurlyEngine.engine_code(): lambda **cfg: KurlyEngine(**cfg),
    NcncEngine.engine_code(): lambda **cfg: NcncEngine(**cfg),
    OasisEngine.engine_code(): lambda **cfg: OasisEngine(**cfg),
    OliveyoungEngine.engine_code(): lambda **cfg: OliveyoungEngine(**cfg),
    SmartstoreEngine.engine_code(): lambda **cfg: SmartstoreEngine(**cfg),
    SsgEngine.engine_code(): lambda **cfg: SsgEngine(**cfg),
    RankingdakEngine.engine_code(): lambda **cfg: RankingdakEngine(**cfg),
    LotteOnEngine.engine_code(): lambda **cfg: LotteOnEngine(**cfg),
    HomeplusEngine.engine_code(): lambda **cfg: HomeplusEngine(**cfg),
    DaisoKrEngine.engine_code(): lambda **cfg: DaisoKrEngine(**cfg),
}

_SERVICE_DEVICE_PARSER = {
    GsTheFreshDevice.device_code(): lambda cfg: GsTheFreshDevice.create_device_id(
        cfg["number"], cfg["store"]
    ),
}

_SERVICE_DEVICE_GENERATOR = {
    GsTheFreshDevice.device_code(): lambda cfg: GsTheFreshDevice(
        entry_id=cfg["entry_id"],
        gs_device_id=cfg["gs_device_id"],
        access_token=cfg["access_token"],
        refresh_token=cfg["refresh_token"],
        name=cfg["name"],
        number=cfg["number"],
        store=cfg["store"],
        store_name=cfg["store_name"],
    )
}


def create_service_item_url_parser(service_code):
    return _SERVICE_ITEM_URL_PARSER[service_code]


def create_service_item_target_parser(service_code):
    return _SERVICE_ITEM_TARGET_PARSER[service_code]


def has_service_item_target_parser(service_code):
    return service_code in _SERVICE_ITEM_TARGET_PARSER


def create_service_device_parser_and_parse(service_code: str, param: dict = None):
    if service_code in _SERVICE_DEVICE_PARSER:
        return _SERVICE_DEVICE_PARSER[service_code](param)

    return None


def create_service_device_generator(service_code):
    return _SERVICE_DEVICE_GENERATOR[service_code]


def create_service_engine(service_code):
    return _SERVICE_ITEM_ENGINE[service_code]

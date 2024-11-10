from custom_components.price_tracker.services.coupang.engine import CoupangEngine
from custom_components.price_tracker.services.gsthefresh.engine import GsTheFreshEngine
from custom_components.price_tracker.services.idus.engine import IdusEngine
from custom_components.price_tracker.services.kurly.engine import KurlyEngine
from custom_components.price_tracker.services.ncnc.engine import NcncEngine
from custom_components.price_tracker.services.oasis.engine import OasisEngine
from custom_components.price_tracker.services.oliveyoung.engine import OliveyoungEngine
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
}

def create_service_item_url_parser(service_code):
    return _SERVICE_ITEM_URL_PARSER[service_code]

def create_service_item_target_parser(service_code):
    return _SERVICE_ITEM_TARGET_PARSER[service_code]
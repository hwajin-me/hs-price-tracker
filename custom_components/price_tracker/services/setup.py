import voluptuous as vol
from homeassistant import config_entries

from custom_components.price_tracker.components.error import UnsupportedError
from custom_components.price_tracker.components.lang import Lang
from custom_components.price_tracker.components.setup import PriceTrackerSetup
from custom_components.price_tracker.services.coupang.setup import CoupangSetup
from custom_components.price_tracker.services.daiso_kr.setup import DaisoKrSetup
from custom_components.price_tracker.services.gsthefresh.setup import GsthefreshSetup
from custom_components.price_tracker.services.homeplus.setup import HomeplusSetup
from custom_components.price_tracker.services.idus.setup import IdusSetup
from custom_components.price_tracker.services.kurly.setup import KurlySetup
from custom_components.price_tracker.services.lotte_kr.setup import LotteOnKoreaSetup
from custom_components.price_tracker.services.ncnc.setup import NcncSetup
from custom_components.price_tracker.services.oasis.setup import OasisSetup
from custom_components.price_tracker.services.oliveyoung.setup import OliveyoungSetup
from custom_components.price_tracker.services.rankingdak.setup import RankingdakSetup
from custom_components.price_tracker.services.smartstore.setup import SmartstoreSetup
from custom_components.price_tracker.services.ssg.setup import SsgSetup

_SERVICE_TYPE = "service_type"
_SERVICE_SETUP = {
    CoupangSetup.setup_code(): lambda cfg: CoupangSetup(config_flow=cfg),
    GsthefreshSetup.setup_code(): lambda cfg: GsthefreshSetup(config_flow=cfg),
    IdusSetup.setup_code(): lambda cfg: IdusSetup(config_flow=cfg),
    KurlySetup.setup_code(): lambda cfg: KurlySetup(config_flow=cfg),
    NcncSetup.setup_code(): lambda cfg: NcncSetup(config_flow=cfg),
    OasisSetup.setup_code(): lambda cfg: OasisSetup(config_flow=cfg),
    OliveyoungSetup.setup_code(): lambda cfg: OliveyoungSetup(config_flow=cfg),
    SmartstoreSetup.setup_code(): lambda cfg: SmartstoreSetup(config_flow=cfg),
    SsgSetup.setup_code(): lambda cfg: SsgSetup(config_flow=cfg),
    RankingdakSetup.setup_code(): lambda cfg: RankingdakSetup(config_flow=cfg),
    LotteOnKoreaSetup.setup_code(): lambda cfg: LotteOnKoreaSetup(config_flow=cfg),
    HomeplusSetup.setup_code(): lambda cfg: HomeplusSetup(config_flow=cfg),
    DaisoKrSetup.setup_code(): lambda cfg: DaisoKrSetup(config_flow=cfg),
}
_SERVICE_OPTION_SETUP = {
    CoupangSetup.setup_code(): lambda cfg, e: CoupangSetup(
        option_flow=cfg, config_entry=e
    ),
    GsthefreshSetup.setup_code(): lambda cfg, e: GsthefreshSetup(
        option_flow=cfg, config_entry=e
    ),
    IdusSetup.setup_code(): lambda cfg, e: IdusSetup(option_flow=cfg, config_entry=e),
    KurlySetup.setup_code(): lambda cfg, e: KurlySetup(option_flow=cfg, config_entry=e),
    NcncSetup.setup_code(): lambda cfg, e: NcncSetup(option_flow=cfg, config_entry=e),
    OasisSetup.setup_code(): lambda cfg, e: OasisSetup(option_flow=cfg, config_entry=e),
    OliveyoungSetup.setup_code(): lambda cfg, e: OliveyoungSetup(
        option_flow=cfg, config_entry=e
    ),
    SmartstoreSetup.setup_code(): lambda cfg, e: SmartstoreSetup(
        option_flow=cfg, config_entry=e
    ),
    SsgSetup.setup_code(): lambda cfg, e: SsgSetup(option_flow=cfg, config_entry=e),
    RankingdakSetup.setup_code(): lambda cfg, e: RankingdakSetup(
        option_flow=cfg, config_entry=e
    ),
    LotteOnKoreaSetup.setup_code(): lambda cfg, e: LotteOnKoreaSetup(
        option_flow=cfg, config_entry=e
    ),
    HomeplusSetup.setup_code(): lambda cfg, e: HomeplusSetup(
        option_flow=cfg, config_entry=e
    ),
    DaisoKrSetup.setup_code(): lambda cfg, e: DaisoKrSetup(
        option_flow=cfg, config_entry=e
    ),
}
_KIND = {
    CoupangSetup.setup_code(): CoupangSetup.setup_name(),
    GsthefreshSetup.setup_code(): GsthefreshSetup.setup_name(),
    IdusSetup.setup_code(): IdusSetup.setup_name(),
    KurlySetup.setup_code(): KurlySetup.setup_name(),
    NcncSetup.setup_code(): NcncSetup.setup_name(),
    OasisSetup.setup_code(): OasisSetup.setup_name(),
    OliveyoungSetup.setup_code(): OliveyoungSetup.setup_name(),
    SmartstoreSetup.setup_code(): SmartstoreSetup.setup_name(),
    SsgSetup.setup_code(): SsgSetup.setup_name(),
    RankingdakSetup.setup_code(): RankingdakSetup.setup_name(),
    LotteOnKoreaSetup.setup_code(): LotteOnKoreaSetup.setup_name(),
    HomeplusSetup.setup_code(): HomeplusSetup.setup_name(),
    DaisoKrSetup.setup_code(): DaisoKrSetup.setup_name(),
}


def price_tracker_setup_init(hass):
    return vol.Schema(
        {
            vol.Required(_SERVICE_TYPE, default=None): vol.In(_KIND),
            **Lang(hass).selector(),
        }
    )


def price_tracker_setup_service(
    service_type: str = None, config_flow: config_entries.ConfigFlow = None
) -> PriceTrackerSetup | None:
    if service_type is None or config_flow is None:
        """Do nothing"""
        return None

    if service_type not in _SERVICE_SETUP:
        raise UnsupportedError(f"Unsupported service type: {service_type}")

    return _SERVICE_SETUP[service_type](config_flow)


def price_tracker_setup_option_service(
    service_type: str = None,
    option_flow: config_entries.OptionsFlow = None,
    config_entry: any = None,
) -> PriceTrackerSetup | None:
    if service_type is None or option_flow is None:
        """Do nothing"""
        return None

    if service_type not in _SERVICE_OPTION_SETUP:
        raise UnsupportedError(f"Unsupported service type: {service_type}")

    return _SERVICE_OPTION_SETUP[service_type](option_flow, config_entry)


def price_tracker_setup_service_user_input(user_input: dict = None) -> str | None:
    if user_input is None:
        """Do nothing"""
        return None

    return user_input.get(_SERVICE_TYPE)

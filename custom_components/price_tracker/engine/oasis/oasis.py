import logging
import re

from bs4 import BeautifulSoup

from custom_components.price_tracker.engine.data import ItemData, InventoryStatus, ItemUnitType, DeliveryData, \
    DeliveryPayType, ItemUnitData
from custom_components.price_tracker.engine.engine import PriceEngine
from custom_components.price_tracker.exception import InvalidError
from custom_components.price_tracker.utils import request

_LOGGER = logging.getLogger(__name__)
_URL = 'https://m.oasis.co.kr/product/detail/{}'


class OasisEngine(PriceEngine):
    def __init__(self, item_url: str):
        self.item_url = item_url
        id = OasisEngine.getId(item_url)
        self.product_id = id

    async def load(self) -> ItemData:
        response = await request(_URL.format(self.product_id))
        soup = BeautifulSoup(response, "html.parser")
        name = soup.find("div", class_='oDetail_info_group_title').find("h1").get_text()
        price = soup.find("div", class_='discountPrice').get_text().replace("원", "")
        delivery_price = soup.find("dd", class_='deliverySave').get_text().replace("\n", "").replace("\t",
                                                                                                     "") if soup.find(
            "dd",
            class_='deliverySave') is not None else None
        if delivery_price is not None:
            delivery = DeliveryData(
                price=float(delivery_price.replace(",", "").split("원")[0]),
                type=DeliveryPayType.PAID if "이상" in delivery_price else DeliveryPayType.FREE if float(
                    delivery_price.replace(",", "")) == 0 else DeliveryPayType.PAID
            )
        else: DeliveryData(price = 0, type = DeliveryPayType.UNKNOWN)

        for detail_data in soup.find_all("div", class_='oDetail_info_group2'):
            for dd in detail_data.find_all("dd"):
                target_for_unit = dd.get_text().replace("\n", "").replace("\t", "")
                target_unit_regex = re.search(r'(?P<unit>[\d,]+)(?P<type>g|ml|mL|l|L|kg|Kg)당(?: |)(?P<price>[\d,]+)원',
                                              target_for_unit)
                if target_unit_regex is not None:
                    g = target_unit_regex.groupdict()
                    unit = ItemUnitData(
                        price=float(g['price'].replace(",", "")),
                        unit_type=ItemUnitType.of(g['type']),
                        unit=float(g['unit'].replace(",", ""))
                    )

        image = soup.find("li", class_='swiper-slide').find("img")['src']

        return ItemData(
            id=self.product_id,
            name=name,
            price=float(price.replace(",", "")),
            delivery=delivery,
            image=image,
            url=self.item_url,
            inventory=InventoryStatus.IN_STOCK,
            unit=unit
        )

    def id(self) -> str:
        return self.product_id

    @staticmethod
    def getId(item_url: str):
        m = re.search(r'(?P<product_id>[\d\-]+)(?:$|\?.*?$)', item_url)

        if m is None:
            raise InvalidError('Invalid OASIS Product URL {}'.format(item_url))
        g = m.groupdict()

        return g['product_id']
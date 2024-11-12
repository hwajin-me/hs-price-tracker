import json

from bs4 import BeautifulSoup

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.utilities.list import Lu


class CoupangParser:
    _data: dict
    _page_atf: dict

    def __init__(self, text: str):
        try:
            soup = BeautifulSoup(text, "html.parser")
            if soup is not None:
                data = soup.find("script", {"id": "__NEXT_DATA__"}).get_text()
                j = json.loads(data)
                self._data = j
                page_atf = Lu.find_item(
                    j["props"]["pageProps"]["pageList"], 'page', 'PAGE_ATF'
                )
                if page_atf is None:
                    raise DataParseError(
                        "Coupang Parse Error (No ATF) - {}".format(j["props"]["pageProps"]["pageList"])
                    )

                self._page_atf = page_atf["widgetList"]
            else:
                raise DataParseError('Coupang Parser Error (Empty HTML PARSER)')
        except DataParseError as e:
            raise e
        except Exception as e:
            raise DataParseError('Coupang Parser Error') from e

    @property
    def price(self):
        price = Lu.find_item(
            self._page_atf, "viewType", "MWEB_PRODUCT_DETAIL_ATF_PRICE_INFO"
        )

        if price is None:
            raise DataParseError('Coupang Parse Error - MWEB_PRODUCT_DETAIL_ATF_PRICE_INFO not found')

        price_data = price['data']
        original_price = price_data['original_price']['price'] if Lu.has(price_data, 'original_price.price') else None
        currency = 'KRW'
        price = price_data['finalPrice']['price']
        payback_price = 0

        return ItemPriceData(
            original_price=original_price,
            price=price,
            currency=currency,
            payback_price=payback_price
        )

"""Tests"""

from custom_components.price_tracker.services.ssg.engine import SsgEngine


def test_ssg_fetch():
    """Test fetch"""
    engine = SsgEngine(
        item_url="https://emart.ssg.com/item/itemView.ssg?itemId=1000035340991&siteNo=6001&salestrNo=6005&tlidSrchWd=%EA%B3%A0%EA%B8%B0&srchPgNo=1"
    )

    result = engine.load()

    assert result

"""Tests for product creation helpers."""

from app.cms.products import CURRENCY_MAP


class TestCurrencyMapping:
    def test_usd_maps_to_2(self):
        assert CURRENCY_MAP["USD"] == 2

    def test_gbp_maps_to_1(self):
        assert CURRENCY_MAP["GBP"] == 1

    def test_eur_maps_to_3(self):
        assert CURRENCY_MAP["EUR"] == 3

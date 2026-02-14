"""Tests for multi-currency quiz question and currency detection."""

import pytest
from src.skills.base import (
    CURRENCY_SYMBOLS,
    COUNTRY_CURRENCY_MAP,
    LOCATION_OPTIONS,
    currency_for_country,
)
from src.routes.quiz import _detect_country_from_profile


class TestCurrencyForCountry:
    """Test currency_for_country mapping."""

    def test_eu_countries_return_eur(self):
        for code in ["NL", "DE", "FR", "ES", "IT", "BE", "AT", "IE", "PT", "FI"]:
            assert currency_for_country(code) == "EUR", f"{code} should map to EUR"

    def test_uk_returns_gbp(self):
        assert currency_for_country("UK") == "GBP"
        assert currency_for_country("GB") == "GBP"

    def test_us_returns_usd(self):
        assert currency_for_country("US") == "USD"

    def test_au_returns_aud(self):
        assert currency_for_country("AU") == "AUD"

    def test_nz_returns_nzd(self):
        assert currency_for_country("NZ") == "NZD"

    def test_ca_returns_cad(self):
        assert currency_for_country("CA") == "CAD"

    def test_ch_returns_chf(self):
        assert currency_for_country("CH") == "CHF"

    def test_unknown_defaults_to_eur(self):
        assert currency_for_country("XX") == "EUR"
        assert currency_for_country("ZZ") == "EUR"

    def test_case_insensitive(self):
        assert currency_for_country("nl") == "EUR"
        assert currency_for_country("us") == "USD"
        assert currency_for_country("Uk") == "GBP"

    def test_all_currencies_have_symbols(self):
        """Every currency in the country map should have a symbol."""
        currencies_used = set(COUNTRY_CURRENCY_MAP.values())
        for currency in currencies_used:
            assert currency in CURRENCY_SYMBOLS, f"{currency} missing from CURRENCY_SYMBOLS"


class TestLocationOptions:
    """Test LOCATION_OPTIONS consistency."""

    def test_all_options_have_value_and_label(self):
        for opt in LOCATION_OPTIONS:
            assert "value" in opt, f"Option missing 'value': {opt}"
            assert "label" in opt, f"Option missing 'label': {opt}"

    def test_has_other_option(self):
        values = [opt["value"] for opt in LOCATION_OPTIONS]
        assert "OTHER" in values

    def test_has_key_markets(self):
        values = [opt["value"] for opt in LOCATION_OPTIONS]
        for market in ["NL", "DE", "UK", "US", "AU"]:
            assert market in values, f"{market} missing from LOCATION_OPTIONS"


class TestDetectCountryFromProfile:
    """Test _detect_country_from_profile auto-detection."""

    def test_detects_from_headquarters_dict(self):
        profile = {
            "basics": {
                "headquarters": {"value": "Amsterdam, Netherlands", "confidence": "high"}
            }
        }
        assert _detect_country_from_profile(profile) == "NL"

    def test_detects_from_headquarters_string(self):
        profile = {
            "basics": {
                "headquarters": "London, United Kingdom"
            }
        }
        assert _detect_country_from_profile(profile) == "UK"

    def test_detects_usa(self):
        profile = {
            "basics": {
                "headquarters": {"value": "San Francisco, United States", "confidence": "medium"}
            }
        }
        assert _detect_country_from_profile(profile) == "US"

    def test_detects_australia(self):
        profile = {
            "basics": {
                "headquarters": {"value": "Sydney, Australia", "confidence": "high"}
            }
        }
        assert _detect_country_from_profile(profile) == "AU"

    def test_detects_germany(self):
        profile = {
            "basics": {
                "headquarters": {"value": "Berlin, Germany", "confidence": "high"}
            }
        }
        assert _detect_country_from_profile(profile) == "DE"

    def test_returns_none_for_empty_profile(self):
        assert _detect_country_from_profile({}) is None
        assert _detect_country_from_profile(None) is None

    def test_returns_none_for_missing_headquarters(self):
        profile = {"basics": {"name": {"value": "Acme Corp"}}}
        assert _detect_country_from_profile(profile) is None

    def test_returns_none_for_unrecognized_location(self):
        profile = {
            "basics": {
                "headquarters": {"value": "Unknown City, Narnia", "confidence": "low"}
            }
        }
        assert _detect_country_from_profile(profile) is None

    def test_detects_holland_variant(self):
        profile = {
            "basics": {
                "headquarters": {"value": "Rotterdam, Holland", "confidence": "medium"}
            }
        }
        assert _detect_country_from_profile(profile) == "NL"

    def test_detects_england(self):
        profile = {
            "basics": {
                "headquarters": {"value": "Manchester, England", "confidence": "high"}
            }
        }
        assert _detect_country_from_profile(profile) == "UK"

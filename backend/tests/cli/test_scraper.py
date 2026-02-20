"""Tests for CLI website scraper."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.cli.scraper import scrape_ecommerce_site


class TestScrapeEcommerceSite:
    """Test lightweight e-commerce site scraper."""

    @pytest.mark.asyncio
    async def test_successful_scrape_returns_structured_data(self):
        """Successful scrape returns description, products, visible_tech."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <head>
            <title>Cool Fashion Store</title>
            <meta name="description" content="Premium fashion for modern people">
        </head>
        <body>
            <h1>Cool Fashion Store</h1>
            <p>We sell the best fashion items online since 2020.</p>
        </body>
        </html>
        """

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await scrape_ecommerce_site("https://cool-fashion.com")

        assert result["success"] is True
        assert "description" in result
        assert result["title"] == "Cool Fashion Store"

    @pytest.mark.asyncio
    async def test_failed_scrape_returns_empty_with_error(self):
        """Failed scrape returns success=False with error message."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
            mock_client_cls.return_value = mock_client

            result = await scrape_ecommerce_site("https://dead-site.com")

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_detects_shopify(self):
        """Detects Shopify platform from page source."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html><head><title>Store</title>
        <meta name="description" content="A store">
        <link rel="stylesheet" href="//cdn.shopify.com/s/files/theme.css">
        </head><body></body></html>
        """

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await scrape_ecommerce_site("https://shopify-store.com")

        assert "shopify" in result.get("visible_tech", [])

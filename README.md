# 🛒 E-Commerce Price Tracker for Home Assistant

This is a custom component for [Home Assistant](https://www.home-assistant.io/) to track prices of products from e-commerce websites. You can find prices of products from different e-commerce websites like Amazon, Flipkart, etc. This component uses [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) to scrape the prices of products from the websites.

## Installation

> 🚨　We do not recommend installing custom components directly from GitHub.

### HACS (Home Assistant Community Store)

1. Add custom repository to HACS:
   - Go to HACS page in Home Assistant.
   - Click on Integrations.
   - Click on the three dots in the top right corner.
   - Click on Custom repositories.
   - Add the URL of this repository:
2. Add Entry

## Manual

You can add entity to your system by configure button in the integrations page. Upsert Item page requires URL of the product page which you want to track.

### Configurations

- `Product URL`: URL of the product page which you want to track.
- `Management Category Id`: Category Id of the product. Some providers support their own display categories.
- `Refresh interval`: Interval in seconds to refresh the price of the product.
- `Proxy URL`: URL of the proxy server to use for scraping the website. (Optional)

## TODO

- [ ] Support Rakuten
- [ ] Support Mercari
- [ ] Support Amazon Japan
- [ ] Support GS Shop (Korea) / Decrypt TLS Socket Communication
- [ ] Support Proxy and enhance scraping performance

## License

MIT License, see [LICENSE](LICENSE).

### Inspiration, Thanks to 

- [https://github.com/oukene/naver_shopping](https://github.com/oukene/naver_shopping)
- [https://github.com/mahlernim/coupang_price/](https://github.com/mahlernim/coupang_price/)

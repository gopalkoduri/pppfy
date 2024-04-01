import json
import requests
from bs4 import BeautifulSoup
from currency_converter import CurrencyConverter


class AppStorePricing:
    def __init__(
        self,
        url="https://developer.apple.com/help/app-store-connect/reference/financial-report-regions-and-currencies/",
        country_info_file="country-info/data/country-info.json",
    ):
        self.url = url
        self.country_info_file = country_info_file
        self.country_info = self.load_country_info()
        self.currency_info = self.fetch_appstore_currency_info()
        self.currency_converter = CurrencyConverter()

    def load_country_info(self):
        with open(self.country_info_file, "r", encoding="utf-8") as file:
            country_info = json.load(file)
            # Create a mapping from country name to ISO2 code
            return {country["Country"]: country["ISO"] for country in country_info}

    def fetch_appstore_currency_info(self):
        print("Fetching appstore countries and regions information ...")
        response = requests.get(self.url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the table - you may need to adjust the selector based on the actual page structure
        table = soup.find("table")
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        data = []
        for row in table.find_all("tr")[1:]:  # Skip header row
            columns = [col.get_text(strip=True) for col in row.find_all("td")]
            data.append(dict(zip(headers, columns)))

        # Some of the rows have region with multiple countries, let's split them up
        currency_info = {}
        for item in data:
            if item["Region Code"] in ["ZZ", "Z1"]:
                continue
            if "," in item["Countries or Regions"]:
                country_names = [i.strip() for i in item["Countries or Regions"].split(",")]
                for c in country_names:
                    iso_code = self.country_info.get(c, "")
                    if not iso_code:
                        print(c, "has not iso code!")
                    country_info = {
                        "Report Region": item["Report Region"],
                        "Report Currency": item["Report Currency"],
                        "Region Code": iso_code,
                        "Country": c,
                    }
                    currency_info[c] = country_info
            else:
                item["Country"] = item["Countries or Regions"]
                item.pop("Countries or Regions")
                currency_info[item["Country"]] = item

        return currency_info

    def convert_to_appstore_currency(self, iso2_code, price, currency):
        appstore_currency = self.currency_info.get(iso2_code, {}).get("Currency", currency)

        if currency == appstore_currency:
            return appstore_currency, price

        converted_price = self.currency_converter.convert(price, currency, appstore_currency)
        return appstore_currency, converted_price

    def round_off_price(self, price):
        # Implement specific App Store rounding logic here
        return round(price)

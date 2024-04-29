import csv
import json

import requests
from decimal import Decimal
from bs4 import BeautifulSoup

from .store import StorePricing
from .utils import GeoUtils


class AppStorePricing(StorePricing):
    def __init__(self, geo_utils=None):
        super().__init__()

        if geo_utils:
            self.geo_utils = geo_utils
        else:
            self.geo_utils = GeoUtils()

        self.fetch_country_to_store_currency_map()
        self.load_country_to_reference_rounded_prices(
            store_reference_prices_file="resources/appstore_reference_prices.csv"
        )

    def load_country_to_reference_rounded_prices(self, store_reference_prices_file):
        with open(store_reference_prices_file, mode="r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                iso_code = self.geo_utils.get_country_iso_code_from_name(row["Countries or Regions"])
                if iso_code:
                    self.map_country_to_reference_rounded_price[iso_code] = Decimal(row["Price"])
                else:
                    print(f"No ISO code found for {row['Countries or Regions']}")

    def fetch_country_to_store_currency_map(self):
        # Get the data from the appstore's official link
        data_sources = json.load(open("resources/data_sources.json"))
        region_currency_reference_url = data_sources["appstore_region_currency_reference"]
        response = requests.get(region_currency_reference_url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the table - you may need to adjust the selector based on the actual page structure
        table = soup.find("table")
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        data = []
        for row in table.find_all("tr")[1:]:  # Skip header row
            columns = [col.get_text(strip=True) for col in row.find_all("td")]
            data.append(dict(zip(headers, columns)))

        # Some of the rows have region with multiple countries, let's split them up
        self.map_country_to_store_currency = {}
        for item in data:
            if item["Region Code"] in ["ZZ", "Z1"]:
                continue
            if "," in item["Countries or Regions"]:
                country_names = [i.strip() for i in item["Countries or Regions"].split(",")]
                for c in country_names:
                    iso_code = self.geo_utils.get_country_iso_code_from_name(c)
                    if not iso_code:
                        print(c, "has no iso code!")

                    # Countries like Vietnam and Pakistan have their own currencies supported, but are mentioned in WW as well
                    # Keep their own currencies
                    if iso_code in self.map_country_to_store_currency.keys() and item["Region Code"] in [
                        "EU",
                        "LL",
                        "WW",
                    ]:
                        continue

                    country_info = {
                        "Report Region": item["Report Region"],
                        "Report Currency": item["Report Currency"],
                        "Region Code": iso_code,
                        "Country": c,
                    }
                    self.map_country_to_store_currency[iso_code] = country_info
            else:
                item["Country"] = item["Countries or Regions"]
                item.pop("Countries or Regions")
                self.map_country_to_store_currency[item["Region Code"]] = item

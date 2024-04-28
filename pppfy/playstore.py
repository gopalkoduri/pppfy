import csv
import json

import requests
from decimal import Decimal
from bs4 import BeautifulSoup

from .utils import PricingUtils, GeoUtils


class PlayStorePricing:
    def __init__(self):
        self.dup_check = {}
        data_sources = json.load("resources/data_sources.json")
        self.region_currency_reference_url = data_sources["playstore_region_currency_reference"]

        self.country_currency_mapping = {}
        self.fetch_playstore_country_currency_mapping()

        self.country_reference_rounded_prices = {}
        self.load_reference_prices(appstore_reference_prices_file="resources/playstore_reference_prices.csv")

        self.pricing_utils = PricingUtils()
        self.geo_utils = GeoUtils()

    def log(self, iso_code, name, match):
        if iso_code in self.dup_check:
            self.dup_check[iso_code].append((name, match))
        else:
            self.dup_check[iso_code] = [(name, match)]

    def load_reference_prices(self, appstore_reference_prices_file):
        with open(appstore_reference_prices_file, mode="r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                iso_code = self.geo_utils.get_country_iso_code(row["Countries or Regions"])
                if iso_code:
                    self.country_reference_rounded_prices[iso_code] = Decimal(row["Price"])
                    # print(",".join([iso_code, row["Countries or Regions"]]))
                else:
                    print(f"No ISO code found for {row['Countries or Regions']}")

    def fetch_playstore_country_currency_mapping(self):
        print("Fetching appstore countries and regions information ...")
        response = requests.get(self.region_currency_reference_url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the table - you may need to adjust the selector based on the actual page structure
        table = soup.find("table")
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        data = []
        for row in table.find_all("tr")[1:]:  # Skip header row
            columns = [col.get_text(strip=True) for col in row.find_all("td")]
            data.append(dict(zip(headers, columns)))

        # Some of the rows have region with multiple countries, let's split them up
        self.country_currency_mapping = {}
        for item in data:
            if item["Region Code"] in ["ZZ", "Z1"]:
                continue
            if "," in item["Countries or Regions"]:
                country_names = [i.strip() for i in item["Countries or Regions"].split(",")]
                for c in country_names:
                    iso_code = self.geo_utils.get_country_iso_code(c)
                    if not iso_code:
                        print(c, "has no iso code!")

                    # Countries like Vietnam and Pakistan have their own currencies supported, but are mentioned in WW as well
                    # Keep their own currencies
                    if iso_code in self.country_currency_mapping.keys() and item["Region Code"] in ["EU", "LL", "WW"]:
                        continue

                    country_info = {
                        "Report Region": item["Report Region"],
                        "Report Currency": item["Report Currency"],
                        "Region Code": iso_code,
                        "Country": c,
                    }
                    self.country_currency_mapping[iso_code] = country_info
            else:
                item["Country"] = item["Countries or Regions"]
                item.pop("Countries or Regions")
                self.country_currency_mapping[item["Region Code"]] = item

    def local_currency_to_appstore_preferred_currency(self, country_iso2_code, price, country_currency):
        appstore_currency = self.country_currency_mapping.get(country_iso2_code, {}).get(
            "Report Currency", country_currency
        )

        if country_currency == appstore_currency:
            return appstore_currency, price

        converted_price = self.pricing_utils.convert_between_currencies_by_market_xrate(
            price=price, from_currency=country_currency, to_currency=appstore_currency
        )
        return appstore_currency, converted_price

    def round_off_price_to_appstore_format(self, iso2_code, price):
        reference_price = self.country_reference_rounded_prices.get(iso2_code)
        if reference_price is None:
            raise ValueError(f"No reference price found for {iso2_code}")

        price = Decimal(price)  # Convert input price to Decimal
        rounded_price = None
        candidates = []

        # Determine suffix and the appropriate rounding mechanism
        if reference_price == reference_price.to_integral_value():
            ref_price_int_str = str(int(reference_price))
            if ref_price_int_str.endswith("8"):
                candidates = [
                    (price / Decimal("10")).to_integral_value() * Decimal("10") + Decimal("8"),
                    (price / Decimal("10")).to_integral_value() * Decimal("10") - Decimal("2"),
                ]
            elif ref_price_int_str.endswith("99"):
                candidates = [
                    (price / Decimal("100")).to_integral_value() * Decimal("100") + Decimal("99"),
                    (price / Decimal("100")).to_integral_value() * Decimal("100") - Decimal("1"),
                ]
            else:  # also handles case where it endswith("0")
                candidates = [(price / Decimal("10")).to_integral_value() * Decimal("10")]
        else:
            ref_price_str = str(reference_price)
            base_price = price.to_integral_value()

            if ref_price_str.endswith("4.99"):
                candidates = [base_price - (base_price % Decimal("10")) + Decimal("4.99")]
            elif ref_price_str.endswith("4.9"):
                candidates = [base_price - (base_price % Decimal("10")) + Decimal("4.9")]
            elif ref_price_str.endswith("9.98"):
                candidates = [
                    base_price - (base_price % Decimal("10")) + Decimal("9.98"),
                    base_price - (base_price % Decimal("10")) - Decimal("0.02"),
                ]
            elif ref_price_str.endswith("9.99"):
                candidates = [
                    base_price - (base_price % Decimal("10")) + Decimal("9.99"),
                    base_price - (base_price % Decimal("10")) - Decimal("0.01"),
                ]
            elif ref_price_str.endswith("9.9"):
                candidates = [
                    base_price - (base_price % Decimal("10")) + Decimal("9.9"),
                    base_price - (base_price % Decimal("10")) - Decimal("0.1"),
                ]
            elif ref_price_str.endswith("8.99"):
                candidates = [
                    base_price - (base_price % Decimal("10")) + Decimal("8.99"),
                    base_price - (base_price % Decimal("10")) - Decimal("1.01"),
                ]
            else:  # also handles the case where price is *.99
                candidates = [base_price + Decimal("0.99")]

        rounded_price = min(candidates, key=lambda x: abs(x - price))
        return rounded_price

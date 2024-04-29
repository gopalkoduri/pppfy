import csv
import json

import requests
from decimal import Decimal
from bs4 import BeautifulSoup

from .utils import PricingUtils, GeoUtils


class PlayStorePricing:
    def __init__(self):
        self.dup_check = {}
        data_sources = json.load(open("resources/data_sources.json"))
        self.region_currency_reference_url = data_sources["playstore_region_currency_reference"]

        self.country_currency_mapping = {}
        self.fetch_playstore_country_currency_mapping()

        self.country_reference_rounded_prices = {}
        self.load_reference_prices(playstore_reference_prices_file="resources/playstore_reference_prices.csv")

        self.pricing_utils = PricingUtils()
        self.geo_utils = GeoUtils()

    def load_reference_prices(self, playstore_reference_prices_file):
        with open(playstore_reference_prices_file, mode="r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                iso_code = self.geo_utils.get_country_iso_code(row["Country"])
                if iso_code:
                    self.country_reference_rounded_prices[iso_code] = Decimal(row["Price"] / 1000000)
                    # print(",".join([iso_code, row["Country"]]))
                else:
                    print(f"No ISO code found for {row['Country']}")

    def fetch_playstore_country_currency_mapping(self):
        """Process HTML tables to extract and transform data according to the rules."""
        response = requests.get(self.region_currency_reference_url).text
        soup = BeautifulSoup(response, "html.parser")

        tables = soup.find_all("table", class_="nice-table")

        self.country_currency_mapping = {}
        headers = (
            []
        )  # will be 4 items - Location, Download free apps, Make Google Play purchases and Buyer Currency and Price Range

        for index, table in enumerate(tables[:3]):
            rows = table.find_all("tr")
            if index == 0:
                # First row of the first table as header
                headers = [th.get_text().strip() for th in rows[0].find_all("th")]
                rows = rows[1:]  # Exclude the header row from data processing

            for row in rows:
                cols = row.find_all("td")
                if not cols:
                    continue  # skip rows without table data cells

                # Filter based on text color in the third column
                third_col_span = cols[2].find("span")
                if third_col_span and third_col_span.get("class"):
                    if "green-text" not in third_col_span.get("class"):
                        continue  # Exclude rows without check mark

                # Create a list of column values
                row_data = [col.get_text().strip() for i, col in enumerate(cols)]

                # Extract only the capital letters from the fourth column
                if len(row_data) > 3:
                    currency = "".join([c for c in row_data[3] if c.isupper()])
                    row_data[3] = currency

                entry = dict(zip(headers, row_data))
                iso_code = self.geo_utils.get_country_iso_code(entry["Location"])
                self.country_currency_mapping[iso_code] = entry

    def local_currency_to_playstore_preferred_currency(self, country_iso2_code, price, country_currency):
        playstore_currency = self.country_currency_mapping.get(country_iso2_code, {}).get(
            "Buyer Currency and Price Range", country_currency
        )

        if country_currency == playstore_currency:
            return playstore_currency, price

        converted_price = self.pricing_utils.convert_between_currencies_by_market_xrate(
            price=price, from_currency=country_currency, to_currency=playstore_currency
        )
        return playstore_currency, converted_price

    def round_off_price_to_playstore_format(self, iso2_code, price):
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

import csv
import json
from pathlib import Path
from .appstore import AppStorePricing


class Converter:
    def __init__(self, ppp_data_dir="ppp/data", country_info_file="country-info/data/country-info.json"):
        self.ppp_data_dir = Path(ppp_data_dir)
        self.ppp_data_file = self.ppp_data_dir / "ppp-gdp.csv"
        self.country_info_file = Path(country_info_file)
        self.ppp_data = {}
        self.country_info = {}
        self.load_ppp_data()
        self.load_country_info()

    def load_ppp_data(self):
        with open(self.ppp_data_file, mode="r", encoding="utf-8") as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                country_code = row["Country ID"]
                year = int(row["Year"])
                ppp = float(row["PPP"])

                if country_code not in self.ppp_data:
                    self.ppp_data[country_code] = {}

                self.ppp_data[country_code][year] = ppp

    def load_country_info(self):
        with open(self.country_info_file, "r", encoding="utf-8") as file:
            countries = json.load(file)
            for country in countries:
                iso2_code = country["ISO"]
                self.country_info[iso2_code] = {
                    "country": country["Country"],
                    "ISO": iso2_code,
                    "ISO3": country["ISO3"],
                    "currency": country["CurrencyCode"],
                }

    def get_price_mapping(self, source_country="US", source_price=79, destination_country=None, year=None):
        if source_country not in self.ppp_data:
            raise ValueError("Source country data not available")

        mappings = []

        if destination_country:
            countries = [destination_country] if destination_country in self.country_info else []
        else:
            countries = self.ppp_data.keys()

        for iso2_code in countries:
            if year is None:
                cur_pair_year = max(
                    set(self.ppp_data[source_country].keys()).intersection(self.ppp_data[iso2_code].keys())
                )
            else:
                cur_pair_year = year

            source_ppp = self.ppp_data[source_country][cur_pair_year]
            destination_ppp = self.ppp_data[iso2_code][cur_pair_year]
            usd_equivalent_price = source_price / source_ppp
            adjusted_price = usd_equivalent_price * destination_ppp

            mappings.append(
                {
                    "country": self.country_info[iso2_code]["country"],
                    "ISO": iso2_code,
                    "ISO3": self.country_info[iso2_code]["ISO3"],
                    "local_currency": self.country_info[iso2_code]["currency"],
                    "local_price": adjusted_price,
                    "ppp_year": cur_pair_year,
                }
            )

        return mappings if destination_country is None else mappings[0]

    def get_appstore_price_mapping(self, source_country="US", source_price=79, destination_country=None, year=None):
        price_mapping = self.get_price_mapping(source_country, source_price, destination_country, year)
        appstore_pricing = AppStorePricing()

        if isinstance(price_mapping, dict):
            price_mapping = [price_mapping]

        appstore_price_mapping = []
        for mapping in price_mapping:
            iso2_code = mapping["ISO"]
            local_price = mapping["local_price"]
            local_currency = mapping["local_currency"]

            # Is the country featured in appstore list of countries?
            if iso2_code not in appstore_pricing.country_reference_rounded_prices:
                continue

            appstore_currency, appstore_price = appstore_pricing.local_currency_to_appstore_preferred_currency(
                iso2_code, local_price, local_currency
            )

            # Some heavily devalued currencies might end up with very low usd values < 10
            # TODO needs a better fix
            if appstore_price < 10:
                appstore_price = 10

            rounded_price = appstore_pricing.round_off_price_to_appstore_format(iso2_code, appstore_price)

            mapping["appstore_currency"] = appstore_currency
            mapping["appstore_price"] = rounded_price
            appstore_price_mapping.append(mapping)

        return appstore_price_mapping


# Usage
# from pppfy.converter import Converter
# converter = Converter()
# print(converter.get_price_mapping(source_country="US", source_price=79))

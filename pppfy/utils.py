import json
import requests
from decimal import Decimal
from thefuzz import process, fuzz
from currency_converter import CurrencyConverter


class GeoUtils:
    def __init__(self):
        # check this object for insights on errors/mistakes
        self.dup_check = {}

        # iso2: country data map
        self.country_info = {}
        self.fetch_country_info()

        # iso2: all possible names of that country map, used for search
        self.country_iso2_to_names_map = {}
        self.make_country_iso2_to_names_map()

    def log(self, iso_code, name, match):
        if iso_code in self.dup_check:
            self.dup_check[iso_code].append((name, match))
        else:
            self.dup_check[iso_code] = [(name, match)]

    def fetch_country_info(self):
        data_sources = json.load(open("resources/data_sources.json"))
        restcountries_api_endpoint = data_sources["restcountries_api_endpoint"]
        response = requests.get(restcountries_api_endpoint)
        data = response.json()
        for country in data:
            self.country_info[country["cca2"]] = country

    def make_country_iso2_to_names_map(self):
        for iso2, country in self.country_info.items():
            # Compile a set of all possible names
            all_names = set()
            all_names.add(country["name"]["common"].lower())
            all_names.add(country["name"].get("official", "").lower())
            all_names.update([name.lower() for name in country.get("altSpellings", []) if len(name) > 2])
            all_names.update(translation.get("common", "").lower() for translation in country["translations"].values())
            all_names.update(
                translation.get("official", "").lower() for translation in country["translations"].values()
            )

            # Add the country's two-letter code to the all_country_names dictionary
            self.country_iso2_to_names_map[iso2] = all_names

    def get_country_iso_code_from_name(self, name, format="iso2"):
        """name: country name
        format: one of iso2/cca2/iso3/cca3"""
        name = name.lower()

        # Attempt to match with the direct common name or official name
        for iso2, names in self.country_iso2_to_names_map.items():
            if name in names:
                self.log(iso2, name, name + "-direct")
                return iso2 if format in ["iso2", "cca2"] else self.country_info[iso2]["cca3"]

        # Use thefuzz's token_set_ratio for fuzzy matching
        all_names = [item for sublist in self.country_iso2_to_names_map.values() for item in sublist]
        best_match, score = process.extractOne(name, all_names, scorer=fuzz.WRatio)

        # Adjust the score threshold based on your needs
        if score > 80:
            for iso2, names in self.country_iso2_to_names_map.items():
                if best_match in names:
                    self.log(iso2, name, best_match + "-thefuzz")
                    return iso2 if format in ["iso2", "cca2"] else self.country_info[iso2]["cca3"]

        self.log(None, name, "no match")
        return None

    def get_country_currencies(self, iso2_code):
        return self.country_info[iso2_code]["currencies"]

    def get_country_name(self, iso2_code, format="common"):
        """format can be common or official"""
        return self.country_info[iso2_code]["name"][format]


class PricingUtils:
    def __init__(self):
        self.currency_converter = CurrencyConverter()

        data_sources = json.load(open("resources/data_sources.json"))
        self.backup_currency_conversion_api_endpoint = data_sources["backup_currency_conversion_api_endpoint"]

    def convert_between_currencies_by_market_xrate(self, price, from_currency, to_currency):
        try:
            converted_price = self.currency_converter.convert(price, from_currency, to_currency)
        except ValueError:
            response = requests.get(
                f"{self.backup_currency_conversion_api_endpoint}/currencies/{from_currency.lower()}.json"
            )
            currency_exchange_rates = response.json()
            converted_price = price * currency_exchange_rates[from_currency.lower()][to_currency.lower()]

            # Alternative solution using xe.com
            # data = requests.get(
            #     f"https://www.xe.com/currencyconverter/convert/?Amount={price}&From={from_currency}&To={to_currency}"
            # )
            # soup = BeautifulSoup(data, "html.parser")
            # p_element = soup.find("p", class_="sc-1c293993-1 fxoXHw")
            # full_text = p_element.get_text()
            # numeric_text = "".join([char for char in full_text if char.isdigit() or char == "."])
            # converted_price = float(numeric_text)

        return converted_price

    def round_off_price_to_playstore_format(self, source_price_value, reference_price_value):
        # reference_price = self.country_reference_rounded_prices.get(iso2_code)
        # if reference_price_value is None:
        #     raise ValueError(f"No reference price found for {iso2_code}")

        source_price_value = Decimal(source_price_value)  # Convert input price to Decimal
        rounded_price = None
        candidates = []

        # Determine suffix and the appropriate rounding mechanism
        if reference_price_value == reference_price_value.to_integral_value():
            ref_price_int_str = str(int(reference_price_value))
            if ref_price_int_str.endswith("8"):
                candidates = [
                    (source_price_value / Decimal("10")).to_integral_value() * Decimal("10") + Decimal("8"),
                    (source_price_value / Decimal("10")).to_integral_value() * Decimal("10") - Decimal("2"),
                ]
            elif ref_price_int_str.endswith("99"):
                candidates = [
                    (source_price_value / Decimal("100")).to_integral_value() * Decimal("100") + Decimal("99"),
                    (source_price_value / Decimal("100")).to_integral_value() * Decimal("100") - Decimal("1"),
                ]
            else:  # also handles case where it endswith("0")
                candidates = [(source_price_value / Decimal("10")).to_integral_value() * Decimal("10")]
        else:
            ref_price_str = str(reference_price_value)
            base_price = source_price_value.to_integral_value()

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

        rounded_price = min(candidates, key=lambda x: abs(x - source_price_value))
        return rounded_price

    def local_currency_to_playstore_preferred_currency(
        self, price_in_country_currency, country_currency, playstore_currency
    ):
        # playstore_currency = self.country_currency_mapping.get(country_iso2_code, {}).get(
        #     "Buyer Currency and Price Range", country_currency
        # )

        if country_currency == playstore_currency:
            return playstore_currency, price_in_country_currency

        converted_price = self.convert_between_currencies_by_market_xrate(
            price=price_in_country_currency, from_currency=country_currency, to_currency=playstore_currency
        )
        return playstore_currency, converted_price

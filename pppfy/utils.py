import json
import requests
from thefuzz import process, fuzz
from currency_converter import CurrencyConverter


class GeoUtils:
    def __init__(self):
        self.dup_check = {}
        self.country_info = {}
        self.country_names_map = {}
        data_sources = json.load(open("resources/data_sources.json"))
        self.restcountries_api_endpoint = data_sources["restcountries_api_endpoint"]
        self.fetch_country_names_map()

    def log(self, iso_code, name, match):
        if iso_code in self.dup_check:
            self.dup_check[iso_code].append((name, match))
        else:
            self.dup_check[iso_code] = [(name, match)]

    def fetch_country_names_map(self):
        response = requests.get(self.restcountries_api_endpoint)
        self.country_info = response.json()

        for country in self.country_info:
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
            self.country_names_map[country["cca2"]] = all_names

    def get_country_iso_code(self, name):
        name = name.lower()

        # Attempt to match with the direct common name or official name
        for iso_code, names in self.country_names_map.items():
            if name in names:
                self.log(iso_code, name, name + "-direct")
                return iso_code

        # Use thefuzz's token_set_ratio for fuzzy matching
        all_names = [item for sublist in self.country_names_map.values() for item in sublist]
        best_match, score = process.extractOne(name, all_names, scorer=fuzz.WRatio)

        # Adjust the score threshold based on your needs
        if score > 80:
            for iso_code, names in self.country_names_map.items():
                if best_match in names:
                    self.log(iso_code, name, best_match + "-thefuzz")
                    return iso_code

        self.log(None, name, "no match")
        return None


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

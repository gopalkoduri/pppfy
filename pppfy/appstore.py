import csv
import requests
from bs4 import BeautifulSoup
from currency_converter import CurrencyConverter
from thefuzz import process, fuzz


class AppStorePricing:
    def __init__(
        self,
        url="https://developer.apple.com/help/app-store-connect/reference/financial-report-regions-and-currencies/",
    ):
        self.dup_check = {}
        self.url = url
        self.currency_converter = CurrencyConverter()
        self.country_info = {}
        self.country_names_map = {}
        self.fetch_country_names_map()

        self.country_currency_mapping = {}
        self.fetch_appstore_country_currency_mapping()

        self.country_reference_rounded_prices = {}
        self.load_reference_prices(appstore_reference_prices_file="resources/appstore_reference_prices.csv")

    def fetch_country_names_map(self):
        response = requests.get("https://restcountries.com/v3.1/all")
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

    def log(self, iso_code, name, match):
        if iso_code in self.dup_check:
            self.dup_check[iso_code].append((name, match))
        else:
            self.dup_check[iso_code] = [(name, match)]

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

    def load_reference_prices(self, appstore_reference_prices_file):
        with open(appstore_reference_prices_file, mode="r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                iso_code = self.get_country_iso_code(row["Countries or Regions"])
                if iso_code:
                    self.country_reference_rounded_prices[iso_code] = float(row["Price"])
                    # print(",".join([iso_code, row["Countries or Regions"]]))
                else:
                    print(f"No ISO code found for {row['Countries or Regions']}")

    def fetch_appstore_country_currency_mapping(self):
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
        self.country_currency_mapping = {}
        for item in data:
            if item["Region Code"] in ["ZZ", "Z1"]:
                continue
            if "," in item["Countries or Regions"]:
                country_names = [i.strip() for i in item["Countries or Regions"].split(",")]
                for c in country_names:
                    iso_code = self.get_country_iso_code(c)
                    if not iso_code:
                        print(c, "has not iso code!")
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

    def convert_to_appstore_currency(self, iso2_code, price, currency):
        appstore_currency = self.country_currency_mapping.get(iso2_code, {}).get("Report Currency", currency)

        if currency == appstore_currency:
            return appstore_currency, price
        try:
            converted_price = self.currency_converter.convert(price, currency, appstore_currency)
        except ValueError:
            response = requests.get(
                f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{currency.lower()}.json"
            )
            currency_exchange_rates = response.json()
            converted_price = price * currency_exchange_rates[currency.lower()][appstore_currency.lower()]

        return appstore_currency, converted_price

    def round_off_price(self, iso2_code, price):
        reference_price = self.country_reference_rounded_prices.get(iso2_code)
        if reference_price is None:
            raise ValueError(f"No reference price found for {iso2_code}")

        # Implement the App Store's specific price rounding logic
        # If the price is a whole number
        if price.is_integer():
            if price % 10 in (0, 9):
                return price
            else:
                return price - (price % 10) + (9 if price % 10 < 5 else 10)
        # If the price is a float
        else:
            # Calculate the difference from the nearest x.99 price
            lower = round(price) - 0.01  # x.99 below the price
            upper = round(price + 0.99) - 0.01  # x.99 above the price

            # Choose the nearest x.99 or x.98 value
            lower_diff = price - lower
            upper_diff = upper - price

            if lower_diff < upper_diff:
                return lower if str(lower)[-1] != "0" else lower - 0.01  # avoid x.00 prices
            else:
                return upper if str(upper)[-1] != "0" else upper - 0.01  # avoid x.00 prices


if __name__ == "__main__":
    appstore_pricing = AppStorePricing()

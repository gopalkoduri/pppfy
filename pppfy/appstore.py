import requests
from bs4 import BeautifulSoup
from currency_converter import CurrencyConverter


class AppStorePricing:
    def __init__(
        self,
        url="https://developer.apple.com/help/app-store-connect/reference/financial-report-regions-and-currencies/",
    ):
        self.url = url
        self.currency_info = self.fetch_appstore_currency_info()
        self.currency_converter = CurrencyConverter()

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
        countries = []
        for item in data:
            if "," in item["Countries or Regions"]:
                countries = [i.strip() for i in item["Countries or Regions"].split(",")]
                for c in countries:
                    country_info = {
                        "Report Region": item["Report Region"],
                        "Report Currency": item["Report Currency"],
                        "Region Code": "",
                        "Country": c,
                    }
                    countries.append(country_info)
            else:
                item["Country"] = item["Countries or Regions"]
                item.pop("Countries or Regions")
                countries.append(item)

        # Convert data to a dictionary with country codes as keys
        currency_info = {item["Country"]: item for item in data}
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


# # Example usage
# app_store_pricing = AppStorePricing()
# iso2_code = "US"
# local_currency = "USD"
# local_price = 10  # Example price
# appstore_currency, converted_price = app_store_pricing.convert_to_appstore_currency(
#     iso2_code, local_price, local_currency
# )
# rounded_price = app_store_pricing.round_off_price(converted_price)

# print(f"Original price: {local_price} {local_currency}")
# print(f"Converted price: {converted_price} {appstore_currency}")
# print(f"Rounded price: {rounded_price} {appstore_currency}")

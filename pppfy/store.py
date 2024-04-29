from abc import ABC, abstractmethod


class StorePricing(ABC):
    def __init__(self):
        # A map of iso2_code: 3 letter ISO code for the currency used for that country in playstore
        self.map_country_to_store_currency = {}

        # A map of iso2_code: price
        self.map_country_to_reference_rounded_price = {}

    @abstractmethod
    def fetch_country_to_store_currency_map(store_reference_prices_file):
        """
        Get the recent most information on the currency that a given store supports for a given country
        """
        pass

    @abstractmethod
    def load_country_to_reference_rounded_prices():
        """
        Load, from local/network, reference prices for all the countries supported in a given store
        """
        pass

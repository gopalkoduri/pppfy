import csv


class Converter:
    def __init__(self, ppp_data_file="ppp/data/ppp-gdp.csv"):
        # map of country_iso2_code: {year: ppp} data
        self._ppp_data = {}
        self._load_ppp_data(ppp_data_file)

    def _load_ppp_data(self, ppp_data_file):
        with open(ppp_data_file, mode="r", encoding="utf-8") as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                country_iso2_code = row["Country ID"]
                year = int(row["Year"])
                ppp = float(row["PPP"])

                if country_iso2_code not in self._ppp_data:
                    self._ppp_data[country_iso2_code] = {}

                self._ppp_data[country_iso2_code][year] = ppp

    def get_price_mapping(self, source_country="US", source_price=79, destination_country=None, year=None):
        """
        Calculates the purchasing power parity (PPP) adjusted price from a source country to one or more
        destination countries. If the destination country is specified, the function returns the PPP-adjusted
        price for that country; otherwise, it computes the prices for all available countries.

        Parameters:
            source_country (str): ISO2 code of the source country (default: 'US').
            source_price (int, float): The price in the source country's currency (default: 79).
            destination_country (str, optional): ISO2 code of the destination country. If None, PPP-adjusted
                                                prices are calculated for all countries.
            year (int, optional): The year for which to calculate the PPP. If None, the latest common year
                                between the source and destination countries is used.

        Returns:
            list or dict: A list of dictionaries containing the PPP-adjusted prices and related information
                        for each destination country. If a single destination country is specified, a dictionary
                        is returned instead of a list.

        Raises:
            ValueError: If PPP data for the source country is not available.
        """
        # Ensure the source country's PPP data is available
        if source_country not in self._ppp_data:
            raise ValueError("Source country PPP data not available")

        mappings = []

        # Determine the destination countries to process
        if destination_country:
            destination_countries = [destination_country] if destination_country in self._ppp_data else []
        else:
            destination_countries = self._ppp_data.keys()

        # Iterate through each destination country to compute the adjusted price
        for destination_country_iso2_code in destination_countries:
            # Find the applicable year for PPP data
            if year is None:
                cur_pair_year = max(
                    set(self._ppp_data[source_country].keys()).intersection(
                        self._ppp_data[destination_country_iso2_code].keys()
                    )
                )
            else:
                cur_pair_year = year

            # Retrieve PPP factors from data
            source_ppp = self._ppp_data[source_country][cur_pair_year]
            destination_ppp = self._ppp_data[destination_country_iso2_code][cur_pair_year]

            # Calculate USD equivalent price and adjust it according to the destination country's PPP
            usd_equivalent_price = source_price / source_ppp
            adjusted_price = usd_equivalent_price * destination_ppp

            # Append the result in the mappings list
            mappings.append(
                {
                    "ISO2": destination_country_iso2_code,
                    "ppp_adjusted_local_price": adjusted_price,
                    "ppp_year": cur_pair_year,
                }
            )

        # Return a list of mappings or a single mapping if a specific country is requested
        return mappings if destination_country is None else mappings[0]

    def get_country_ppp(self, country_iso2_code, year=None):
        if country_iso2_code in self._ppp_data:
            if not year:
                year = max(self._ppp_data[country_iso2_code])

            if year in self._ppp_data[country_iso2_code]:
                return self._ppp_data[country_iso2_code][year]
            else:
                raise ("Data not available for the given year")


# Usage
# from pppfy.converter import Converter
# c = Converter()
# print(c.get_price_mapping(source_country="US", source_price=79))

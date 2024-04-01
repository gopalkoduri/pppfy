import csv
from datetime import datetime, timedelta
from pathlib import Path
import subprocess


class Converter:
    def __init__(self, ppp_data_dir="ppp/data"):
        self.ppp_data_dir = Path(ppp_data_dir)
        self.ppp_data_file = self.ppp_data_dir / "ppp-gdp.csv"
        self.ppp_data = {}

        self.check_and_regenerate_data()
        self.load_ppp_data()

    def check_and_regenerate_data(self):
        if self.ppp_data_file.exists():
            file_age = datetime.now() - datetime.fromtimestamp(self.ppp_data_file.stat().st_mtime)
            if file_age.days > 365:
                print("Data file is older than a year, regenerating...")
                subprocess.run(["make", "data"], cwd=self.ppp_data_dir.parent)
        else:
            print("Data file not found, generating now...")
            subprocess.run(["make", "data"], cwd=self.ppp_data_dir.parent)

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

    def get_price_mapping(self, source_country="US", source_price=79, destination_country=None, year=None):
        if source_country not in self.ppp_data:
            raise ValueError("Source country data not available")
        if destination_country not in self.ppp_data:
            raise ValueError("Destination country data not available")

        if year is None:
            year = max(
                set(self.ppp_data[source_country].keys()).intersection(self.ppp_data[destination_country].keys())
            )

        if year not in self.ppp_data[source_country]:
            raise ValueError(f"Data for the year {year} is not available for {source_country}")
        if year not in self.ppp_data[destination_country]:
            raise ValueError(f"Data for the year {year} is not available for {destination_country}")

        source_ppp = self.ppp_data[source_country][year]
        destination_ppp = self.ppp_data[destination_country][year]

        usd_equivalent_price = source_price / source_ppp
        adjusted_price = usd_equivalent_price * destination_ppp
        return adjusted_price

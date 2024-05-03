# PPPfy - Purchasing Power Parity Adjustments

## Overview

PPPfy is a Python package that provides tools for adjusting prices across different countries based on Purchasing Power Parity (PPP). The package includes functionality to convert a price from a source country's currency into its PPP equivalent in another country's currency, using historical PPP data.

**Supports 200+ countries**, that have PPP data available from World Bank.

## Installation

Install the package using pip:

```bash
pip install pppfy
```

## Features

- **Get Price Mapping**: Calculate the PPP-adjusted price from a source country to one or more destination countries.
- **Get Country PPP**: Retrieve the PPP factor for a specific country and year.

## Usage

### Importing the Module

You can import the `Converter` class from the `pppfy` package like this:

```python
from pppfy.converter import Converter
```

### Creating an Instance

Create an instance of the `Converter` class. Optionally, specify a path to a different PPP data file:

```python
c = Converter()
```

### Getting PPP Adjusted Price Mapping

The `get_price_mapping` method is a core feature of the `pppfy` package that allows users to adjust prices from a source country to one or more destination countries based on Purchasing Power Parity (PPP). This method calculates the equivalent price in a destination country's currency, considering the difference in buying power between the source and destination countries.

#### Parameters:

- **source_country (str)**: The ISO2 code of the country from which the price originates. Default is 'US'.
- **source_price (int, float)**: The original price in the source country's currency. For example, if the source price is 79 USD and the source country is the US.
- **destination_country (str, optional)**: The ISO2 code of the destination country for which the PPP-adjusted price is to be calculated. If not specified, the method will calculate PPP-adjusted prices for all countries with available data.
- **year (int, optional)**: The year for which the PPP adjustment should be calculated. If not specified, the method uses the most recent year for which PPP data is available for both the source and destination countries.

#### Returns:

- If a specific destination country is specified, the method returns a dictionary containing:

  - **ISO2**: The ISO2 code of the destination country.
  - **ppp_adjusted_local_price**: The price adjusted for PPP, in the destination country's currency.
  - **ppp_year**: The year of the PPP data used for the calculation.

- If no destination country is specified, the method returns a list of dictionaries, each containing the above fields for each available destination country.

#### Example Usage:

```python
from pppfy.converter import Converter

# Initialize the converter
c = Converter()

# Calculate the PPP-adjusted price from the USA to India
ppp_adjusted_price = c.get_price_mapping(source_country="US", source_price=79, destination_country="IN")
print(ppp_adjusted_price)

# Output:
# {
#   "ISO2": "IN",
#   "ppp_adjusted_local_price": 2400.95,
#   "ppp_year": 2021
# }
```

### Retrieving Country PPP Data

To get the PPP factor for a specific country and year:

```python
ppp_factor = c.get_country_ppp(country_iso2_code="IN", year=2021)
print(ppp_factor)
```

## Contributing

Contributions to pppfy are welcome! Please feel free to submit pull requests or raise issues on the repository.

## License

This project is licensed under the GNU Affero General Public License - see the [LICENSE](LICENSE) file for details.

# PPPfy - Purchasing Power Parity Adjustments

## Overview

PPPfy is a Python package that provides tools for adjusting prices across different countries based on Purchasing Power Parity (PPP). The package includes functionality to convert a price from a source country's currency into its PPP equivalent in another country's currency, using historical PPP data.

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

To get the PPP-adjusted price from the USA to another country, you can use the `get_price_mapping` method:

```python
ppp_adjusted_prices = c.get_price_mapping(source_country="US", source_price=79, destination_country="IN")
print(ppp_adjusted_prices)
```

This method returns a dictionary containing the PPP-adjusted price, the ISO2 code of the destination country, and the year of the PPP data used.

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

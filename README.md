# Installation

## FlareSolverr

Proxy server to bypass Cloudflare protection.

### Linux / MacOS

```
docker-compose up -d
```

### Window

Download the precompiled binary from [here](https://github.com/FlareSolverr/FlareSolverr#precompiled-binaries).

## Crawler

```
pip install poetry
poetry install
```

# Usage

```
usage: batdongsan crawl [-h] [--min-price MIN_PRICE] [--max-price MAX_PRICE] [--price-sell-option PRICE_SELL_OPTION] [--price-rent-option PRICE_RENT_OPTION]
                        [--min-area MIN_AREA] [--max-area MAX_AREA] [--area-option AREA_OPTION] [--city CITY] [--directions [DIRECTIONS ...]] [--n-rooms [N_ROOMS ...]]
                        [--max-result MAX_RESULT] --output-path OUTPUT_PATH [--debug] [--no-use-request]
                        {sell,rent}

positional arguments:
  {sell,rent}           Looking for sell or rent ?

optional arguments:
  -h, --help            show this help message and exit
  --min-price MIN_PRICE
                        Minimum price (in million VND)
  --max-price MAX_PRICE
                        Maximum price (in million VND)
  --price-sell-option PRICE_SELL_OPTION
                        Price sell predefined options. View available options by calling `batdongsan show price-sell`. No-op when search_mode is rent.
  --price-rent-option PRICE_RENT_OPTION
                        Price rent predefined options. View available options by calling `batdongsan show price-rent`. No-op when search_mode is sell.
  --min-area MIN_AREA   Minimum area (in m-squared)
  --max-area MAX_AREA   Maximum area (in m-squared)
  --area-option AREA_OPTION
                        Area predefined options. View available options by calling `batdongsan show area`.
  --city CITY           City code. View available options by calling `batdongsan show city`.
  --directions [DIRECTIONS ...]
                        Direction code. View available options by calling `batdongsan show direction`.
  --n-rooms [N_ROOMS ...]
                        Number of rooms (5 for >= 5 rooms)
  --max-result MAX_RESULT
                        Maximum number of result for one scrape. 0 for infinity [default: 100]
  --output-path OUTPUT_PATH
                        Result output path
  --debug               Save the original html file for debugging purpose [default: False]
  --no-use-request      Use proxy server (slower but could bypass 403 error) instead of the library request [default: False]
```

All filtering options are optional. If one filter for a property is missing, the query result will include items regardless their value of that property, i.e. `poetry run batdongsan crawl sell` will return everything regardless their price, area, location, direction, number of rooms.

## Sell/Rent

Use `poetry run batdongsan crawl sell` for crawling selling price and `poetry run batdongsan crawl rent` for renting one.

## Min price/Max Price/Price sell option/Price rent option

Set the minimum/maximum price (in million VND) for the crawling query, or set the pre-defined price sell/rent option code (integer). The meaning of these options could be found by calling `poetry run batdongsan show price-sell`/`poetry run batdongsan show price-rent`. An example output is shown below:

```
poetry run batdongsan show price-sell
1   : Dưới 500 triệu
2   : 500 - 800 triệu
3   : 800 triệu - 1 tỷ
4   : 1 - 2 tỷ
5   : 2 - 3 tỷ
6   : 3 - 5 tỷ
7   : 5 - 7 tỷ
8   : 7 - 10 tỷ
9   : 10 - 20 tỷ
10  : 20 - 30 tỷ
11  : 30 - 40 tỷ
12  : 40 - 60 tỷ
13  : Trên 60 tỷ
0   : Thỏa thuận
```

The maximum price should be supplied to limit the query range. If the minimum price is missing, it defaults to 0. If the maximum price is missing, the limit will not be considered.

If both maximum price and pre-defined price sell option are supplied, the price sell option takes over. For example if we run `poetry run batdongsan crawl sell --max-price 1000 --price-sell-option 13`, the final result will has their price satisfies "Trên 60 tỷ".

## Min area/Max area/Area option

Set the minimum/maximum area (in m^2) for the crawling query, or set the pre-defined area option code (integer). The meaning of these options could be found by calling `poetry run batdongsan show area`.

The maximum area should be supplied to limit the query range. If the minimum area is missing, it defaults to 0. If the maximum area is missing, the limit will not be considered.

If both maximum area and pre-defined area option are supplied, the area option takes over (same as the price option).

## City

Set the specific city short code for the crawling query. The full corresponding name could be found by running `poetry run batdongsan show city`. An example option could be `--city SG` for searching only in Hồ Chí Minh city.

## Directions

Set the specific directions code (integer) for the crawling query. The full corresponding direction could be found by running `poetry run batdongsan show direction`. Multiple directions could be supplied by using `--directions 1 3`.

## N_rooms

Set the specific number of rooms (integer) for the crawling query. Multiple number of rooms could be supplied by using `--n-rooms 1 3`. Only positive number will be counted, number larger than 5 will be round down to 5 and the meaning is searching for houses with equal or more than 5 rooms. For example `--n-rooms 1 0 -1 5 5 5555 11111 -20` will be equivalent to `--n-rooms 1 5`.

## Max-Result

The maximum number of items the crawler should get before finishing.

## Output path

Where to save the result csv file. Scraped images will also be saved into the same directory.

## Debug

Save the scraped html file to local folder.

## No-use-request

By default the crawler will try to use the `requests` library since it is faster. However, it can be blocked by cloudflare and throws 403 error. In this case, supply this option to force the crawler use the proxy server instead.

# Example Output

```
poetry run batdongsan crawl sell --max-price 500 --area-option 2 --city SG --n-rooms 1 2 --output-path output/sell-sg/result.csv
```

The command above will return the selling price of houses in Hồ Chí Minh:

- Their price is less than 500 million VND.
- Their area is from 30 to 50 m^2.
- They have 1 or 2 bedrooms.

The output is saved to [output/sell-sg/result.csv](output/sell-sg/result.csv).

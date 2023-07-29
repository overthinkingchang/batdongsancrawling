import typing
from pathlib import Path

import typed_argparse as tap

from batdongsan_crawler import BatDongSanCrawler

global_crawler = BatDongSanCrawler()


class ShowArgs(tap.TypedArgs):
    option: typing.Literal[
        "direction", "city", "price-sell", "price-rent", "area"
    ] = tap.arg(positional=True, help="Type of option to show")


def show_option_map(args: ShowArgs):
    option_map = {
        "direction": global_crawler.direction_map,
        "city": global_crawler.city_map,
        "price-sell": global_crawler.price_sell_map,
        "price-rent": global_crawler.price_rent_map,
        "area": global_crawler.area_map,
    }
    for k, v in option_map[args.option].items():
        print("{0: <4}: {1}".format(k, v))


class CrawlArgs(tap.TypedArgs):
    search_mode: typing.Literal["sell", "rent"] = tap.arg(
        positional=True, help="Looking for sell or rent ?"
    )

    min_price: typing.Optional[int] = tap.arg(help="Minimum price (in million VND)")
    max_price: typing.Optional[int] = tap.arg(help="Maximum price (in million VND)")

    price_sell_option: typing.Optional[int] = tap.arg(
        help="Price sell predefined options. View available options by calling `batdongsan show price-sell`. No-op when search_mode is rent."
    )
    price_rent_option: typing.Optional[int] = tap.arg(
        help="Price rent predefined options. View available options by calling `batdongsan show price-rent`. No-op when search_mode is sell."
    )

    min_area: typing.Optional[int] = tap.arg(help="Minimum area (in m-squared)")
    max_area: typing.Optional[int] = tap.arg(help="Maximum area (in m-squared)")
    area_option: typing.Optional[int] = tap.arg(
        help="Area predefined options. View available options by calling `batdongsan show area`."
    )

    city: typing.Optional[str] = tap.arg(
        help="City code. View available options by calling `batdongsan show city`."
    )
    directions: typing.Optional[list[int]] = tap.arg(
        help="Direction code. View available options by calling `batdongsan show direction`.",
        nargs="*",
    )
    n_rooms: typing.Optional[list[int]] = tap.arg(
        help="Number of rooms (5 for >= 5 rooms)", nargs="*"
    )

    max_result: int = tap.arg(
        help="Maximum number of result for one scrape. 0 for infinity", default=100
    )
    start_page: int = tap.arg(
        help="Continue searching from this page instead of the first page", default=1
    )

    output_path: Path = tap.arg(help="Result output path")

    debug: bool = tap.arg(
        help="Save the original html file for debugging purpose", default=False
    )

    no_use_request: bool = tap.arg(
        help="Use proxy server (slower but could bypass 403 error) instead of the library request",
        default=False,
    )


def crawl_runner(args: CrawlArgs):
    product_id = (
        global_crawler.product_sell_id
        if args.search_mode == "sell"
        else global_crawler.product_rent_id
    )
    global_crawler.crawl(
        product_id,
        args.city,
        args.min_price,
        args.max_price,
        args.price_sell_option
        if args.search_mode == "sell"
        else args.price_rent_option,
        args.min_area,
        args.max_area,
        args.area_option,
        args.n_rooms,
        args.directions,
        args.max_result,
        args.start_page,
        args.output_path,
        args.debug,
        not args.no_use_request,
    )


def main() -> None:
    tap.Parser(
        tap.SubParserGroup(
            tap.SubParser("show", ShowArgs, help="Show option maps"),
            tap.SubParser("crawl", CrawlArgs, help="Crawl"),
        )
    ).bind(show_option_map, crawl_runner).run()

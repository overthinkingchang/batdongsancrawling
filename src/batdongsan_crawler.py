import math
import os
import typing
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from loguru import logger


class BatDongSanCrawler:
    def __init__(self) -> None:
        self.target_endpoint = "https://batdongsan.com.vn"
        self.proxy_endpoint = "{}://{}:{}/v1".format(
            "https" if os.environ.get("FLARESOLVER_USE_SSL") else "http",
            os.environ.get("FLARESOLVER_HOST", "localhost"),
            os.environ.get("FLARESOLVER_PORT", 8191),
        )

        self.session_id = "batdongsan.com.vn_solver"
        sessions = requests.post(
            self.proxy_endpoint, json={"cmd": "sessions.list"}
        ).json()["sessions"]
        if self.session_id not in sessions:
            logger.info("Session {} notfound. Creating a new one.", self.session_id)
            requests.post(
                self.proxy_endpoint,
                json={"cmd": "sessions.create", "session": self.session_id},
            ).raise_for_status()
        else:
            logger.info("Reusing old session {}.", self.session_id)

        self.solution = self.__get_solution()
        logger.info("Solving cloudflare challenge successfully.")

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.solution["userAgent"]})
        for cookie in self.solution["cookies"]:
            _ = cookie.pop("sameSite")
            http_only = cookie.pop("httpOnly")
            expires = cookie.pop("expiry", None)
            self.session.cookies.set(
                cookie.pop("name"),
                cookie.pop("value"),
                expires=expires,
                rest={"HttpOnly": http_only},
                **cookie
            )

        self.homepage = BeautifulSoup(self.solution["response"], "lxml")
        self.box_search_form = self.homepage.find("form", id="boxSearchForm")
        assert self.box_search_form

        self.product_sell_id, self.product_rent_id = self.__get_product_id()
        logger.debug("Product sell id {}.", self.product_sell_id)
        logger.debug("Product rent id {}.", self.product_rent_id)

        self.direction_map = self.__get_direction_map()
        logger.debug("Direction map {}.", self.direction_map)

        self.city_map = self.__get_city_map()
        logger.debug("City map {}.", self.city_map)

        self.price_sell_map = self.__get_price_sell_map()
        logger.debug("Price sell map {}.", self.price_sell_map)

        self.price_rent_map = self.__get_price_rent_map()
        logger.debug("Price rent map {}.", self.price_rent_map)

        self.area_map = self.__get_area_map()
        logger.debug("Area map {}.", self.area_map)

    def __get_solution(self):
        r = requests.post(
            self.proxy_endpoint,
            json={
                "cmd": "request.get",
                "url": self.target_endpoint,
                "session": self.session_id,
                "maxTimeout": 60000,
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["solution"]

    def __get_product_id(self) -> tuple[int, int]:
        product_htmls = self.box_search_form.select_one(
            "ul.re__product-type-tab.js__product-type"
        ).find_all("li")
        sell_id, rent_id = 0, 0
        for product_html in product_htmls:
            if product_html.text.strip() == "Nhà đất bán":
                sell_id = int(product_html["data-type"])
            elif product_html.text.strip() == "Nhà đất cho thuê":
                rent_id = int(product_html["data-type"])
        assert sell_id
        assert rent_id
        return sell_id, rent_id

    def __get_direction_map(self) -> dict[int, str]:
        direction_htmls = self.box_search_form.find(
            "div", string="Đông - Nam"
        ).parent.find_all("div")
        return {
            int(direction_html["data-value"]): direction_html.text.strip()
            for direction_html in direction_htmls
        }

    def __get_city_map(self) -> dict[str, str]:
        city_htmls = self.box_search_form.find(
            lambda tag: tag.name == "span" and tag.text.strip() == "Tất cả Tỉnh/Thành"
        ).parent.parent.find_all("li")
        return {
            city_html["value"]: city_html.text.strip()
            for city_html in city_htmls
            if "value" in city_html.attrs
        }

    def __get_price_sell_map(self) -> dict[int, str]:
        prices_htmls = self.box_search_form.find(
            "div", class_="js__sell-price-select-list"
        ).find_all("li")
        return {
            int(prices_html["value"]): prices_html.text.strip()
            for prices_html in prices_htmls
            if "value" in prices_html.attrs
        }

    def __get_price_rent_map(self) -> dict[int, str]:
        prices_htmls = self.box_search_form.find(
            "div", class_="js__rent-price-select-list"
        ).find_all("li")
        return {
            int(prices_html["value"]): prices_html.text.strip()
            for prices_html in prices_htmls
            if "value" in prices_html.attrs
        }

    def __get_area_map(self) -> dict[int, str]:
        area_htmls = self.box_search_form.find(
            lambda tag: tag.name == "span" and tag.text.strip() == "Tất cả diện tích"
        ).parent.parent.find_all("li")
        return {
            int(area_html["value"]): area_html.text.strip()
            for area_html in area_htmls
            if "value" in area_html.attrs
        }

    def crawl(
        self,
        product_id: int,
        city_code: typing.Optional[str],
        min_price: typing.Optional[int],
        max_price: typing.Optional[int],
        price_option: typing.Optional[int],
        min_area: typing.Optional[int],
        max_area: typing.Optional[int],
        area_option: typing.Optional[int],
        n_rooms: typing.Optional[list[int]],
        directions: typing.Optional[list[int]],
        max_result: int,
        output_path: Path,
        debug: bool,
    ):
        n_rooms_str = []
        if n_rooms is not None:
            for n_room in n_rooms:
                if n_room >= 1:
                    n_room_str = str(min(n_room, 5))
                    if n_room_str not in n_rooms_str:
                        n_rooms_str.append(n_room_str)

        search_data = {}
        search_data["ProductType"] = product_id
        search_data["CityCode"] = city_code or ""

        if price_option is not None:
            search_data["PriceAsString"] = price_option
        elif max_price is not None:
            min_price = min_price or 0
            search_data["PriceAsString"] = "[{},{}]".format(min_price, max_price)
        else:
            search_data["PriceAsString"] = ""

        if area_option is not None:
            search_data["AreaAsString"] = area_option
        elif max_area is not None:
            min_area = min_area or 0
            search_data["AreaAsString"] = "[{},{}]".format(min_area, max_area)
        else:
            search_data["AreaAsString"] = ""

        search_data["RoomNumersAsString"] = ";".join(n_rooms_str)

        search_data["DirectionsAsString"] = (
            ";".join(map(str, set(directions))) if directions else ""
        )

        logger.info("Search data {}.", search_data)

        res = self.session.post(
            self.target_endpoint
            + "/microservice-architecture-router/Product/ProductSearch",
            data=search_data,
        )

        max_result_real = max_result or math.inf
        results = []

        while len(results) < max_result_real:
            res.raise_for_status()
            soup = BeautifulSoup(res.content, "lxml")
            products_html = soup.find_all("a", "js__product-link-for-product-id")
            results += [self.__parse_html(product) for product in products_html]

            if debug:
                with open("{}.html".format(len(results)), "w") as f:
                    f.write(str(soup))

            next_page_icon = soup.select_one(
                "a.re__pagination-icon>i.re__icon-chevron-right--sm"
            )
            if not next_page_icon:
                break
            next_page_path = next_page_icon.parent["href"]
            res = self.session.get(self.target_endpoint + next_page_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(results).to_csv(output_path, index=False)

    def __parse_number(self, content: str):
        return float(content.replace(".", "").replace(",", "."))

    def __parse_html(self, item):
        data = {}
        data["id"] = item["data-product-id"]
        data["title"] = item.find("div", class_="re__card-info")["title"]
        data["href"] = item["href"]

        config = item.select_one("div.re__card-config.js__card-config")
        data["price"] = config.find("span", class_="re__card-config-price").text
        data["area_m2"] = self.__parse_number(
            config.find("span", class_="re__card-config-area").text.removesuffix("m²")
        )

        bedroom_config = config.find("span", class_="re__card-config-bedroom")
        data["n_room"] = int(bedroom_config.text) if bedroom_config else None

        wc_config = config.find("span", class_="re__card-config-toilet")
        data["n_wc"] = int(wc_config.text) if wc_config else None

        location_raw = item.find("div", class_="re__card-location").find_all("span")[-1]
        district, city = location_raw.text.split(", ")
        data["district"] = district
        data["city"] = city

        return data

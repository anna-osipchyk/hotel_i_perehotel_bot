import datetime

import requests
import os
import json

from telebot.types import InputMediaPhoto

from botrequests.query import Query
from database import Database
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("x-rapidapi-key")


class QueryBestdeal(Query):
    """
    Класс-наследник для обработки команды bestdeal
    Все методы реализованы по аналогии с родительским классом, только с добавлением новых данных
    """

    def __init__(self, bot, user_id):
        super().__init__(bot, user_id)
        self.min_price = None
        self.max_price = None
        self.miles = None
        self.sorting = "PRICE"

    def db_get_tuple(self):
        Database.sql.execute(
            f"SELECT city_of_destination, number_of_variants, number_of_photos, arrival, departure, "
            f"miles, min_price, max_price FROM users WHERE user_id = {self.user_id}"
        )

        tuple_of_data = Database.sql.fetchall()[-1]
        self.city_of_destination = tuple_of_data[0]
        self.number_of_variants = int(tuple_of_data[1])
        self.number_of_photos = int(tuple_of_data[2])
        self.arrival, self.departure = tuple_of_data[3], tuple_of_data[4]
        self.miles = tuple_of_data[5]
        self.min_price, self.max_price = tuple_of_data[6], tuple_of_data[7]

    def for_each_variant(self, variant):
        (
            name,
            address,
            price,
            overall_price,
            distance,
            urls,
            url,
        ) = super().for_each_variant(variant)
        miles = distance.replace(" км", "")
        km = float(miles.replace(",", "."))
        if km > self.miles:
            return None
        return name, address, price, overall_price, distance, urls, url

    def get_response(self, user_data):
        self.db_insert(user_data)
        self.logger.info("Insert запрос в базу данных завершен")
        self.db_get_tuple()
        self.logger.info(
            "Select запрос в базу данных завершен. Необходимые данные получены"
        )
        querystring = {"query": self.city_of_destination, "locale": "ru"}
        response = requests.request(
            "GET", self.URL, headers=self.HEADERS, params=querystring
        )
        dict_of_response = json.loads(response.text)
        self.logger.info(
            f"Ответ 1 от сервера получен со статус кодом {response.status_code}"
        )
        try:
            destination_id = dict_of_response["suggestions"][0]["entities"][1][
                "destinationId"
            ]
            querystring = {
                "destinationId": destination_id,
                "pageNumber": "1",
                "pageSize": "25",
                "checkIn": str(self.arrival),
                "priceMin": str(self.min_price),
                "priceMax": self.max_price,
                "checkOut": self.departure,
                "adults1": "1",
                "sortOrder": self.sorting,
                "locale": "ru_RU",
                "currency": "USD",
            }

            response = requests.request(
                "GET",
                self.URL_COMMAND,
                headers=self.HEADERS_COMMAND,
                params=querystring,
            )
            dict_of_response = json.loads(response.text)
            self.logger.info(
                f"Ответ 2 от сервера получен со статус кодом {response.status_code}"
            )
            list_of_variants = dict_of_response["data"]["body"]["searchResults"][
                "results"
            ]
            count_of_valid_variants = 0
            for variant in list_of_variants:
                if (
                    count_of_valid_variants == self.number_of_variants
                    or count_of_valid_variants > len(list_of_variants)
                ):
                    break
                try:
                    (
                        name,
                        address,
                        price,
                        overall_price,
                        distance,
                        urls,
                        url,
                    ) = self.for_each_variant(variant)
                    count_of_valid_variants += 1
                    if urls is not None:
                        urls = urls.copy()
                    current_data = {
                        "Название отеля": name,
                        "Адрес": address,
                        "Стоимость": price,
                        "Общая стоимость": overall_price,
                        "Расстояние от центра": distance,
                        "Фотографии": urls,
                        "Подробнее": url,
                    }
                    uploaded_at = datetime.datetime.today().strftime("%Y-%m-%d %H.%M")
                    hotel_data = {
                        "user_id": self.user_id,
                        "name": name,
                        "address": address,
                        "price": price,
                        "url": url,
                        "distance": distance,
                        "uploaded_at": uploaded_at,
                    }
                    self.db_insert_hotel_data(hotel_data)
                    photos = current_data.pop("Фотографии")
                    string = "\n".join(
                        [key + ": " + value for key, value in current_data.items()]
                    )
                    self.bot.send_message(
                        user_data["id"], string, disable_web_page_preview=True
                    )
                    if photos is not None:
                        photos_tg = [InputMediaPhoto(media=el) for el in photos]
                        self.bot.send_media_group(user_data["id"], photos_tg)

                except Exception as e:
                    self.logger.error(e)
                    continue

        except Exception as e:
            self.logger.error(e)
            return e
        else:
            return 0

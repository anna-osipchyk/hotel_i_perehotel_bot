import datetime
import logging
from typing import Optional

import requests
import os
import json

from telebot.types import InputMediaPhoto

from database import Database
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("x-rapidapi-key")


class Query:
    """
    Базовый класс для формирования и обработки запроса на основе пользовательских данных;
    создания select и insert запросов в базу данных; формирования и обработки полученного от api ответа;
    отсылки ответа пользователю
    """

    # urls & headers, необходимые для формирования запроса к api
    URL_COMMAND = "https://hotels4.p.rapidapi.com/properties/list"
    URL_GETPHOTOS = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"

    HEADERS_COMMAND = {
        "x-rapidapi-host": "hotels4.p.rapidapi.com",
        "x-rapidapi-key": API_KEY,
    }
    URL = "https://hotels4.p.rapidapi.com/locations/v2/search"
    HEADERS = {"x-rapidapi-host": "hotels4.p.rapidapi.com", "x-rapidapi-key": API_KEY}
    HEADERS_GETPHOTOS = {
        "x-rapidapi-host": "hotels4.p.rapidapi.com",
        "x-rapidapi-key": API_KEY,
    }

    def __init__(self, bot, user_id: int) -> None:
        """
        Конструктор класса.
            :param user_id: id пользователя сессии
            :param bot: сам бот
        """
        self.logger = logging.getLogger(__name__)
        consoleHandler = logging.StreamHandler()
        self.logger.addHandler(consoleHandler)
        logging.basicConfig(
            filename="logging.log",
            level=logging.INFO,
            format="%(asctime)s - [%(levelname)s]  - (%(filename)s).%(funcName)s(%(lineno)d) - %("
            "message)s",
        )
        self.bot = bot
        self.user_id = user_id
        self.departure = None
        self.number_of_photos = None
        self.number_of_variants = None
        self.city_of_destination = None
        self.arrival = None
        self.sorting = "PRICE"

    @staticmethod
    def db_insert(user_data: dict) -> None:
        """
        Insert-запрос в базу данных
            :param user_data: словарь пользовательских данных
        """
        Database.insert(user_data)

    @staticmethod
    def db_insert_hotel_data(hotel_data: dict) -> None:
        """
        Select-запрос в базу данных
            :param hotel_data: словарь данных об отеле
        """
        Database.insert_hotels(hotel_data)

    def db_get_tuple(self) -> None:
        """
        Select-запрос в базу данных. Получение кортежа с пользовательскими данными
        """
        Database.sql.execute(
            f"SELECT city_of_destination, number_of_variants, number_of_photos, arrival, departure, "
            f"user_id "
            f"FROM users WHERE user_id = {self.user_id}"
        )
        tuple_of_data = Database.sql.fetchall()[-1]
        self.city_of_destination = tuple_of_data[0]
        self.number_of_variants = int(tuple_of_data[1])
        self.number_of_photos = int(tuple_of_data[2])
        self.user_id = tuple_of_data[5]
        self.arrival, self.departure = tuple_of_data[3], tuple_of_data[4]

    def get_photos(self, number_of_photos: int, hotel_id: int) -> list:
        """
        Запрос к api для получения фотографий
            :param number_of_photos: количество фотографий
            :param hotel_id: id отеля
            :return: список полученных фотографий
        """
        querystring_getphotos = {"id": hotel_id}
        response = requests.request(
            "GET",
            self.URL_GETPHOTOS,
            headers=self.HEADERS_GETPHOTOS,
            params=querystring_getphotos,
        )
        dict_of_response = json.loads(response.text)
        images = dict_of_response["hotelImages"]
        urls = [
            image["baseUrl"].format(size=image["sizes"][0]["suffix"])
            for image in images
        ]
        if len(urls) > number_of_photos:
            return urls[:number_of_photos]
        return urls

    def for_each_variant(self, variant: dict) -> tuple:
        """
        Получение необходимых данных в готовом виде для формирования ответа пользователю:
            :param variant: полученный от api вариант отеля/хостела/апартаментов
            :return: красиво-упакованные данные для ответа пользователю
        """
        urls = None
        if self.number_of_photos > 0:
            hotel_id = variant["id"]
            urls = self.get_photos(self.number_of_photos, hotel_id)
        name = variant["name"]
        address = variant["address"].get("streetAddress", "🤔")
        price = variant["ratePlan"]["price"]["current"]
        d1 = datetime.datetime.strptime(self.arrival, "%Y-%m-%d")
        d2 = datetime.datetime.strptime(self.departure, "%Y-%m-%d")
        overall_price = "$" + str(
            int(variant["ratePlan"]["price"]["exactCurrent"]) * (d2 - d1).days
        )
        distance = variant["landmarks"][0]["distance"]
        url = f"https://ru.hotels.com/ho{variant['id']}"
        return name, address, price, overall_price, distance, urls, url

    def get_response(self, user_data: dict) -> Optional:
        """
        Получение ответа от api в сыром виде (json-объект)
            :param user_data: пользовательские данные
            :return: либо исключение, либо 0 при успешной отработке
        """
        self.db_insert(user_data)
        self.logger.info("Insert запрос в базу данных завершен")
        self.db_get_tuple()
        self.logger.info(
            "Select запрос в базу данных завершен. Необходимые данные получены"
        )
        querystring = {"query": self.city_of_destination, "locale": "ru_RU"}
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
                "checkIn": self.arrival,
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
            for i, variant in enumerate(list_of_variants):
                if i == self.number_of_variants or i > len(list_of_variants):
                    break
                (
                    name,
                    address,
                    price,
                    overall_price,
                    distance,
                    urls,
                    url,
                ) = self.for_each_variant(variant)
                if urls is not None:
                    urls = urls.copy()
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
                current_data = {
                    "Название отеля": name,
                    "Адрес": address,
                    "Стоимость": price,
                    "Общая стоимость": overall_price,
                    "Расстояние от центра": distance,
                    "Фотографии": urls,
                    "Подробнее": url,
                }
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
            return e
        else:
            return 0

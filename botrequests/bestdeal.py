import datetime

import requests
import os
import json

from telebot.types import InputMediaPhoto

from botrequests.query import Query
from database import Database
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('x-rapidapi-key')


class QueryBestdeal(Query):

    def __init__(self, bot):
        super().__init__(bot)
        self.min_price = None
        self.max_price = None
        self.miles = None
        self.sorting = "PRICE"

    def db_get_tuple(self):
        Database.sql.execute('SELECT city_of_destination, number_of_variants, number_of_photos, arrival, departure, '
                             'miles, min_price, max_price FROM users')

        tuple_of_data = Database.sql.fetchall()[-1]
        self.city_of_destination = tuple_of_data[0]
        self.number_of_variants = int(tuple_of_data[1])
        self.number_of_photos = int(tuple_of_data[2])
        self.arrival, self.departure = tuple_of_data[3], tuple_of_data[4]
        self.miles = tuple_of_data[5]
        self.min_price, self.max_price = tuple_of_data[6], tuple_of_data[7]

    def for_each_variant(self, variant):
        name, address, price, overall_price, distance, urls, url = super().for_each_variant(variant)
        miles = int(distance.replace(" miles", ""))
        if miles > self.miles:
            print('its none')
            return None
        return name, address, price, overall_price, distance, urls, url

    def get_response(self, user_data):
        self.db_insert(user_data)
        self.db_get_tuple()
        querystring = {"query": self.city_of_destination, "locale": "ru"}
        response = requests.request("GET", self.URL, headers=self.HEADERS, params=querystring)
        dict_of_response = json.loads(response.text)
        print("database is ok")
        try:
            destination_id = dict_of_response['suggestions'][0]['entities'][1]['destinationId']
            print(destination_id)
            querystring = {"destinationId": destination_id, "pageNumber": "1", "pageSize": "25",
                           "checkIn": str(self.arrival), "priceMin": str(self.min_price), "priceMax": self.max_price,
                           "checkOut": self.departure, "adults1": "1", "sortOrder": self.sorting, "locale": "ru",
                           "currency": "USD"}

            response = requests.request("GET", self.URL_COMMAND, headers=self.HEADERS_COMMAND,
                                        params=querystring)
            dict_of_response = json.loads(response.text)
            print("json is correct")
            list_of_variants = dict_of_response['data']["body"]["searchResults"]["results"]
            print("lov is correct")
            count_of_valid_variants = 0
            for variant in list_of_variants:
                print(self.number_of_variants)
                if count_of_valid_variants == self.number_of_variants or count_of_valid_variants > len(
                        list_of_variants):
                    break
                try:
                    name, address, price, overall_price, distance, urls, url = self.for_each_variant(variant)
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
                        "Подробнее": url
                    }
                    uploaded_at = datetime.datetime.today().strftime("%Y-%m-%d %H.%M")
                    hotel_data = {"user_id": self.user_id, "name": name, "address": address, "price": price, "url": url,
                                  "distance": distance, "uploaded_at": uploaded_at}
                    self.db_insert_hotel_data(hotel_data)
                    print(current_data)
                    photos = current_data.pop("Фотографии")
                    string = "\n".join([key + ": " + value for key, value in current_data.items()])
                    self.bot.send_message(user_data['id'], string, disable_web_page_preview=True)
                    if photos is not None:
                        photos_tg = [InputMediaPhoto(media=el) for el in photos]
                        self.bot.send_media_group(user_data['id'], photos_tg)

                except Exception as e:
                    print(e)
                    continue

        except Exception as e:
            return e
        else:
            pass
            # return data

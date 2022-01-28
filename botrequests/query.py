from datetime import datetime

import requests
import os
import json

from telebot.types import InputMediaPhoto

from database import Database
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('x-rapidapi-key')




class Query:
    URL_COMMAND = "https://hotels4.p.rapidapi.com/properties/list"
    URL_GETPHOTOS = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"

    HEADERS_COMMAND = {
        'x-rapidapi-host': "hotels4.p.rapidapi.com",
        'x-rapidapi-key': API_KEY
    }
    URL = "https://hotels4.p.rapidapi.com/locations/v2/search"
    HEADERS = {
        'x-rapidapi-host': "hotels4.p.rapidapi.com",
        'x-rapidapi-key': API_KEY
    }
    HEADERS_GETPHOTOS = {
        'x-rapidapi-host': "hotels4.p.rapidapi.com",
        'x-rapidapi-key': API_KEY
    }

    def __init__(self, bot):
        self.bot = bot
        self.departure = None
        self.number_of_photos = None
        self.number_of_variants = None
        self.city_of_destination = None
        self.arrival = None
        self.sorting = "PRICE"

    @staticmethod
    def db_insert(user_data):
        Database.insert(user_data)

    def db_get_tuple(self):
        Database.sql.execute('SELECT city_of_destination, number_of_variants, number_of_photos, arrival, departure '
                             'FROM users')

        tuple_of_data = Database.sql.fetchall()[-1]
        self.city_of_destination = tuple_of_data[0]
        self.number_of_variants = int(tuple_of_data[1])
        self.number_of_photos = int(tuple_of_data[2])
        self.arrival, self.departure = tuple_of_data[3], tuple_of_data[4]

    def get_photos(self, number_of_photos, hotel_id):
        querystring_getphotos = {"id": hotel_id}
        response = requests.request("GET", self.URL_GETPHOTOS, headers=self.HEADERS_GETPHOTOS,
                                    params=querystring_getphotos)
        dict_of_response = json.loads(response.text)
        images = dict_of_response["hotelImages"]
        urls = [image["baseUrl"].format(size=image["sizes"][0]["suffix"]) for image in images]
        if len(urls) > number_of_photos:
            return urls[:number_of_photos]
        return urls

    def for_each_variant(self, variant):
        urls = None
        if self.number_of_photos > 0:
            hotel_id = variant["id"]
            urls = self.get_photos(self.number_of_photos, hotel_id)
            print("urls are correct")
        print(variant)
        name = variant["name"]
        print("name is correct")
        address = variant["address"].get('streetAddress', '🤔')
        print("address is correct")
        price = variant["ratePlan"]["price"]["current"]
        d1 = datetime.strptime(self.arrival, "%Y-%m-%d")
        d2 = datetime.strptime(self.departure, "%Y-%m-%d")
        overall_price = "$" + str(int(variant["ratePlan"]["price"]["exactCurrent"]) * (d2 - d1).days)
        print("price is correct")
        distance = variant["landmarks"][0]["distance"]
        # print(list_of_variants[i]["landmarks"])
        print("distance is correct")
        url = f"https://ru.hotels.com/ho{variant['id']}"
        print(url)
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
            querystring = {"destinationId": destination_id, "pageNumber": "1", "pageSize": "25",
                           "checkIn": self.arrival,
                           "checkOut": self.departure, "adults1": "1", "sortOrder": self.sorting, "locale": "ru",
                           "currency": "BYN"}

            response = requests.request("GET", self.URL_COMMAND, headers=self.HEADERS_COMMAND,
                                        params=querystring)
            dict_of_response = json.loads(response.text)
            print("json is correct")
            list_of_variants = dict_of_response['data']["body"]["searchResults"]["results"]
            print("lov is correct")
            data = []
            for i, variant in enumerate(list_of_variants):
                if i == self.number_of_variants or i > len(list_of_variants):
                    break
                name, address, price, overall_price, distance, urls, url = self.for_each_variant(variant)
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
                photos = current_data.pop("Фотографии")
                string = "\n".join([key + ": " + value for key, value in current_data.items()])
                self.bot.send_message(user_data['id'], string)
                print(string)
                if photos is not None:
                    print("there are photos to send")
                    photos_tg = [InputMediaPhoto(media=el) for el in photos]
                    self.bot.send_media_group(user_data['id'], photos_tg)
                # data.append(
                #     {
                #         "Название отеля": name,
                #         "Адрес": address,
                #         "Стоимость": price,
                #         "Общая стоимость": overall_price,
                #         "Расстояние от центра": distance,
                #         "Фотографии": urls
                #     }
                # )

        except Exception as e:
            return e
        else:
            # return data
            pass

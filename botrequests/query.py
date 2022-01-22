import requests
import os
import json

from botrequests.lowprice import get_photos
from database import Database
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('x-rapidapi-key')


class Query:

    URL = "https://hotels4.p.rapidapi.com/locations/v2/search"
    HEADERS = {
        'x-rapidapi-host': "hotels4.p.rapidapi.com",
        'x-rapidapi-key': API_KEY
    }
    HEADERS_GETPHOTOS = {
        'x-rapidapi-host': "hotels4.p.rapidapi.com",
        'x-rapidapi-key': API_KEY
    }


class QueryLowprice(Query):

    URL_LOWPRICE = "https://hotels4.p.rapidapi.com/properties/list"
    URL_GETPHOTOS = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"

    HEADERS_LOWPRICE = {
        'x-rapidapi-host': "hotels4.p.rapidapi.com",
        'x-rapidapi-key': API_KEY
    }

    def get_photos(self,number_of_photos, hotel_id):
        querystring_getphotos = {"id": hotel_id}

        response = requests.request("GET", self.URL_GETPHOTOS, headers=self.HEADERS_GETPHOTOS, params=querystring_getphotos)
        dict_of_response = json.loads(response.text)
        images = dict_of_response["hotelImages"]
        urls = [image["baseUrl"].format(size=image["sizes"][0]["suffix"]) for image in images]
        if len(urls) > number_of_photos:
            return urls[:number_of_photos]
        return urls

    def lowprice(self, temp_dict):
        Database.insert(temp_dict)
        Database.sql.execute('SELECT city_of_destination, num_of_variants, num_of_photos FROM users')

        tuple_of_data = Database.sql.fetchall()[-1]
        num = int(tuple_of_data[1])
        num_of_photos = int(tuple_of_data[2])
        city = tuple_of_data[0]

        querystring = {"query": city, "locale": "ru"}
        response = requests.request("GET", self.URL, headers=self.HEADERS, params=querystring)

        dict_of_response = json.loads(response.text)
        # print(dict_of_response)
        try:
            destination_id = dict_of_response['suggestions'][0]['entities'][1]['destinationId']
            # print(destination_id)

            querystring_lowprice = {"destinationId": destination_id, "pageNumber": "1", "pageSize": "25",
                                    "checkIn": "2020-01-08",
                                    "checkOut": "2020-01-15", "adults1": "1", "sortOrder": "PRICE", "locale": "ru",
                                    "currency": "BYN"}

            response_lowprice = requests.request("GET", self.URL_LOWPRICE, headers=self.HEADERS_LOWPRICE,
                                                 params=querystring_lowprice)
            print(response_lowprice.text)
            dict_of_response_lowprice = json.loads(response_lowprice.text)
            print("json is correct")
            list_of_variants = dict_of_response_lowprice['data']["body"]["searchResults"]["results"]
            print("lov is correct")
            urls = None
            data = []
            for i in range(num):
                if i == len(list_of_variants):
                    break
                if num_of_photos > 0:
                    hotel_id = list_of_variants[i]["id"]
                    urls = get_photos(num_of_photos, hotel_id)
                    print("urls are correct")

                name = list_of_variants[i]["name"]
                print("name is correct")
                address = list_of_variants[i]["address"]["streetAddress"]
                print("adress is correct")
                price = list_of_variants[i]["ratePlan"]["price"]["current"]
                print("price name is correct")
                distance = list_of_variants[i]["landmarks"][0]["distance"]
                print(list_of_variants[i]["landmarks"])
                print("distance is correct")
                data.append(
                    {
                        "Название отеля": name,
                        "Адрес": address,
                        "Стоимость": price,
                        "Расстояние от центра": distance,
                        "Фотографии": urls
                    }
                )

                print(data)

        except Exception as e:

            return e

        else:
            return data

# URL = "https://hotels4.p.rapidapi.com/locations/search"
# URL_QUERY = "https://hotels4.p.rapidapi.com/properties/list"
# URL_GETPHOTOS = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
#
# HEADERS = {
#     'x-rapidapi-host': "hotels4.p.rapidapi.com",
#     'x-rapidapi-key': API_KEY
# }
# HEADERS_QUERY = {
#     'x-rapidapi-host': "hotels4.p.rapidapi.com",
#     'x-rapidapi-key': API_KEY
# }
# HEADERS_GETPHOTOS = {
#     'x-rapidapi-host': "hotels4.p.rapidapi.com",
#     'x-rapidapi-key': API_KEY
# }
#
#
# def get_photos(number_of_photos, hotel_id):
#     querystring_getphotos = {"id": hotel_id}
#
#     response = requests.request("GET", URL_GETPHOTOS, headers=HEADERS_GETPHOTOS, params=querystring_getphotos)
#     dict_of_response = json.loads(response.text)
#     images = dict_of_response["hotelImages"]
#     urls = [image["baseUrl"].format(size=image["sizes"][0]["suffix"]) for image in images]
#     if len(urls) > number_of_photos:
#         return urls[:number_of_photos]
#     return urls
#
# def put_in_database(temp_dict):
#     Database.insert(temp_dict)
#
# def get_query(temp_dict):
#     Database.insert(temp_dict)
#     Database.sql.execute('SELECT city_of_destination, num_of_variants, num_of_photos FROM users')
#
#     tuple_of_data = Database.sql.fetchall()[-1]
#     num = int(tuple_of_data[1])
#     num_of_photos = int(tuple_of_data[2])
#     city = tuple_of_data[0]
#
#     querystring = {"query": city, "locale": "ru"}
#     response = requests.request("GET", URL, headers=HEADERS, params=querystring)
#
#     dict_of_response = json.loads(response.text)
#     # print(dict_of_response)
#     try:
#         destination_id = dict_of_response['suggestions'][0]['entities'][1]['destinationId']
#         # print(destination_id)
#
#         querystring = {"destinationId": destination_id, "pageNumber": "1", "pageSize": "25",
#                                 "checkIn": "2020-01-08",
#                                 "checkOut": "2020-01-15", "adults1": "1", "sortOrder": "PRICE", "locale": "ru",
#                                 "currency": "BYN"}
#
#         response_url = requests.request("GET", URL_QUERY, headers=HEADERS_QUERY, params=querystring)
#         dict_of_response_lowprice = json.loads(response_url.text)
#         list_of_variants = dict_of_response_lowprice['data']["body"]["searchResults"]["results"]
#
#         urls = None
#         data = []
#         for i in range(num):
#             if i == len(list_of_variants):
#                 break
#             if num_of_photos > 0:
#                 hotel_id = list_of_variants[i]["id"]
#                 urls = get_photos(num_of_photos, hotel_id)
#
#             name = list_of_variants[i]["name"]
#             address = list_of_variants[i]["address"]["streetAddress"]
#             price = list_of_variants[i]["ratePlan"]["price"]["current"]
#             distance = list_of_variants[i]["landmarks"][1]["distance"]
#             data.append(
#                 {
#                     "Название отеля": name,
#                     "Адрес": address,
#                     "Стоимость": price,
#                     "Расстояние от центра": distance,
#                     "Фотографии": urls
#                 }
#             )
#             print(name, address, price, distance, urls)
#
#
#     except Exception as e:
#         return e
#
#     else:
#         return data

import requests
import os
import json

from botrequests.query import Query
from database import Database
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('x-rapidapi-key')


class QueryHighprice(Query):
    URL_HIGHPRICE = "https://hotels4.p.rapidapi.com/properties/list"
    URL_GETPHOTOS = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"

    HEADERS_HIGHPRICE = {
        'x-rapidapi-host': "hotels4.p.rapidapi.com",
        'x-rapidapi-key': API_KEY
    }

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

    def highprice(self, temp_dict):
        Database.insert(temp_dict)
        Database.sql.execute('SELECT city_of_destination, num_of_variants, num_of_photos FROM users')

        tuple_of_data = Database.sql.fetchall()[-1]
        num = int(tuple_of_data[1])
        num_of_photos = int(tuple_of_data[2])
        city = tuple_of_data[0]

        querystring = {"query": city, "locale": "ru"}
        response = requests.request("GET", self.URL, headers=self.HEADERS, params=querystring)

        dict_of_response = json.loads(response.text)
        try:
            destination_id = dict_of_response['suggestions'][0]['entities'][1]['destinationId']
            querystring_highprice = {"destinationId": destination_id, "pageNumber": "1", "pageSize": "25",
                                     "checkIn": "2020-01-08",
                                     "checkOut": "2020-01-15", "adults1": "1", "sortOrder": "PRICE_HIGHEST_FIRST", "locale": "ru",
                                     "currency": "BYN"}

            response_highprice = requests.request("GET", self.URL_HIGHPRICE, headers=self.HEADERS_HIGHPRICE,
                                                  params=querystring_highprice)
            print(response_highprice.text)
            dict_of_response_highprice = json.loads(response_highprice.text)
            print("json is correct")
            list_of_variants = dict_of_response_highprice['data']["body"]["searchResults"]["results"]
            print("lov is correct")
            urls = None
            data = []
            for i in range(num):
                print(list_of_variants[i])
                if i == len(list_of_variants):
                    break
                if num_of_photos > 0:
                    hotel_id = list_of_variants[i]["id"]
                    urls = self.get_photos(num_of_photos, hotel_id)
                    print("urls are correct")

                name = list_of_variants[i]["name"]
                print("name is correct")
                address = list_of_variants[i]["address"].get('streetAddress', '🤔')
                print("address is correct")
                price = list_of_variants[i]["ratePlan"]["price"]["current"]
                print("price name is correct")
                distance = list_of_variants[i]["landmarks"][0]["distance"]
                # print(list_of_variants[i]["landmarks"])
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

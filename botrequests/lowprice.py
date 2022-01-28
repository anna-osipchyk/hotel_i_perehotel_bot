import os

from dotenv import load_dotenv

from botrequests.query import Query

load_dotenv()

API_KEY = os.getenv('x-rapidapi-key')


class QueryLowprice(Query):
    def __init__(self, bot):
        super().__init__(bot)
        self.sorting = "PRICE"

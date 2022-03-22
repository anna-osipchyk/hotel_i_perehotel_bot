import os

from dotenv import load_dotenv

from botrequests.query import Query

load_dotenv()

API_KEY = os.getenv("x-rapidapi-key")


class QueryLowprice(Query):
    """Класс-наследник для обработки команды lowprice"""

    def __init__(self, bot, user_id):
        super().__init__(bot, user_id)
        self.sorting = "PRICE"

import os
from botrequests.query import Query
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("x-rapidapi-key")


class QueryHighprice(Query):
    """Класс-наследник для обработки команды highprice"""

    def __init__(self, bot, user_id):
        super().__init__(bot, user_id)
        self.sorting = "PRICE_HIGHEST_FIRST"

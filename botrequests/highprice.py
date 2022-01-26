import requests
import os
import json
from datetime import date, datetime
from botrequests.query import Query
from database import Database
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('x-rapidapi-key')


class QueryHighprice(Query):

    def __init__(self):
        super().__init__()
        self.sorting = "PRICE_HIGHEST_FIRST"
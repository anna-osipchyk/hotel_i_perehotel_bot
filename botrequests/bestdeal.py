import requests
import os
import json

from botrequests.query import Query
from database import Database
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('x-rapidapi-key')


class QueryBestdeal(Query):
    pass
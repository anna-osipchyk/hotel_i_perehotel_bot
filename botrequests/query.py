import requests
import os
import json

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

import telebot
import os

from telebot.types import InputMediaPhoto

from botrequests.highprice import QueryHighprice
from botrequests.lowprice import QueryLowprice
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv('x-rapidapi-key')
BOT = telebot.TeleBot(TOKEN)


class DialogHandler:
    user_data = {}
    bot = BOT

    def __init__(self, id, command):
        self.response = None
        self.id = id
        self.command = command

    def get_city(self, message):
        self.user_data['city_of_destination'] = message.text
        self.user_data['id'] = message.from_user.id
        self.bot.send_message(message.from_user.id, "Круто! Сколько вариантов тебе показать?")
        self.bot.register_next_step_handler(message, self.get_number_of_variants)

    def get_number_of_variants(self, message):
        try:
            self.user_data['number_of_variants'] = int(message.text)
            if self.user_data['number_of_variants'] <= 0:
                raise Exception
            self.bot.send_message(self.id,
                                  "Замечательно! Уже пробиваю по базам. Нужны ли тебе фотографии? Да/нет")
            self.bot.register_next_step_handler(message, self.get_photos)

        except Exception:
            self.bot.send_message(self.id, " Введи корректное число 👉🏻👈🏻\nСколько вариантов тебе показать?")
            self.bot.register_next_step_handler(message, self.get_number_of_variants)

    def get_photos(self, message):
        are_photos_needed = message.text.lower()
        if are_photos_needed == 'да':
            self.bot.send_message(self.id, "Отлично! Сколько фотографий тебе нужно?")
            self.bot.register_next_step_handler(message, self.get_number_of_photos)
        elif are_photos_needed == 'нет':
            self.bot.send_message(self.id, "Окей, работаю!")
            self.user_data['number_of_photos'] = 0
            self.get_answer()
        else:
            self.bot.send_message(self.id, "Я тебя не понял🥲\nДа или нет?")
            self.bot.register_next_step_handler(message, self.get_photos)

    def get_number_of_photos(self, message):
        number_of_photos = message.text
        try:
            self.user_data['number_of_photos'] = int(number_of_photos)
            self.bot.send_message(self.id, "Понял, работаю...")
            self.get_answer()

        except ValueError:
            self.bot.send_message(self.id,
                                  "Моя твоя не понимать🤯\nДавай попробуем еще раз.\nСколько фотографий показать?")
            self.bot.register_next_step_handler(message, self.get_number_of_photos)

    def get_answer(self):
        print('повезло повезло')
        print(self.user_data)
        return self.user_data

    def get_query(self, user_data):
        ql = None
        if self.command == "/lowprice":
            ql = QueryLowprice()
            self.response = ql.lowprice(user_data)
        elif self.command == "/highprice":
            ql = QueryHighprice()
            self.response = ql.highprice(user_data)
        elif self.command == "/bestdeal":
            ql = QueryBestdeal()
            self.response = ql.bestdeal(user_data)
        if isinstance(self.response, Exception):
            self.bot.send_message(self.id, 'Извини, я ничего не нашел😣')
            return
        self.send_response()

    def send_response(self):
        for result in self.response:
            photos = result.pop("Фотографии")
            print(photos)
            string = "\n".join([key + ": " + value for key, value in result.items()])
            self.bot.send_message(self.id, string)
            print(string)
            if photos is not None:
                print("there are photos to send")
                photos_tg = [InputMediaPhoto(media=el) for el in photos]
                self.bot.send_media_group(self.id, photos_tg)


class DialogHandlerLowprice(DialogHandler):

    def get_answer(self):
        print("Мне повезло повезло я лоупрайс")
        BOT.clear_step_handler_by_chat_id(self.id)
        print(self.user_data)
        self.get_query(self.user_data)


class DialogHandlerHighprice(DialogHandler):

    def get_answer(self):
        print("Мне повезло повезло я хайпрайс")
        print(self.user_data)
        BOT.clear_step_handler_by_chat_id(self.id)
        self.get_query(self.user_data)


class DialogHandlerBestDeal(DialogHandler):

    def get_number_of_variants(self, message):
        try:
            self.user_data['number_of_variants'] = int(message.text)
            if self.user_data['number_of_variants'] <= 0:
                raise Exception
            self.bot.send_message(self.id,
                                  "Замечательно! Введи минимальную стоимость")
            self.bot.register_next_step_handler(message, self.get_min_price)

        except Exception:
            self.bot.send_message(self.id, " Введи корректное число 👉🏻👈🏻\nСколько вариантов тебе показать?")
            self.bot.register_next_step_handler(message, self.get_number_of_variants)

    def get_min_price(self, message):
        try:
            self.user_data["min_price"] = float(message.text)
            self.bot.send_message(self.id, "Супер! Tеперь максимальную")
            self.bot.register_next_step_handler(message, self.get_max_price)
        except Exception:
            self.bot.send_message(self.id, " Введи корректную цену 👉🏻👈🏻")
            self.bot.register_next_step_handler(message, self.get_min_price)

    def get_max_price(self, message):
        try:
            self.user_data["max_price"] = float(message.text)
            if self.user_data["max_price"] <= self.user_data["min_price"]:
                raise Exception
            self.bot.send_message(self.id, "Супер! Теперь введи предпочтительное расстояние от центра")
            self.bot.register_next_step_handler(message, self.get_miles)
        except Exception:
            self.bot.send_message(self.id, " Введи корректную цену 👉🏻👈🏻")
            self.bot.register_next_step_handler(message, self.get_max_price)

    def get_miles(self, message):
        try:
            self.user_data["miles"] = int(message.text)
            if self.user_data["miles"] <= 0:
                raise Exception
            self.bot.send_message(self.id,
                                  "Замечательно! Уже пробиваю по базам. Нужны ли тебе фотографии? Да/нет")
            self.bot.register_next_step_handler(message, self.get_photos)
        except Exception:
            self.bot.send_message(self.id, " Введи корректные данные🥺")
            self.bot.register_next_step_handler(message, self.get_miles)

    def get_answer(self):
        print("Мне повезло повезло я бест деал")
        print(self.user_data)
        BOT.clear_step_handler_by_chat_id(self.id)
        self.get_query(self.user_data)


@BOT.message_handler(commands=["start", "lowprice", "highprice", "bestdeal", "history"])
def get_text_message(message):
    if message.text == '/start':
        BOT.send_message(message.from_user.id, f"Привет, {message.from_user.first_name}!🤗\n\n"
                                               f"Меня зовут {BOT.get_me().first_name},"
                                               f" и я помогу найти подходящий отель в интересующем тебя городе!\n\n"
                                               f"Для навигации по командам отправь мне /help")

    elif message.text in ["/lowprice", "/highprice", "/bestdeal"]:
        BOT.send_message(message.from_user.id, f"Класс, теперь"
                                               f" отправь мне название города,"
                                               f" в котором ты хочешь найти подходящий отель\n✨✨✨\nНапример, Минск")
        if message.text == "/lowprice":
            dh = DialogHandlerLowprice(message.from_user.id, message.text)
        elif message.text == "/highprice":
            dh = DialogHandlerHighprice(message.from_user.id,message.text)
        elif message.text == "/bestdeal":
            dh = DialogHandlerBestDeal(message.from_user.id,message.text)
        BOT.register_next_step_handler(message, dh.get_city)

    elif message.text == '/history':
        pass
        # command = COMMANDS.get(message.text)
        # answer = BOT.register_next_step_handler(message, get_city)
        # print(answer)


@BOT.message_handler(content_types=["text"])
def hello(message):
    if message.text in ["Привет", "/hello_world"]:
        BOT.send_message(message.from_user.id, "И тебе привет!")


if __name__ == '__main__':
    BOT.polling(none_stop=True)

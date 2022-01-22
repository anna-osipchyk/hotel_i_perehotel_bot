import telebot
import os

from telebot.types import InputMediaPhoto

from botrequests.query import *
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv('x-rapidapi-key')
BOT = telebot.TeleBot(TOKEN)


# TEMP_DICT = {'city_of_destination': 0, "id": 0, 'num': 0, 'num_of_photos': 0}
# COMMANDS = {
#     "/lowprice": "lowprice",
#     "/highprice": "highprice",
#     "/bestdeal": "bestdeal",
#     "/history": "history"
# }

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
        if self.command == "/lowprice":
            ql = QueryLowprice()
            self.response = ql.lowprice(user_data)
            print(self.response)
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
                photos_string = "\nФотографии: "
                self.bot.send_media_group(self.id, photos_tg)




class DialogHandlerLowprice(DialogHandler):

    def get_answer(self):
        print("Мне повезло повезло я лоупрайс")
        BOT.clear_step_handler_by_chat_id(self.id)
        print(self.user_data)
        self.get_query(self.user_data)


class DialogHandlerHighprice(DialogHandler):
    def __init__(self, command, id):
        super().__init__(id)
        self.command = command

    def get_answer(self):
        print("Мне повезло повезло я хайпрайс")
        print(self.user_data)
        return self.user_data


class DialogHandlerBestDeal(DialogHandler):
    def __init__(self, command, id):
        super().__init__(id)
        self.command = command

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
        return self.user_data


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

#
# def show_variants(variants, user_id):
#     bot.send_message(user_id, "Смотри, что я нашел:")
#     data = ""
#     for variant in variants:
#         for key in variant.keys():
#             if variant[key] is not None:
#                 data+=str(key)
#                 data+=": "
#                 if isinstance(variant[key], list):
#                     for url in variant[key]:
#                         data+=str(url)+"\n"
#                 else:
#                     data+=str(variant[key])
#             data += "\n"
#         data+="\n"
#     data += "\n"
#     bot.send_message(user_id, data)
#
#
# def get_city(message):
#
#     TEMP_DICT['city_of_destination'] = message.text
#     TEMP_DICT['id'] = message.from_user.id
#     bot.send_message(message.from_user.id, "Круто! Сколько вариантов тебе показать?")
#     bot.register_next_step_handler(message, get_num)
#
#
# def get_num(message): try: TEMP_DICT['num'] = int(message.text) if TEMP_DICT['num'] <= 0: raise Exception
# bot.send_message(message.from_user.id, "Замечательно! Уже пробиваю по базам. Нужны ли тебе фотографии? Да/нет")
# bot.register_next_step_handler(message, get_photos) except ValueError: bot.send_message(message.from_user.id,
# "Я тебя не понял(") except Exception: pass
#
#
# def get_photos(message):
#     are_photos_needed = message.text.lower()
#     if are_photos_needed == 'да':
#         bot.send_message(message.from_user.id, "Отлично! Сколько фотографий тебе нужно?")
#         bot.register_next_step_handler(message, get_num_of_photos)
#     elif are_photos_needed == 'нет':
#         bot.send_message(message.from_user.id, "Окей, работаю!")
#         TEMP_DICT['num_of_photos'] = 0
#         answer = lowprice(TEMP_DICT)
#         if isinstance(answer, Exception):
#             bot.send_message(message.from_user.id, "Данные отсутствуют")
#         else:
#             show_variants(answer, message.from_user.id)
#     else:
#         bot.send_message(message.from_user.id, "Я тебя не понял(")
#
#
# def get_num_of_photos(message):
#     num_of_photos = message.text
#     try:
#         TEMP_DICT['num_of_photos'] = int(num_of_photos)
#         bot.send_message(message.from_user.id, "Понял, работаю...")
#         answer = lowprice(TEMP_DICT)
#         if isinstance(answer, Exception):
#             bot.send_message(message.from_user.id, "Данные отсутствуют")
#         else:
#             show_variants(answer, message.from_user.id)
#
#     except ValueError:
#         bot.send_message(message.from_user.id, "Я тебя не понимаю...")
#
#
# @bot.message_handler(commands=["start", "lowprice", "highprice", "bestdeal", "history"])
# def get_text_message(message):
#     if message.text == '/start':
#         bot.send_message(message.from_user.id, f"Привет, {message.from_user.first_name}!🤗\n\n"
#                                                f"Меня зовут {bot.get_me().first_name},"
#                                                f" и я помогу найти подходящий отель в интересующем тебя городе!\n\n"
#                                                f"Для навигации по командам отправь мне /help")
#     elif message.text in ["/lowprice", "/highprice", "/bestdeal"]:
#         bot.send_message(message.from_user.id, f"Класс, теперь"
#                                                f" отправь мне название города,"
#                                                f" в котором ты хочешь найти подходящий отель.\nНапример, Минск")
#     elif message.text == '/history':
#         pass
#     # command = COMMANDS.get(message.text)
#     bot.register_next_step_handler(message, get_city)
#
#
#
# @bot.message_handler(content_types=["text"])
# def hello(message):
#     if message.text in ["Привет", "/hello_world"]:
#         bot.send_message(message.from_user.id, "И тебе привет!")
#     else:
#
#         url = 'https://exp.cdn-hotels.com/hotels/49000000/48470000/48461200/48461122/9bbd8813_z.jpg'
#
#
#         bot.send_message(message.from_user.id, "Я тебя не понимаю!")
#
#
# if __name__ == '__main__':
#     bot.polling(none_stop=True)

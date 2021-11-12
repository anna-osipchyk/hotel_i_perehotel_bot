import telebot
import os
from botrequests.lowprice import lowprice
from botrequests import query
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv('x-rapidapi-key')
bot = telebot.TeleBot(TOKEN)
TEMP_DICT = {'city_of_destination': 0, "id": 0, 'num': 0, 'num_of_photos': 0}
COMMANDS = {
    "/lowprice": "lowprice",
    "/highprice": "highprice",
    "/bestdeal": "bestdeal",
    "/history": "history"
}


def show_variants(variants, user_id):
    bot.send_message(user_id, "Смотри, что я нашел:")
    data = ""
    for variant in variants:
        for key in variant.keys():
            if variant[key] is not None:
                data+=str(key)
                data+=" "
                data+=str(variant[key])
        data+="\n"
    bot.send_message(user_id, data)


def get_city(message):

    TEMP_DICT['city_of_destination'] = message.text
    TEMP_DICT['id'] = message.from_user.id
    bot.send_message(message.from_user.id, "Круто! Сколько вариантов тебе показать?")
    bot.register_next_step_handler(message, get_num)


def get_num(message):
    try:
        TEMP_DICT['num'] = int(message.text)
        if TEMP_DICT['num'] <= 0:
            raise Exception
        bot.send_message(message.from_user.id, "Замечательно! Уже пробиваю по базам. Нужны ли тебе фотографии? Да/нет")
        bot.register_next_step_handler(message, get_photos)
    except ValueError:
        bot.send_message(message.from_user.id, "Я тебя не понял(")
    except Exception:
        pass


def get_photos(message):
    are_photos_needed = message.text.lower()
    if are_photos_needed == 'да':
        bot.send_message(message.from_user.id, "Отлично! Сколько фотографий тебе нужно?")
        bot.register_next_step_handler(message, get_num_of_photos)
    elif are_photos_needed == 'нет':
        bot.send_message(message.from_user.id, "Окей, работаю!")
        TEMP_DICT['num_of_photos'] = 0
        answer = lowprice(TEMP_DICT)
        if isinstance(answer, Exception):
            bot.send_message(message.from_user.id, "Данные отсутствуют")
        else:
            show_variants(answer, message.from_user.id)
    else:
        bot.send_message(message.from_user.id, "Я тебя не понял(")


def get_num_of_photos(message):
    num_of_photos = message.text
    try:
        TEMP_DICT['num_of_photos'] = int(num_of_photos)
        bot.send_message(message.from_user.id, "Понял, работаю...")
        get_full_answer()
        answer = lowprice(TEMP_DICT)
        if isinstance(answer, Exception):
            bot.send_message(message.from_user.id, "Данные отсутствуют")
        else:
            show_variants(answer, message.from_user.id)

    except ValueError:
        bot.send_message(message.from_user.id, "Я тебя не понимаю...")


@bot.message_handler(commands=["start", "lowprice", "highprice", "bestdeal", "history"])
def get_text_message(message):
    if message.text == '/start':
        bot.send_message(message.from_user.id, f"Привет, {message.from_user.first_name}!🤗\n\n"
                                               f"Меня зовут {bot.get_me().first_name},"
                                               f" и я помогу найти подходящий отель в интересующем тебя городе!\n\n"
                                               f"Для навигации по командам отправь мне /help")
    elif message.text in ["/lowprice", "/highprice", "/bestdeal"]:
        bot.send_message(message.from_user.id, f"Класс, теперь"
                                               f" отправь мне название города,"
                                               f" в котором ты хочешь найти подходящий отель.\nНапример, Минск")
    elif message.text == '/history':
        pass
    # command = COMMANDS.get(message.text)
    bot.register_next_step_handler(message, get_city)



@bot.message_handler(content_types=["text"])
def hello(message):
    if message.text in ["Привет", "/hello_world"]:
        bot.send_message(message.from_user.id, "И тебе привет!")
    else:
        bot.send_message(message.from_user.id, "Я тебя не понимаю!")


if __name__ == '__main__':
    bot.polling(none_stop=True)

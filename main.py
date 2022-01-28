import datetime as dt
from bot_start import BOT
from telebot import types
from telegram_bot_calendar import DetailedTelegramCalendar as Calendar

from botrequests.bestdeal import QueryBestdeal
from botrequests.highprice import QueryHighprice
from botrequests.lowprice import QueryLowprice


def check_dates(date1, date2=None):
    now = dt.date.today()
    if date2 is not None and (date1 < now or date1 > date2):
        return False
    elif date2 is False and (date1 < now):
        return False
    return True


def choose_command_and_create_instance(id, command, message, photos_needed=False):
    dh = None
    if command == "/lowprice":
        dh = DialogHandlerLowprice(id, command)
    elif command == "/highprice":
        dh = DialogHandlerHighprice(id, command)
    elif command == "/bestdeal":
        print("bestdeal is chosen")
        dh = DialogHandlerBestDeal(id, command)
    if photos_needed:
        BOT.register_next_step_handler(message, dh.get_number_of_photos)
    else:
        BOT.register_next_step_handler(message, dh.get_city)


class CommandMixin:
    def __init__(self, command):
        self.command = command


class User(CommandMixin):
    users = {}
    self_like_id = None

    def __init__(self, id, command):
        super().__init__(command)
        self.id = id
        User.add_user(id, self)

    @classmethod
    def add_user(cls, id, user):
        cls.users[id] = user

    @classmethod
    def get_user(cls, id, command=None):
        if id in User.users:
            return User.users[id]
        return User(id, command)

    @staticmethod
    def get_dates(id):
        calendar = Calendar(locale='ru', calendar_id=1).build()[0]
        User.self_like_id = id
        BOT.send_message(id,
                         f"В каком году отправляемся? ",
                         reply_markup=calendar)

    @staticmethod
    @BOT.callback_query_handler(func=lambda call: call.data in ['yes_1', 'yes_2', 'yes_3', 'no_1', 'no_2', 'no_3'])
    def call(c):
        if c.data == "yes_1":
            calendar, step = Calendar(locale='ru', calendar_id=2).build()
            BOT.send_message(c.message.chat.id,
                             f"Здорово! Напиши год, когда ты вернешься: ",
                             reply_markup=calendar)
        elif c.data == "no_1":
            DialogHandler.user_data.pop('arrival')
            calendar, step = Calendar(locale='ru', calendar_id=1).build()
            BOT.send_message(c.message.chat.id,
                             f"Выбери нужный год: ",
                             reply_markup=calendar)

        elif c.data == "yes_2":
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            yes_btn = types.InlineKeyboardButton(text="да", callback_data="yes_3")
            no_btn = types.InlineKeyboardButton(text="нет", callback_data="no_3")
            keyboard.add(yes_btn, no_btn)
            BOT.send_message(c.message.chat.id, "Тебе понадобятся фотографии?", reply_markup=keyboard)

        elif c.data == "no_2":
            DialogHandler.user_data.pop('arrival')
            calendar, step = Calendar(locale='ru', calendar_id=1).build()
            BOT.send_message(c.message.chat.id,
                             f"Выбери нужный год: ",
                             reply_markup=calendar)
        elif c.data == "yes_3":
            BOT.send_message(c.message.chat.id, "Напиши, сколько фотографий тебе показать📸")
            id, command = User.self_like_id, User.users[User.self_like_id].command
            choose_command_and_create_instance(id, command, c.message, True)

        elif c.data == "no_3":
            BOT.send_message(c.message.chat.id, f"Класс, теперь"
                                                f" отправь мне название города,"
                                                f" в котором ты хочешь найти подходящий отель\n✨✨✨\nНапример, Минск")
            id, command = User.self_like_id, User.users[User.self_like_id].command
            choose_command_and_create_instance(id, command, c.message)

    @staticmethod
    @BOT.callback_query_handler(func=Calendar.func(calendar_id=1))
    def call(c):
        step_dict = {'y': 'год', 'm': 'месяц', 'd': 'день'}

        result, key, step = Calendar(locale='ru', calendar_id=1).process(c.data)
        if not result and key:
            BOT.edit_message_text(f"Выбери {step_dict[step]}",
                                  c.message.chat.id,
                                  c.message.message_id,
                                  reply_markup=key)
        elif result:
            DialogHandler.user_data['arrival'] = result
            is_valid = check_dates(DialogHandler.user_data['arrival'], DialogHandler.user_data.get('departure', None))
            if is_valid:
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                yes_btn = types.InlineKeyboardButton(text="да", callback_data="yes_1")
                no_btn = types.InlineKeyboardButton(text="нет", callback_data="no_1")
                keyboard.add(yes_btn, no_btn)
                BOT.send_message(c.message.chat.id, f'Твоя выбранная дата: {result}. Все верно?', reply_markup=keyboard)
            else:
                BOT.send_message(c.message.chat.id, f'Неверная дата! Давай попробуем еще раз')
                calendar, step = Calendar(locale='ru', calendar_id=1).build()
                BOT.send_message(c.message.chat.id,
                                 f"Выбери нужный год: ",
                                 reply_markup=calendar)

    @staticmethod
    @BOT.callback_query_handler(func=Calendar.func(calendar_id=2))
    def call(c):
        step_dict = {'y': 'год', 'm': 'месяц', 'd': 'день'}
        result, key, step = Calendar(locale='ru', calendar_id=2).process(c.data)
        if not result and key:
            BOT.edit_message_text(f"Выбери {step_dict[step]}",
                                  c.message.chat.id,
                                  c.message.message_id,
                                  reply_markup=key)
        elif result:
            DialogHandler.user_data['departure'] = result
            print(DialogHandler.user_data)
            is_valid = check_dates(DialogHandler.user_data['arrival'], DialogHandler.user_data.get('departure', None))
            if is_valid:
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                yes_btn = types.InlineKeyboardButton(text="да", callback_data="yes_2")
                no_btn = types.InlineKeyboardButton(text="нет", callback_data="no_2")
                keyboard.add(yes_btn, no_btn)
                BOT.send_message(c.message.chat.id, f'Твоя выбранная дата: {result}. Все верно?', reply_markup=keyboard)
            else:
                BOT.send_message(c.message.chat.id, f'Неверная дата! Давай попробуем еще раз')
                calendar, step = Calendar(locale='ru', calendar_id=2).build()
                BOT.send_message(c.message.chat.id,
                                 f"Выбери нужный год: ",
                                 reply_markup=calendar)


class DialogHandler(User):
    user_data = {}
    bot = BOT

    def __init__(self, id, command):
        super().__init__(id, command)
        self.response = None

    def get_number_of_photos(self, message):
        number_of_photos = message.text
        try:
            self.user_data['number_of_photos'] = int(number_of_photos)
            self.bot.send_message(self.id, f"Класс, теперь"
                                           f" отправь мне название города,"
                                           f" в котором ты хочешь найти подходящий отель\n✨✨✨\nНапример, Минск")
            self.bot.register_next_step_handler(message, self.get_city)

        except ValueError:
            self.bot.send_message(self.id,
                                  "Моя твоя не понимать🤯\nДавай попробуем еще раз.\nСколько фотографий показать?")
            self.bot.register_next_step_handler(message, self.get_number_of_photos)

    def get_city(self, message):
        self.user_data['city_of_destination'] = message.text
        self.user_data['id'] = message.from_user.id
        self.bot.send_message(self.id,
                              "Сколько вариантов тебе нужно?")
        self.bot.register_next_step_handler(message, self.get_number_of_variants)

    def get_number_of_variants(self, message):
        try:
            self.user_data['number_of_variants'] = int(message.text)
            if self.user_data['number_of_variants'] <= 0:
                raise Exception
            self.bot.send_message(self.id,
                                  "Понял! Работаю...")
            self.get_answer()

        except ValueError as e:
            print(e)
            self.bot.send_message(self.id, " Введи корректное число 👉🏻👈🏻\nСколько вариантов тебе показать?")
            self.bot.register_next_step_handler(message, self.get_number_of_variants)

    def get_answer(self):
        print('повезло повезло')
        print(self.user_data)
        return self.user_data

    def get_query(self, user_data):
        ql = None
        print(user_data)
        if self.command == "/lowprice":
            ql = QueryLowprice(BOT)
        elif self.command == "/highprice":
            ql = QueryHighprice(BOT)
        elif self.command == "/bestdeal":
            ql = QueryBestdeal(BOT)
        self.response = ql.get_response(user_data)
        if isinstance(self.response, Exception):
            self.bot.send_message(self.id, 'Извини, я ничего не нашел😣')
            return
        # self.send_response()

    # def send_response(self):
    #     for result in self.response:
    #         photos = result.pop("Фотографии")
    #         print(photos)
    #         string = "\n".join([key + ": " + value for key, value in result.items()])
    #         self.bot.send_message(self.id, string)
    #         print(string)
    #         if photos is not None:
    #             print("there are photos to send")
    #             photos_tg = [InputMediaPhoto(media=el) for el in photos]
    #             self.bot.send_media_group(self.id, photos_tg)


class DialogHandlerLowprice(DialogHandler):

    def get_answer(self):
        print("Мне повезло повезло я лоупрайс")
        number_of_photos = self.user_data.get("number_of_photos", 0)
        self.user_data['number_of_photos'] = number_of_photos
        BOT.clear_step_handler_by_chat_id(self.id)
        print(self.user_data)
        self.get_query(self.user_data)


class DialogHandlerHighprice(DialogHandler):

    def get_answer(self):
        print("Мне повезло повезло я хайпрайс")
        number_of_photos = self.user_data.get("number_of_photos", 0)
        self.user_data['number_of_photos'] = number_of_photos
        print(self.user_data)
        BOT.clear_step_handler_by_chat_id(self.id)
        self.get_query(self.user_data)


class DialogHandlerBestDeal(DialogHandler):
    def get_city(self, message):
        print("bestdeal")
        self.user_data['city_of_destination'] = message.text
        self.user_data['id'] = message.from_user.id
        self.bot.send_message(self.id,
                              "Сколько вариантов тебе нужно?")
        self.bot.register_next_step_handler(message, self.get_number_of_variants)

    def get_number_of_variants(self, message):
        try:
            self.user_data['number_of_variants'] = int(message.text)
            if self.user_data['number_of_variants'] <= 0:
                raise Exception
            self.bot.send_message(self.id,
                                  "Замечательно! Введи минимальную стоимость ($)")
            self.bot.register_next_step_handler(message, self.get_min_price)

        except Exception:
            self.bot.send_message(self.id, " Введи корректное число 👉🏻👈🏻\nСколько вариантов тебе показать?")
            self.bot.register_next_step_handler(message, self.get_number_of_variants)

    def get_min_price(self, message):
        try:
            self.user_data["min_price"] = int(message.text)
            self.bot.send_message(self.id, "Супер! Tеперь максимальную ($)")
            self.bot.register_next_step_handler(message, self.get_max_price)
        except Exception:
            self.bot.send_message(self.id, " Введи корректную цену 👉🏻👈🏻")
            self.bot.register_next_step_handler(message, self.get_min_price)

    def get_max_price(self, message):
        try:
            self.user_data["max_price"] = int(message.text)
            if self.user_data["max_price"] <= self.user_data["min_price"]:
                raise Exception
            self.bot.send_message(self.id, "Введи максимальное предпочтительное расстояние от центра (miles)")
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
                                  "Понял! Работаю...")
            self.get_answer()
        except Exception:
            self.bot.send_message(self.id, " Введи корректные данные🥺")
            self.bot.register_next_step_handler(message, self.get_miles)

    def get_answer(self):
        print("Мне повезло повезло я бест деал")
        print(self.user_data)
        number_of_photos = self.user_data.get("number_of_photos", 0)
        self.user_data['number_of_photos'] = number_of_photos
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

        user = User.get_user(message.from_user.id, message.text)
        user.get_dates(user.id)

    elif message.text == '/history':
        pass


@BOT.message_handler(content_types=["text"])
def hello(message):
    if message.text in ["Привет", "/hello_world"]:
        BOT.send_message(message.from_user.id, "И тебе привет!")


if __name__ == '__main__':
    BOT.polling(none_stop=True)

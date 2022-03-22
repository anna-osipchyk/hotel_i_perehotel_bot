import datetime

from telebot import types
from telebot.types import User as t_user
from telegram_bot_calendar import DetailedTelegramCalendar

from bot_start import BOT
from botrequests.bestdeal import QueryBestdeal
from botrequests.highprice import QueryHighprice
from botrequests.history import history
from botrequests.lowprice import QueryLowprice
import logging


class Calendar(DetailedTelegramCalendar):
    """
    Календарь. Объекты этого класса создаются каждый раз,
    когда у пользователя запрашивают дату заселения/выселения

    """

    prev_button = "👈🏻️"
    next_button = "👉🏻"
    empty_year_button = "🚫"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # конструктор запрещает пользователю запросить дату, меньшую текущей
        self.min_date = datetime.date.today()


def check_dates(date1: datetime.date, date2=None) -> bool:
    """ "Проверяется валидность дат: дата выселения не меньше даты заселения"""
    if date2 is not None and date1 > date2:
        return False
    elif date2 is False:
        return False
    return True


def choose_command_and_create_instance(
    id: int, command: str, message: str, photos_needed=False
) -> None:
    """
    В зависимости от команды создаются объекты разных DialogHandler-классов

          :param id: id пользователя сессии
          :param command: команда, выбранная пользователем
          :param message: сообщение, переданное пользователем
          :param photos_needed: нужны ли пользователю в ответе фото
    """

    dh = None
    if command == "/lowprice":
        dh = DialogHandlerLowprice(id, command)
    elif command == "/highprice":
        dh = DialogHandlerHighprice(id, command)
    elif command == "/bestdeal":
        dh = DialogHandlerBestDeal(id, command)
    if photos_needed:
        logger.info(
            f"Создался экземпляр DialogHandler для обработки данных пользователя {id}"
        )
        # передается управление функции get_number_of_photos
        BOT.register_next_step_handler(message, dh.get_number_of_photos)
    else:
        logger.info(
            f"Создался экземпляр DialogHandler для обработки данных пользователя {id}"
        )
        # передается управление функции get_city
        BOT.register_next_step_handler(message, dh.get_city)


class CommandMixin:
    """Класс-примесь для запоминания команды, запрошенной пользователем"""

    def __init__(self, command: str) -> None:
        self.command = command


class User(CommandMixin):
    """Класс пользователя"""

    users = {}
    self_like_id = None

    def __init__(self, id: int, command: str) -> None:
        """
        Конструктор класса:
            :param id: id пользователя сессии
            :param command: команда, выбранная пользователем
        """
        super().__init__(command)
        self.id = id
        User.add_user(id, self)

    @classmethod
    def add_user(cls, id: int, user: t_user) -> None:
        """
        Пользователь добавляется в список существующих пользователей:
            :param id: id пользователя сессии
            :param user: объект класса User
        """

        cls.users[id] = user

    @classmethod
    def get_user(cls, id: int, command=None) -> "User":
        """
        Пользователь либо создается, если его нет в словаре пользователей,
        в противном случае возвращается существующий объект:
            :param id: id пользователя сессии
            :param command: выбранная пользователем команда
            :return: User
        """
        if id in User.users:
            user = User.users[id]
            user.command = command
            return user
        logger.info(f"Создался новый пользователь {id}")
        return User(id, command)

    @staticmethod
    def get_dates(id: int) -> None:
        """Отправляет пользователю календарь:
        :param id: id пользователя сессии"""
        logger.info(f"Пользователю {id} отправлен календарь")
        calendar = Calendar(locale="ru", calendar_id=1).build()[0]
        User.self_like_id = id
        BOT.send_message(id, f"В каком году отправляемся? ", reply_markup=calendar)

    @staticmethod
    @BOT.callback_query_handler(
        func=lambda call: call.data
        in ["yes_1", "yes_2", "yes_3", "no_1", "no_2", "no_3"]
    )
    def call(c):
        """
        Обработчик кнопок Да/Нет
        """
        if c.data == "yes_1":
            # если дата заселения верна, создается календарь для ввода даты выселения
            calendar, step = Calendar(locale="ru", calendar_id=2).build()
            BOT.send_message(
                c.message.chat.id,
                f"Здорово! Напиши год, когда ты вернешься: ",
                reply_markup=calendar,
            )
        elif c.data == "no_1":
            # если дата заселения не верна, еще раз создается календарь для ввода даты заселения
            DialogHandler.user_data.pop("arrival")
            calendar, step = Calendar(locale="ru", calendar_id=1).build()
            BOT.send_message(
                c.message.chat.id, f"Выбери нужный год: ", reply_markup=calendar
            )

        elif c.data == "yes_2":
            # если дата выселения верна, создаются кнопки Да\Нет (нужны ли пользователю фотографии)
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            yes_btn = types.InlineKeyboardButton(text="да", callback_data="yes_3")
            no_btn = types.InlineKeyboardButton(text="нет", callback_data="no_3")
            keyboard.add(yes_btn, no_btn)
            BOT.send_message(
                c.message.chat.id, "Тебе понадобятся фотографии?", reply_markup=keyboard
            )

        elif c.data == "no_2":
            # если дата выселения не верна, еще раз создается календарь для ввода даты выселения
            DialogHandler.user_data.pop("arrival")
            calendar, step = Calendar(locale="ru", calendar_id=1).build()
            BOT.send_message(
                c.message.chat.id, f"Выбери нужный год: ", reply_markup=calendar
            )
        elif c.data == "yes_3":
            # пользователю нужны фотографии
            BOT.send_message(
                c.message.chat.id, "Напиши, сколько фотографий тебе показать📸"
            )
            id, command = User.self_like_id, User.users[User.self_like_id].command
            choose_command_and_create_instance(id, command, c.message, True)

        elif c.data == "no_3":
            # пользователю не нужны фотографии

            BOT.send_message(
                c.message.chat.id,
                f"Класс, теперь"
                f" отправь мне название города,"
                f" в котором ты хочешь найти подходящий отель\n✨✨✨\nНапример, Минск",
            )
            id, command = User.self_like_id, User.users[User.self_like_id].command
            choose_command_and_create_instance(id, command, c.message)

    @staticmethod
    @BOT.callback_query_handler(func=Calendar.func(calendar_id=1))
    def call(c):
        step_dict = {"y": "год", "m": "месяц", "d": "день"}

        result, key, step = Calendar(locale="ru", calendar_id=1).process(c.data)
        if not result and key:
            BOT.edit_message_text(
                f"Выбери {step_dict[step]}",
                c.message.chat.id,
                c.message.message_id,
                reply_markup=key,
            )
        elif result:
            DialogHandler.user_data["arrival"] = result
            # вызывается проверка валидности дат
            is_valid = check_dates(
                DialogHandler.user_data["arrival"],
                DialogHandler.user_data.get("departure", None),
            )
            if is_valid:
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                yes_btn = types.InlineKeyboardButton(text="да", callback_data="yes_1")
                no_btn = types.InlineKeyboardButton(text="нет", callback_data="no_1")
                keyboard.add(yes_btn, no_btn)
                logger.info(f"Пользователь {c.message.chat.id} запросил дату {result}")
                BOT.send_message(
                    c.message.chat.id,
                    f"Твоя выбранная дата: {result}. Все верно?",
                    reply_markup=keyboard,
                )
            else:

                logger.warning(
                    f"Пользователь {c.message.chat.id} запросил некорректную дату"
                )
                BOT.send_message(
                    c.message.chat.id, f"Неверная дата! Давай попробуем еще раз"
                )
                calendar, step = Calendar(locale="ru", calendar_id=1).build()
                BOT.send_message(
                    c.message.chat.id, f"Выбери нужный год: ", reply_markup=calendar
                )

    @staticmethod
    @BOT.callback_query_handler(func=Calendar.func(calendar_id=2))
    def call(c):
        step_dict = {"y": "год", "m": "месяц", "d": "день"}
        result, key, step = Calendar(locale="ru", calendar_id=2).process(c.data)
        if not result and key:
            BOT.edit_message_text(
                f"Выбери {step_dict[step]}",
                c.message.chat.id,
                c.message.message_id,
                reply_markup=key,
            )
        elif result:
            # вызывается проверка валидности дат
            DialogHandler.user_data["departure"] = result
            is_valid = check_dates(
                DialogHandler.user_data["arrival"],
                DialogHandler.user_data.get("departure", None),
            )
            if is_valid:
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                yes_btn = types.InlineKeyboardButton(text="да", callback_data="yes_2")
                no_btn = types.InlineKeyboardButton(text="нет", callback_data="no_2")
                keyboard.add(yes_btn, no_btn)
                logger.info(f"Пользователь {c.message.chat.id} запросил дату {result}")
                BOT.send_message(
                    c.message.chat.id,
                    f"Твоя выбранная дата: {result}. Все верно?",
                    reply_markup=keyboard,
                )
            else:
                BOT.send_message(
                    c.message.chat.id, f"Неверная дата! Давай попробуем еще раз"
                )
                logger.warning(
                    f"Пользователь {c.message.chat.id} запросил некорректную дату"
                )
                calendar, step = Calendar(locale="ru", calendar_id=2).build()
                BOT.send_message(
                    c.message.chat.id, f"Выбери нужный год: ", reply_markup=calendar
                )


class DialogHandler(User):
    user_data = {}
    bot = BOT

    def __init__(self, id: int, command: str) -> None:
        """
        Конструктор класса:
            :param id: id пользователя сессии
            :param command: команда, выбранная пользователем
        """
        super().__init__(id, command)
        self.response = None

    def get_number_of_photos(self, message: types.Message) -> None:
        """
        Запоминает количество запрошенных фотографий для пользователя с активной сессией:
            :param message: сообщение от пользователя
        """
        number_of_photos = message.text
        try:
            if message.content_type != "text":
                raise ValueError
            self.user_data["number_of_photos"] = int(number_of_photos)
            logger.info(
                f"Пользователь {self.id} запросил {number_of_photos} фотографий"
            )
            self.bot.send_message(
                self.id,
                f"Класс, теперь"
                f" отправь мне название города,"
                f" в котором ты хочешь найти подходящий отель\n✨✨✨\nНапример, Минск",
            )
            self.bot.register_next_step_handler(message, self.get_city)

        except ValueError:
            logger.warning(
                f"Пользователь {self.id} запросил некорректное число фотографий"
            )
            self.bot.send_message(
                self.id,
                "Моя твоя не понимать🤯\nДавай попробуем еще раз.\nСколько фотографий показать?",
            )
            self.bot.register_next_step_handler(message, self.get_number_of_photos)
        except Exception:
            logger.error(
                f"Цикл обработки данных пользователя {self.id} завершен с ошибкой"
            )
            self.bot.send_message(
                self.id, "Что-то пошло не так... Отправь команду заново😇"
            )

    def get_city(self, message: types.Message) -> None:
        """
        Запоминает запрошенный город для пользователя с активной сессией:
            :param message: сообщение от пользователя
        """
        try:
            if message.content_type != "text":
                raise ValueError
            logger.info(f"Пользователь {self.id} запросил город {message.text}")
            self.user_data["city_of_destination"] = message.text
            self.user_data["id"] = message.from_user.id
            self.bot.send_message(self.id, "Сколько вариантов тебе нужно?")
            self.bot.register_next_step_handler(message, self.get_number_of_variants)
        except ValueError:
            self.bot.send_message(
                self.id, "Ты точно отправил мне название города 🤔? Давай по новой!"
            )
            logger.warning(f"Пользователь {self.id} запросил неверное название города")
            self.bot.register_next_step_handler(message, self.get_city)

        except Exception:
            logger.error(
                f"Цикл обработки данных пользователя {self.id} завершен с ошибкой"
            )
            self.bot.send_message(
                self.id, "Что-то пошло не так... Отправь команду заново😇"
            )

    def get_number_of_variants(self, message: types.Message) -> None:
        """
        Запоминает количество запрошенных вариантов для пользователя с активной сессией:
            :param message: сообщение от пользователя
        """
        try:
            if message.content_type != "text":
                raise ValueError
            self.user_data["number_of_variants"] = int(message.text)
            if self.user_data["number_of_variants"] <= 0:
                raise ValueError
            logger.info(
                f"Пользователь {self.id} запросил кол-во вариантов {message.text}"
            )
            self.bot.send_message(self.id, "Понял! Работаю...")
            self.get_answer()

        except ValueError:
            self.bot.send_message(
                self.id,
                " Введи корректное число 👉🏻👈🏻\nСколько вариантов тебе показать?",
            )
            logger.warning(f"Пользователь {self.id} запросил неверное число вариантов")
            self.bot.register_next_step_handler(message, self.get_number_of_variants)
        except Exception:
            logger.error(
                f"Цикл обработки данных пользователя {self.id} завершен с ошибкой"
            )
            self.bot.send_message(
                self.id, "Что-то пошло не так... Отправь команду заново😇"
            )

    def get_answer(self):
        """Абстрактный метод. См. описание в классах-наследниках"""
        pass

    def get_query(self, user_data: dict) -> None:
        """
        Создается объект Query-класса, внутри которого происходит формирование и обработка запроса на основе данных,
        запрошенных пользователем:
            :param user_data: словарь с полученными данными от пользователя (город, даты,
        стоимость, тд)
        """
        ql = None
        if self.command == "/lowprice":
            ql = QueryLowprice(BOT, self.id)
        elif self.command == "/highprice":
            ql = QueryHighprice(BOT, self.id)
        elif self.command == "/bestdeal":
            ql = QueryBestdeal(BOT, self.id)
        self.response = ql.get_response(user_data)
        if isinstance(self.response, Exception):
            logger.info(f"Данные по запросу пользователя {self.id} не найдены")
            self.bot.send_message(self.id, "Извини, я ничего не нашел😣")
            return
        else:
            logger.info(
                f"Цикл обработки данных пользователя {self.id} успешно завершен"
            )
            self.user_data.clear()
        return


class DialogHandlerLowprice(DialogHandler):
    """Класс-наследник для обработки команды lowprice"""

    def get_answer(self) -> None:
        """Формирование словаря с данными от пользователя"""
        logger.info("Вызвана функция get_answer lowprice")
        number_of_photos = self.user_data.get("number_of_photos", 0)
        self.user_data["number_of_photos"] = number_of_photos
        BOT.clear_step_handler_by_chat_id(self.id)
        self.get_query(self.user_data)


class DialogHandlerHighprice(DialogHandler):
    def get_answer(self) -> None:
        """Формирование словаря с данными от пользователя"""
        logger.info("Вызвана функция get_answer highprice")
        number_of_photos = self.user_data.get("number_of_photos", 0)
        self.user_data["number_of_photos"] = number_of_photos
        BOT.clear_step_handler_by_chat_id(self.id)
        self.get_query(self.user_data)


class DialogHandlerBestDeal(DialogHandler):
    def get_city(self, message: types.Message) -> None:
        """
        Запоминает запрошенный город для пользователя с активной сессией:
            :param message: сообщение от пользователя
        """
        if message.content_type != "text":
            raise ValueError
        try:
            self.user_data["city_of_destination"] = str(message.text)
            self.user_data["id"] = message.from_user.id
            self.bot.send_message(self.id, "Сколько вариантов тебе нужно?")
            logger.info(f"Пользователь {self.id} запросил город {message.text}")

            self.bot.register_next_step_handler(message, self.get_number_of_variants)
        except ValueError:
            logger.warning(
                f"Пользователь {self.id} запросил некорректное название города"
            )
            self.bot.send_message(
                self.id, "Ты точно отправил мне название города 🤔? Давай по новой!"
            )
            self.bot.register_next_step_handler(message, self.get_city)

        except Exception:
            logger.error(
                f"Цикл обработки данных пользователя {self.id} завершен с ошибкой"
            )
            self.bot.send_message(
                self.id, "Что-то пошло не так... Отправь команду заново😇"
            )

    def get_number_of_variants(self, message: types.Message) -> None:
        """
        Запоминает количество запрошенных вариантов для пользователя с активной сессией:
            :param message: сообщение от пользователя
        """
        try:
            if message.content_type != "text":
                raise ValueError
            self.user_data["number_of_variants"] = int(message.text)
            if self.user_data["number_of_variants"] <= 0:
                raise ValueError
            logger.info(f"Пользователь {self.id} запросил {message.text} вариантов")

            self.bot.send_message(
                self.id, "Замечательно! Введи минимальную стоимость ($)"
            )
            self.bot.register_next_step_handler(message, self.get_min_price)

        except ValueError:
            logger.warning(
                f"Пользователь {self.id} запросил некорректное число вариантов"
            )
            self.bot.send_message(
                self.id,
                " Введи корректное число 👉🏻👈🏻\nСколько вариантов тебе показать?",
            )
            self.bot.register_next_step_handler(message, self.get_number_of_variants)

        except Exception:
            logger.error(
                f"Цикл обработки данных пользователя {self.id} завершен с ошибкой"
            )
            self.bot.send_message(
                self.id, "Что-то пошло не так... Отправь команду заново😇"
            )

    def get_min_price(self, message: types.Message) -> None:
        """
        Запоминает минимально допустимую цену для пользователя с активной сессией:
            :param message: сообщение от пользователя
        """
        try:
            if message.content_type != "text":
                raise ValueError
            self.user_data["min_price"] = int(message.text)
            if self.user_data["min_price"] <= 0:
                raise ValueError
            logger.info(
                f"Пользователь {self.id} запросил минимальную цену {message.text}"
            )

            self.bot.send_message(self.id, "Супер! Tеперь максимальную ($)")
            self.bot.register_next_step_handler(message, self.get_max_price)
        except ValueError:
            logger.warning(
                f"Пользователь {self.id} запросил некорректную минимальную цену"
            )
            self.bot.send_message(self.id, " Введи корректную цену 👉🏻👈🏻")
            self.bot.register_next_step_handler(message, self.get_min_price)

        except Exception:
            logger.error(
                f"Цикл обработки данных пользователя {self.id} завершен с ошибкой"
            )
            self.bot.send_message(
                self.id, "Что-то пошло не так... Отправь команду заново😇"
            )

    def get_max_price(self, message: types.Message) -> None:
        """
        Запоминает максимально допустимую цену для пользователя с активной сессией:
            :param message: сообщение от пользователя
        """
        try:
            if message.content_type != "text":
                raise ValueError
            self.user_data["max_price"] = int(message.text)
            if self.user_data["max_price"] <= self.user_data["min_price"]:
                raise ValueError
            self.bot.send_message(
                self.id,
                "Введи максимальное предпочтительное расстояние от центра (км)",
            )
            logger.info(
                f"Пользователь {self.id} запросил максимальную цену {message.text}"
            )
            self.bot.register_next_step_handler(message, self.get_miles)
        except ValueError:
            logger.warning(f"Пользователь {self.id} запросил некорректную цену")
            self.bot.send_message(self.id, " Введи корректную цену 👉🏻👈🏻")
            self.bot.register_next_step_handler(message, self.get_max_price)

        except Exception:
            logger.error(
                f"Цикл обработки данных пользователя {self.id} завершен с ошибкой"
            )
            self.bot.send_message(
                self.id, "Что-то пошло не так... Отправь команду заново😇"
            )

    def get_miles(self, message: types.Message) -> None:
        """
        Запоминает максимально допустимую дистанцию от центра для пользователя с активной сессией:
            :param message: сообщение от пользователя
        """
        try:
            if message.content_type != "text":
                raise ValueError
            self.user_data["miles"] = int(message.text)
            if self.user_data["miles"] <= 0:
                raise ValueError
            self.bot.send_message(self.id, "Понял! Работаю...")
            logger.info(f"Пользователь {self.id} запросил  {message.text} км")
            self.get_answer()
        except ValueError:
            logger.warning(
                f"Пользователь {self.id} запросил некорректную удаленность от центра"
            )
            self.bot.send_message(self.id, " Введи корректные данные🥺")
            self.bot.register_next_step_handler(message, self.get_miles)

        except Exception:
            logger.error(
                f"Цикл обработки данных пользователя {self.id} завершен с ошибкой"
            )
            self.bot.send_message(
                self.id, "Что-то пошло не так... Отправь команду заново😇"
            )

    def get_answer(self) -> None:
        """Формирование словаря с данными от пользователя"""
        logger.info("Вызвана функция get_answer bestdeal")
        number_of_photos = self.user_data.get("number_of_photos", 0)
        self.user_data["number_of_photos"] = number_of_photos
        BOT.clear_step_handler_by_chat_id(self.id)
        self.get_query(self.user_data)


@BOT.message_handler(
    commands=["start", "lowprice", "highprice", "bestdeal", "history", "help"]
)
def get_text_message(message: types.Message) -> None:
    """
    Обработчик команд, отправляемых пользователем ("start", "lowprice", "highprice", "bestdeal", "history", "help"):
        :param message: сообщение от пользователя
    """
    if message.text == "/start":
        logger.info(f"Пользователь {message.from_user.id} запустил бота")
        BOT.send_message(
            message.from_user.id,
            f"Привет, {message.from_user.first_name}!🤗\n\n"
            f"Меня зовут {BOT.get_me().first_name},"
            f" и я помогу найти подходящий отель в интересующем тебя городе!\n\n"
            f"Для навигации по командам отправь мне /help",
        )

    elif message.text in ["/lowprice", "/highprice", "/bestdeal"]:
        logger.info(
            f"Пользователь {message.from_user.id} запустил команду {message.text}"
        )
        user = User.get_user(message.from_user.id, message.text)
        user.get_dates(user.id)

    elif message.text == "/history":
        logger.info(
            f"Пользователь {message.from_user.id} запустил команду {message.text}"
        )
        user = User.get_user(message.from_user.id, message.text)
        history(user.id)
    elif message.text == "/help":
        logger.info(
            f"Пользователь {message.from_user.id} запустил команду {message.text}"
        )

        string = (
            f"_/lowprice: Подбор вариантов осуществляется с учетом стоимости._"
            f"_Тебе будут предложены самые недорогие варианты😇_\n"
            f"\n"
            f"\n"
            f"_/highrice: Подбор вариантов также осуществляется с учетом стоимости._"
            f"_В отличие от предыдущей команды, ты увидишь только самые престижные и дорогие отели и апартаменты🤩_\n"
            f"\n"
            f"\n"
            f"_/bestdeal: В этом случае ты сам(а) сможешь настроить необходимые параметры для поиска - диапазон цен и расстояние от центра🥰_"
            f"\n"
            f"\n"
            f"_/history: Ты увидишь историю своих последних запросов со всеми предложениями☺_\n"
        )
        BOT.send_message(message.from_user.id, string, parse_mode="Markdown")


if __name__ == "__main__":
    """Запуск бота и создание объекта для логирования"""
    logger = logging.getLogger(__name__)
    consoleHandler = logging.StreamHandler()
    logger.addHandler(consoleHandler)
    logging.basicConfig(
        filename="logging.log",
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s]  - (%(filename)s).%(funcName)s(%(lineno)d) - %("
        "message)s",
    )

    BOT.polling(none_stop=True)

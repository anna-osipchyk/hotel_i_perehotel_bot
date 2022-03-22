import sqlite3
from typing import Optional


class Database:
    """Класс sqlite-базы данных"""

    db = sqlite3.connect("telebot.db", check_same_thread=False)
    sql = db.cursor()
    """Создание таблиц"""
    sql.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id BIGINT UNSIGNED NOT NULL,
        city_of_destination VARCHAR(50),
        arrival VARCHAR(15),
        departure VARCHAR(15),
        number_of_variants INT UNSIGNED,
        number_of_photos INT UNSIGNED,
        min_price INT UNSIGNED,
        max_price INT UNSIGNED,
        miles INT UNSIGNED
        )
        """
    )
    sql.execute(
        """
        CREATE TABLE IF NOT EXISTS hotels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id BIGINT UNSIGNED NOT NULL,
        name VARCHAR(30),
        price VARCHAR(10),
        address VARCHAR(70),
        distance VARCHAR(15),
        url VARCHAR(50),
        uploaded_at TEXT,
        FOREIGN KEY(request_id) REFERENCES users(id)
        )
        """
    )

    sql.execute("CREATE INDEX IF NOT EXISTS user ON users(user_id)")
    db.commit()

    @classmethod
    def insert(cls, temp_dict: dict) -> None:
        """
        Insert-запрос в базу данных:
            :param temp_dict: словарь с данными для вставки
        """
        cls.sql.execute(
            f"INSERT INTO users(user_id, city_of_destination, arrival, departure, number_of_variants, "
            f"number_of_photos, min_price, max_price, miles) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                temp_dict["id"],
                temp_dict["city_of_destination"],
                temp_dict["arrival"],
                temp_dict["departure"],
                temp_dict["number_of_variants"],
                temp_dict["number_of_photos"],
                temp_dict.get("min_price", None),
                temp_dict.get("max_price", None),
                temp_dict.get("miles", None),
            ),
        )
        cls.db.commit()

    @classmethod
    def insert_hotels(cls, temp_dict: dict) -> None:
        """
        Insert-запрос в базу данных:
            :param temp_dict: словарь с данными для вставки
        """
        cls.sql.execute(f"SELECT id FROM users WHERE user_id ={temp_dict['user_id']}")
        cls.db.commit()
        id = [tup[0] for tup in cls.sql.fetchall()][-1]
        cls.sql.execute(
            f"INSERT INTO hotels(request_id, name, price, address, distance, url, uploaded_at) "
            f"VALUES (?,?,?,?,?,?,?)",
            (
                id,
                temp_dict["name"],
                temp_dict["price"],
                temp_dict["address"],
                temp_dict["distance"],
                temp_dict["url"],
                temp_dict["uploaded_at"],
            ),
        )
        cls.db.commit()

    @classmethod
    def select_hotels(cls, user_id: int) -> Optional:
        """
        Select-запрос в базу данных:
            :param user_id: id пользователя
        """
        cls.sql.execute(f"SELECT id FROM users WHERE user_id ={user_id}")
        cls.db.commit()
        data = cls.sql.fetchall()
        try:
            id = [tup[0] for tup in data][-1]
            cls.sql.execute(
                f"SELECT name, price, address, distance, url, uploaded_at FROM hotels WHERE request_id = {id}"
            )
            cls.db.commit()
            data = cls.sql.fetchall()
            return data
        except Exception:
            return None

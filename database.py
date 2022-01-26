import sqlite3


class Database:
    db = sqlite3.connect('telebot.db', check_same_thread=False)
    sql = db.cursor()
    sql.execute("DROP TABLE  IF EXISTS users")
    sql.execute("""
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
        """)

    sql.execute("CREATE INDEX IF NOT EXISTS user ON users(user_id)")
    db.commit()

    @classmethod
    def insert(cls, temp_dict):
        cls.sql.execute(f"INSERT INTO users(user_id, city_of_destination, arrival, departure, number_of_variants, "
                        f"number_of_photos, min_price, max_price, miles) VALUES(?,?,?,?,?,?,?,?, ?)",
                        (temp_dict['id'], temp_dict['city_of_destination'],
                         temp_dict['arrival'], temp_dict['departure'],
                         temp_dict['number_of_variants'], temp_dict[
                             'number_of_photos'], temp_dict.get('min_price', None), temp_dict.get('max_price', None),
                         temp_dict.get('miles', None)))
        cls.db.commit()

    @classmethod
    def print(cls):
        for value in cls.sql.execute("SELECT * FROM users"):
            print(value)

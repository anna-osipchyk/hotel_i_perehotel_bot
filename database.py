import sqlite3

class Database:
    db = sqlite3.connect('server.db',check_same_thread=False)
    sql = db.cursor()
    sql.execute("""
        CREATE TABLE IF NOT EXISTS users (
        id BIGINT UNSIGNED NOT NULL,
        city_of_destination VARCHAR(50),
        num_of_variants INT UNSIGNED,
        num_of_photos INT UNSIGNED
        )
        """)
    db.commit()

    @classmethod
    def insert(cls, temp_dict):
        cls.sql.execute(f"INSERT INTO users(id, city_of_destination, num_of_variants,num_of_photos) VALUES(?,?,?,?)", (temp_dict['id'], temp_dict['city_of_destination'],  temp_dict['num'], temp_dict['num_of_photos']))
        cls.db.commit()

    @classmethod
    def print(cls):
        for value in cls.sql.execute("SELECT * FROM users"):
            print(value)

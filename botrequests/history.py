from bot_start import BOT
from database import Database


def history(user_id):
    data = Database.select_hotels(user_id)
    for response in data:
        name, address, price, distance, url, uploaded_at = response
        current_data = {
            "Дата и время запроса": uploaded_at,
            "Название отеля": name,
            "Адрес": address,
            "Стоимость": price,
            "Расстояние от центра": distance,
            "Подробнее": url
        }
        string = "\n".join([key + ": " + value for key, value in current_data.items()])
        BOT.send_message(user_id, string, disable_web_page_preview=True)

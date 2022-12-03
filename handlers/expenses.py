import sqlite3
from datetime import date
from aiogram import Dispatcher
from aiogram import types


async def all_expenses(message: types.Message):
    period = "Month"
    db = sqlite3.connect("server.db")
    sql = db.cursor()
    sql.execute(f"""SELECT spent FROM '{message.from_user.id}' WHERE month={date.today().month}
                """)
    s = 0
    for number in sql.fetchall():
        if number[0]:
            s += number[0]

    await message.reply(f"Вот ваши траты за {period}\n{s}")


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(all_expenses, commands=['Траты'])
    
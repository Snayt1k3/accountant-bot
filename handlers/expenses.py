import sqlite3
from datetime import date

from aiogram import Dispatcher
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup


class Date(StatesGroup):
    day = State()
    month = State()


async def start_fsm_expenses(message: types.Message):
    await Date.day.set()
    await message.reply("Напиши в какой день,\nхочешь увидеть свои траты")


# Принимаем День
async def process_day(message: types.Message, state: FSMContext):
    await state.update_data(day=int(message.text))
    await message.reply("Напиши месяц или укажи .")
    await Date.next()


# Принимаем Месяц
async def process_month(message: types.Message, state: FSMContext):
    await state.update_data(month=int(message.text))
    await message.reply(await all_expenses(message))
    await state.finish()


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

    return f"Вот ваши траты за {period}\n{s}"


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_fsm_expenses, commands=['Траты'])
    dp.register_message_handler(process_day, state=Date.day)
    dp.register_message_handler(process_month, state=Date.month)

import sqlite3
from datetime import date

from aiogram import Dispatcher
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup

from Keyboards import kb


class Date(StatesGroup):
    day = State()
    month = State()


async def start_fsm_expenses(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(".")

    await Date.day.set()
    await message.reply("Напиши в какой день, хочешь увидеть свои траты\nили укажи точку", reply_markup=kb)


# Принимаем День
async def process_day(message: types.Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(".")

    await state.update_data(day=message.text)
    await message.reply("Напиши месяц или укажи .", reply_markup=kb)
    await Date.next()


# Принимаем Месяц
async def process_month(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["month"] = message.text
        await message.reply(await all_expenses(message, data), reply_markup=kb)
    await state.finish()


async def all_expenses(message: types.Message, data):
    period = {}
    res = f'WHERE month={date.today().month}'
    day = ''
    month = ''

    if data['month'] != ".":
        period['month'] = data["month"]
        month = period['month']

    if data['day'] != ".":
        period['day'] = data['day']
        day = period['day']

    if len(period) == 2:
        res = f"WHERE month={period['month']} AND day={period['day']}"

    elif 'day' in period:
        res = f"WHERE day={period['day']} AND month={date.today().month}"

    elif 'month' in period:
        res = f"WHERE month={period['month']}"

    db = sqlite3.connect("server.db")
    sql = db.cursor()
    sql.execute(f"""SELECT spent FROM '{message.from_user.id}' {res}
                """)
    s = 0
    for number in sql.fetchall():
        if number[0]:
            s += number[0]

    str_res = f"Вот ваши траты за {date.today().month}\n{s}"

    if month and day:
        str_res = f"Вот ваши траты за {month} Месяц и {day} День\n{s}"
    elif month:
        str_res = f"Вот ваши траты за {month} Месяц\n{s}"
    elif day:
        str_res = f"Вот ваши траты за {day} День\n{s}"

    return str_res


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_fsm_expenses, commands=['Траты'])
    dp.register_message_handler(process_day, state=Date.day)
    dp.register_message_handler(process_month, state=Date.month)

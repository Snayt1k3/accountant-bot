import sqlite3
from datetime import date

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup

from Keyboards import kb


class Money(StatesGroup):
    action = State()
    money = State()
    day = State()


async def cmd_start(message: types.Message):
    await Money.action.set()
    kb1 = ReplyKeyboardMarkup(resize_keyboard=True)
    kb1.add("доход").add("расход")
    await message.reply("Привет! Укажи действие кнопкой на клавиатуре", reply_markup=kb1)


# проверка Action
# @dp.message_handler(lambda message: message.text.lower() not in ["расход", "доход"], state=Money.action)
async def process_action_invalid(message: types.Message):
    return await message.reply("Напиши Действие или напиши /cancel")


# Принимаем Action и узнаем сумму
# @dp.message_handler(state=Money.action)
async def process_action(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['action'] = message.text

    await Money.next()
    await message.reply("Введи Сумму")


# Проверка суммы
# @dp.message_handler(lambda message: not message.text.isdigit(), state=Money.money)
async def process_money_invalid(message: types.Message):
    return await message.reply("Напиши Сумму или напиши /cancel")


# Принимаем сумму и узнаем день
# @dp.message_handler(lambda message: message.text.isdigit(), state=Money.money)
async def process_money(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["money"] = int(message.text)
    await message.reply("Напиши день (цифрой)")
    await Money.next()


# @dp.message_handler(state=Money.date)
async def process_day(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        # print(f"day - {message.text}")
        data["day"] = int(message.text)
        await db_accountant(message, data)
        await message.reply(f"Я учел ваш {data['action']}", reply_markup=kb)
    await state.finish()

# Добавляем возможность отмены, если пользователь передумал заполнять
# @dp.message_handler(state='*', commands='cancel')
# @dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await message.reply('ОК')


async def all_expenses(message: types.Message):
    period = "Month"
    db, sql = connection(message)
    sql.execute(f"""SELECT spent FROM '{message.from_user.id}' WHERE month={date.today().month}
                """)
    s = 0
    for number in sql.fetchall():
        if number[0]:
            s += number[0]

    await message.reply(f"Вот ваши траты за {period}\n{s}")


# Создания табл с id пользователя, если еще таблица не создана
def connection(message: types.Message):
    db = sqlite3.connect("server.db")
    sql = db.cursor()
    sql.execute(f"""CREATE TABLE IF NOT EXISTS '{message.from_user.id}'(
                 income BIGINT NULL,
                 spent BIGINT NULL,
                 month INTEGER,
                 day INTEGER,
                 year INTEGER)""")
    db.commit()
    return db, sql


# Взаимодействия с бд (запись данных)
async def db_accountant(message, data):
    pillar = "income"
    if data["action"] == "расход":
        pillar = "spent"

    today = date.today()

    db, sql = connection(message)
    sql.execute(f"""INSERT INTO '{message.from_user.id}' ({pillar}, year, month, day)
                VALUES ({int(data["money"])}, {today.year}, {today.month}, {data['day']})""")

    db.commit()
    # await message.reply(f"Я учел ваш {data['action']}")


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["Внести_Расход_Доход"])
    dp.register_message_handler(all_expenses, commands=["Траты"])
    dp.register_message_handler(process_action_invalid, lambda message: message.text.lower() not in ["расход", "доход"],
                                state=Money.action)
    dp.register_message_handler(process_action, state=Money.action)
    dp.register_message_handler(process_money_invalid, lambda message: not message.text.isdigit(), state=Money.money)
    dp.register_message_handler(process_money, lambda message: message.text.isdigit(), state=Money.money)
    dp.register_message_handler(cancel_handler, Text(equals='отмена', ignore_case=True), commands='cancel', state='*')
    dp.register_message_handler(process_day, state=Money.day)
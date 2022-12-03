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
    month = State()


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
    await state.update_data(money=int(message.text))
    await message.reply("Напиши день (цифрой) или .")
    await Money.next()


# @dp.message_handler(state=Money.day)
# Принимаем день и узнаем месяц
async def process_day(message: types.Message, state: FSMContext):
    await state.update_data(day=message.text)
    await message.reply(f"Введите номер месяца или точку\nПо умолчанию будет выставлен {date.today().month}")

    await Money.next()


# @dp.message_handler(state=Money.month)
# Принимаем месяц
async def process_month(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["month"] = message.text
        await db_accountant(message, data)
        await message.reply(f"Я учел ваш {data['action'].capitalize()}", reply_markup=kb)

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
    day = today.day
    month = today.month

    if data['day'].isdigit():
        day = data['day']

    if data['month'].isdigit():
        month = data['month']

    db, sql = connection(message)
    sql.execute(f"""INSERT INTO '{message.from_user.id}' ({pillar}, year, month, day)
                VALUES ({int(data["money"])}, {today.year}, {month}, {day})""")

    db.commit()
    # await message.reply(f"Я учел ваш {data['action']}")


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["Внести_Расход_Доход"])
    dp.register_message_handler(process_action_invalid, lambda message: message.text.lower() not in ["расход", "доход"],
                                state=Money.action)
    dp.register_message_handler(process_action, state=Money.action)
    dp.register_message_handler(process_money_invalid, lambda message: not message.text.isdigit(), state=Money.money)
    dp.register_message_handler(process_money, lambda message: message.text.isdigit(), state=Money.money)
    dp.register_message_handler(cancel_handler, Text(equals='отмена', ignore_case=True), commands='cancel', state='*')
    dp.register_message_handler(process_day, state=Money.day)
    dp.register_message_handler(process_month, state=Money.month)

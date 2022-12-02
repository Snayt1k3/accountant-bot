from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

b1 = KeyboardButton("/Внести_Расход_Доход")
b2 = KeyboardButton("/Траты")

kb = ReplyKeyboardMarkup(resize_keyboard=True)

kb.add(b1).add(b2)

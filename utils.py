import re
from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def create_reply_keyboard(commands: list) -> ReplyKeyboardMarkup:
    buttons = [KeyboardButton(text=command) for command in commands]
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*buttons)
    return keyboard


def create_inline_keyboard(name_call_buttons: dict) -> InlineKeyboardMarkup:
    inline_keyboard = InlineKeyboardMarkup()
    buttons = []
    for name, call in name_call_buttons.items():
        buttons.append(InlineKeyboardButton(text=name, callback_data=call))
    inline_keyboard.add(*buttons)
    return inline_keyboard


def get_matched(keyword, names):
    regex = re.compile(keyword.lower())

    matched = []
    for name in names:
        match = regex.search(name.lower())
        if match is not None:
            matched.append(name)
    return matched


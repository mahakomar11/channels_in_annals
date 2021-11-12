import json
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


if __name__ == "__main__":
    user_id = 99649314
    with open("channels.json", "r") as f:
        users_channels = json.load(f)

    channels = users_channels[str(user_id)]["channels"]
    chan_names = channels.keys()

    keyword = "диет"

    matched = get_matched(keyword, chan_names)
    print(matched)

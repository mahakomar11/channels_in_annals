import os

from dotenv import load_dotenv
import telebot

from db import DB
from user import User
from utils import create_reply_keyboard, create_inline_keyboard

load_dotenv()

db = DB()
db.setup()

my_commands = [
    "Инструкция",
    "Список каналов",
    "Поиск по названию",
    "Добавить вручную",
    "Удалить канал",
    "Удалить все каналы",
]
keyboard = create_reply_keyboard(my_commands)

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))


@bot.message_handler(commands=["start"])
def handle_command(message):
    user_id = message.from_user.id
    bot.send_message(
        user_id,
        'Привет, я — бот "Каналы в анналах".\n'
        "Я сделан, чтобы помогать Маше меньше прокрастинировать в телеграме.\n\n"
        "Если ты тоже иногда ловишь себя на том, что залипаешь в каналы, когда планы были совсем другие, "
        "я могу быть полезным. "
        "Перешли мне сообщение из канала и я сохраню на него ссылку. "
        "Так можно отписаться от каналов, но не потерять их.\n\n"
        'Для подробностей жми "Инструкция".',
        reply_markup=keyboard,
    )


@bot.message_handler(
    content_types=[
        "text",
        "photo",
        "video",
        "document",
        "sticker",
        "video_note",
        "voice",
    ],
)
def get_message(message):
    user_id = message.from_user.id
    user = User(user_id, db)
    last_message = user.read_last_message()
    reply_markup = keyboard

    if message.text == "Инструкция":
        answer = (
            "Перешли мне сообщение из канала и "
            "я сохраню на него ссылку. "
            "Важно: сообщение не должно быть репостом — я достаю "
            "автора оригинального сообщения.\n\n"
            "Чтобы получить список "
            'своих каналов, нажми "Список каналов".\n\n'
            'Если я не могу достать ссылку на канал из сообщения, нажми "Добавить вручную".'
        )
    elif message.text == "Поиск по названию":
        answer = "Напиши ключевое слово"
    elif message.text == "Добавить вручную":
        answer = 'Пришли мне ссылку на канал. Если канал засекречен, пришли "Название ссылка", через пробел.'
    elif message.text == "Удалить канал":
        answer = "Напиши ключевое слово"
    elif message.text == "Список каналов":
        answer = user.display_channels()
        reply_markup = create_inline_keyboard(
            {"Сортировать по алфавиту": "sort"},
        )
    elif message.text == "Удалить все каналы" and last_message != message.text:
        answer = (
            "Каналы нельзя будет вернуть. Чтобы подтвердить удаление всех-всех"
            ' каналов, нажми "Удалить все каналы" ещё раз'
        )
    elif message.text == last_message == "Удалить все каналы":
        user.delete_all_channels()
        answer = "Список каналов пуст."
    elif last_message == "Поиск по названию":
        answer = user.search_channels(message.text)
    elif last_message == "Добавить вручную":
        answer = user.add_channel_by_link(message.text, bot)
    elif last_message == "Удалить канал":
        answer = user.search_channels(message.text, max_num=1)
        if answer != "Таких каналов не найдено, попробуй другое слово.":
            answer = "Удалить этот канал?" + "\n\n" + answer
            reply_markup = create_inline_keyboard(
                {"Да": message.text, "Нет": "no"},
            )
    elif message.forward_from_chat is None:
        answer = "Сообщение должно быть переслано из канала."
    else:
        answer = user.add_channel(message.forward_from_chat)

    if message.text not in my_commands:
        last_message = ""
    else:
        last_message = message.text

    bot.send_message(user_id, answer, reply_markup=reply_markup)
    user.write_last_message(last_message)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    user = User(user_id, db)
    answer = "Не понимаю..."
    if call.data == "sort":
        answer = user.display_channels(to_sort=True)
    elif call.data == "no":
        answer = "Нет так нет."
    elif isinstance(call.data, str):
        user.delete_matched_channel(call.data)
        answer = "Удалил!"
    bot.send_message(user_id, answer)


bot.polling(none_stop=True, interval=0)

# TODO: порефакторить
# TODO: добавить логирование
# TODO: настроить пре-коммиты
# TODO: доставать из ссылки название или из пересланного сообщения ссылку

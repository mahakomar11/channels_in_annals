import telebot
from telebot import types
from decouple import config
from handler import UserDataHandler
from utils import create_inline_keyboard


bot = telebot.TeleBot(config("TOKEN"))

my_commands = [
    "Инструкция",
    "Список каналов",
    "Поиск по названию",
    "Добавить канал вручную",
    "Удалить канал",
    "Удалить все каналы",
]
buttons = [types.KeyboardButton(text=command) for command in my_commands]
keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(*buttons)


@bot.message_handler(commands=["start"])
def handle_command(message):
    if message.text == "/start":
        user_id = message.from_user.id
        bot.send_message(
            user_id,
            'Привет, я — бот "Каналы в анналах".\n\n'
            "Я сделан, чтобы помогать Маше меньше прокрастинировать.\n\n"
            "Перешли мне свои каналы, и я их сохраню. "
            "Так ты сможешь от них отписаться, "
            "чтобы отвлекаться на них, только когда напишешь мне. "
            'Чтобы узнать как пользоваться, жми "Инструкция".',
            reply_markup=keyboard,
        )
        UserDataHandler(user_id).write_channels({})


@bot.message_handler(
    content_types=[
        "text",
        "photo",
        "video",
        "document",
        "sticker",
        "video_note",
        "voice",
    ]
)
def get_message(message):
    user_id = message.from_user.id
    user_data_handler = UserDataHandler(user_id)
    last_message = user_data_handler.read_last_message()
    reply_markup = keyboard

    if message.text == "Инструкция":
        answer = (
            "Перешли мне сообщение из канала и "
            "я сохраню на него ссылку. "
            "Важно: сообщение не должно быть репостом — бот достаёт "
            "автора оригинального сообщения.\n\n"
            "Чтобы получить список "
            'своих каналов, нажми "Список каналов".'
        )
    elif message.text == "Поиск по названию":
        answer = "Напиши ключевое слово"
    elif message.text == "Добавить канал вручную":
        answer = "Пришли мне ссылку на канал"
    elif message.text == "Удалить канал":
        answer = "Напиши ключевое слово"
    elif message.text == "Список каналов":
        answer = user_data_handler.display_channels()
        reply_markup = create_inline_keyboard(
            {"Сортировать по алфавиту": "sort"}
        )
    elif (
        message.text == "Удалить все каналы"
        and last_message != "Удалить все каналы"
    ):
        answer = (
            "Каналы нельзя будет вернуть. Чтобы подтвердить удаление всех-всех"
            ' каналов, нажми "Удалить все каналы" ещё раз'
        )
    elif (
        message.text == "Удалить все каналы"
        and last_message == "Удалить все каналы"
    ):
        user_data_handler.delete_all_channels()
        answer = "Список каналов пуст."
    elif last_message == "Поиск по названию":
        answer = user_data_handler.search_channels(message.text)
    elif last_message == "Добавить канал вручную":
        answer = user_data_handler.add_channel_by_link(message.text, bot)
    elif last_message == "Удалить канал":
        answer = user_data_handler.search_channels(message.text, max_num=1)
        if answer != "Таких каналов не найдено, попробуй другое слово.":
            answer = "Удалить этот канал?" + "\n\n" + answer
            reply_markup = create_inline_keyboard(
                {"Да": message.text, "Нет": "no"}
            )
    elif message.forward_from_chat is None:
        answer = "Сообщение должно быть переслано из канала."
    else:
        answer = user_data_handler.add_channel(message.forward_from_chat)

    if message.text not in my_commands:
        last_message = ""
    else:
        last_message = message.text

    bot.send_message(user_id, answer, reply_markup=reply_markup)
    user_data_handler.write_last_message(last_message)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    user_data_handler = UserDataHandler(user_id)
    if call.data == "sort":
        answer = user_data_handler.display_channels(to_sort=True)
    elif call.data == "no":
        answer = "Нет так нет."
    elif isinstance(call.data, str):
        user_data_handler.delete_matched_channel(call.data)
        answer = "Удалил!"
    bot.send_message(user_id, answer)


bot.polling(none_stop=True, interval=0)

# TODO: подключить бд
# TODO: залить на сервер
# TODO: добавить логирование
# TODO: доставать из ссылки название или из пересланного сообщения ссылку

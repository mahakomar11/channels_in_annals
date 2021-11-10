import telebot
from telebot import types
from decouple import config
from handler import UserDataHandler


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

    if message.text == "Инструкция":
        bot.send_message(
            user_id,
            "Перешли мне сообщение из канала и "
            "я сохраню на него ссылку. "
            "Важно: сообщение не должно быть репостом — бот достаёт "
            "автора оригинального сообщения.\n\n"
            "Чтобы получить список "
            'своих каналов, нажми "Список каналов".',
            reply_markup=keyboard,
        )
    elif message.text == "Список каналов":
        inline_keyboard = types.InlineKeyboardMarkup()
        button_sort = types.InlineKeyboardButton(
            text="Сортировать по алфавиту", callback_data="sort"
        )
        inline_keyboard.add(button_sort)

        bot.send_message(
            user_id,
            user_data_handler.display_channels(user_id),
            reply_markup=inline_keyboard,
        )
    elif message.text == "Поиск по названию":
        bot.send_message(user_id, "Напиши ключевое слово")
    elif message.text == "Добавить канал вручную":
        bot.send_message(user_id, "Пришли мне ссылку на канал")
    elif message.text == "Удалить канал":
        bot.send_message(user_id, "Напиши ключевое слово")
    elif (
        message.text == "Удалить все каналы"
        and last_message != "Удалить все каналы"
    ):
        bot.send_message(
            user_id,
            "Каналы нельзя будет вернуть. Чтобы подтвердить удаление всех-всех"
            ' каналов, нажми "Удалить все каналы" ещё раз',
        )
    elif (
        message.text == "Удалить все каналы"
        and last_message == "Удалить все каналы"
    ):
        user_data_handler.delete_all_channels()
        bot.send_message(user_id, "Список каналов пуст.")
    elif last_message == "Поиск по названию":
        bot.send_message(
            user_id, user_data_handler.search_channels(message.text)
        )
    elif last_message == "Добавить канал вручную":
        bot.send_message(
            user_id, user_data_handler.add_channel_by_link(message.text, bot)
        )
    elif last_message == "Удалить канал":
        inline_keyboard = types.InlineKeyboardMarkup()
        button_yes = types.InlineKeyboardButton(
            text="Да", callback_data=message.text
        )
        button_no = types.InlineKeyboardButton(text="Нет", callback_data="no")
        inline_keyboard.add(button_yes, button_no)

        answer = user_data_handler.search_channels(message.text, max_num=1)
        bot.send_message(user_id, answer)
        if answer != "Таких каналов не найдено, попробуй другое слово.":
            bot.send_message(
                user_id, "Удалить этот канал?", reply_markup=inline_keyboard
            )
    elif message.forward_from_chat is None:
        bot.send_message(
            user_id,
            "Сообщение должно быть переслано из канала.",
            reply_markup=keyboard,
        )
    else:
        # technical message
        # bot.send_message(user_id, message.forward_from_chat)
        answer = user_data_handler.add_channel(message.forward_from_chat)
        bot.send_message(user_id, answer, reply_markup=keyboard)

    if message.text is None or len(message.text) > 30:
        new_last_message = ""
    else:
        new_last_message = message.text

    user_data_handler.write_last_message(new_last_message)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    user_data_handler = UserDataHandler(user_id)
    if call.data == "sort":
        answer = user_data_handler.display_channels(to_sort=True)
        bot.send_message(user_id, answer)
    elif call.data == "no":
        bot.send_message(user_id, "Нет так нет.")
    elif isinstance(call.data, str):
        user_data_handler.delete_matched_channel(call.data)
        bot.send_message(user_id, "Удалил!")


bot.polling(none_stop=True, interval=0)

# TODO: порефакторить
# TODO: подключить бд
# TODO: залить на сервер
# TODO: добавить логирование
# TODO: доставать из ссылки название или из пересланного сообщения ссылку

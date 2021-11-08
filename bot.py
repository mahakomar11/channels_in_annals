import telebot
from telebot import types
import json
from collections import OrderedDict
from searcher import get_most_similar
from decouple import config


bot = telebot.TeleBot(config('TOKEN'))

keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
help_button = types.KeyboardButton(text='Инструкция')
list_button = types.KeyboardButton(text='Список каналов')
search_button = types.KeyboardButton(text='Поиск по названию')
keyboard.add(help_button, list_button, search_button)
mode = 0


@bot.message_handler(commands=['start'])
def handle_command(message):
    user_id = message.from_user.id
    if message.text == '/start':
        bot.send_message(user_id, 'Привет, я — бот "Каналы в анналах".\n\n'
                                  'Я сделан, чтобы помогать Маше меньше прокрастинировать.\n\n'
                                  'Перешли мне свои каналы, и я их сохраню. '
                                  'Так ты сможешь от них отписаться, '
                                  'чтобы отвлекаться на них, только когда напишешь мне. '
                                  'Чтобы узнать как пользоваться, жми "Инструкция".',
                         reply_markup=keyboard)


@bot.message_handler(content_types=['text', 'photo', 'video',
                                    'document', 'sticker', 'video_note',
                                    'voice'])
def get_message(message):
    user_id = message.from_user.id
    if message.text == 'Инструкция':
        bot.send_message(user_id, 'Перешли мне сообщение из канала и '
                                  'я сохраню на него ссылку. '
                                  'Важно: сообщение не должно быть репостом — бот достаёт '
                                  'автора оригинального сообщения.\n\n'
                                  'Чтобы получить список '
                                  'своих каналов, нажми "Список каналов".',
                         reply_markup=keyboard)
    elif message.text == 'Список каналов':
        inline_keyboard = types.InlineKeyboardMarkup()
        button_sort = types.InlineKeyboardButton(text='Сортировать по алфавиту',
                                                 callback_data='sort')
        inline_keyboard.add(button_sort)
        bot.send_message(user_id, display_channels(user_id), reply_markup=inline_keyboard)
    elif message.text == 'Поиск по названию':
        bot.send_message(user_id, 'Напиши ключевое слово')
        global mode
        mode = 1
    elif mode == 1:
        bot.send_message(user_id, search_channels(user_id, message.text))
        mode = 0
    elif message.forward_from_chat is None:
        bot.send_message(user_id, 'Сообщение должно быть переслано из канала.',
                         reply_markup=keyboard)
    else:
        # bot.send_message(user_id, message.forward_from_chat)  # technical message
        answer = add_channel(user_id, message.forward_from_chat)
        bot.send_message(user_id, answer, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == 'sort':
        user_id = call.message.chat.id
        answer = display_channels(user_id, to_sort=True)
        bot.send_message(user_id, answer)


def add_channel(user_id, chat):
    channels = _read_channels(user_id)
    if chat.username is None:
        return 'Не могу достать ссылку, вероятно канал засекречен.'
    else:
        channels[chat.title] = f't.me/{chat.username}'
        _write_channels(user_id, channels)
        return f'Добавлен канал {chat.title}!'


def display_channels(user_id, to_sort=False):
    channels = _read_channels(user_id)
    if to_sort:
        channels = OrderedDict(sorted(channels.items()))
    return _create_message_from_channels(channels)


def search_channels(user_id, text):
    channels = _read_channels(user_id)
    chan_names = get_most_similar(text, channels.keys(), num_of_best=3)
    found_channels = {name: channels[name] for name in chan_names}
    print(found_channels)
    return _create_message_from_channels(found_channels)


def _create_message_from_channels(channels):
    if len(channels) == 0:
        return 'Каналы не добавлены! Чтобы добавить канал, перешли мне сообщение из него.'
    channels_list = [f'{title}:\n\t\t\t\t\t\t\t\t\t{link}' for title, link in channels.items()]
    return '\n'.join(channels_list)


def _read_channels(user_id):
    with open('channels.json') as f:
        users_channels = json.load(f)
    if len(users_channels) != 0:
        return users_channels[str(user_id)]
    else:
        return {}


def _write_channels(user_id, channels):
    with open('channels.json', 'r+') as f:
        users_channels = json.load(f)
        users_channels[user_id] = channels
        f.seek(0)
        json.dump(users_channels, f)


bot.polling(none_stop=True, interval=0)

# TODO: добавление канала вручную
# TODO: удаление канала/ов
# TODO: сделать нормальный поиск
# TODO: подключить бд
# TODO: залить на сервер




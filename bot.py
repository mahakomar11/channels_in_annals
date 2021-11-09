import telebot
from telebot import types
import json
from collections import OrderedDict
from searcher import get_matched
from decouple import config


bot = telebot.TeleBot(config('TOKEN'))

my_commands = ['Инструкция', 'Список каналов', 'Поиск по названию', 'Удалить канал', 'Удалить все каналы']
buttons = [types.KeyboardButton(text=command) for command in my_commands]
keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(*buttons)

IS_SEARCH_MODE = False
LAST_MESSAGE = None

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
    global IS_SEARCH_MODE
    global LAST_MESSAGE
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
        IS_SEARCH_MODE = True
    elif message.text == 'Удалить канал':
        bot.send_message(user_id, 'Напиши ключевое слово')
        IS_SEARCH_MODE = True
    elif message.text == 'Удалить все каналы' and LAST_MESSAGE != 'Удалить все каналы':
        bot.send_message(user_id, 'Каналы нельзя будет вернуть. Чтобы подтвердить удаление всех-всех каналов, нажми "Удалить все каналы" ещё раз')
    elif message.text == 'Удалить все каналы' and LAST_MESSAGE == 'Удалить все каналы':
        delete_all_channels(user_id)
        bot.send_message(user_id, 'Список каналов пуст.')
    elif IS_SEARCH_MODE and LAST_MESSAGE == 'Поиск по названию':
        bot.send_message(user_id, search_channels(user_id, message.text))
        IS_SEARCH_MODE = False
    elif IS_SEARCH_MODE and LAST_MESSAGE == 'Удалить канал':
        inline_keyboard = types.InlineKeyboardMarkup()
        button_yes = types.InlineKeyboardButton(text='Да',
                                                callback_data=message.text)
        button_no = types.InlineKeyboardButton(text='Нет',
                                               callback_data='no')
        inline_keyboard.add(button_yes, button_no)
        bot.send_message(user_id, search_channels(user_id, message.text, max=1))
        bot.send_message(user_id, 'Удалить этот канал?', reply_markup=inline_keyboard)
        IS_SEARCH_MODE = False
    elif message.forward_from_chat is None:
        bot.send_message(user_id, 'Сообщение должно быть переслано из канала.',
                         reply_markup=keyboard)
    else:
        # bot.send_message(user_id, message.forward_from_chat)  # technical message
        answer = add_channel(user_id, message.forward_from_chat)
        bot.send_message(user_id, answer, reply_markup=keyboard)
    LAST_MESSAGE = message.text

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    if call.data == 'sort':
        answer = display_channels(user_id, to_sort=True)
        bot.send_message(user_id, answer)
    elif call.data == 'no':
        bot.send_message(user_id, 'Нет так нет.')
    elif isinstance(call.data, str):
        delete_matched_channel(user_id, call.data)
        bot.send_message(user_id, 'Удалил!')


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


def search_channels(user_id, text, max=None):
    channels = _read_channels(user_id)
    chan_names = get_matched(text, channels.keys())
    if max is not None:
        chan_names = chan_names[:1]
    found_channels = {name: channels[name] for name in chan_names}
    return _create_message_from_channels(found_channels)


def delete_matched_channel(user_id, text):
    channels = _read_channels(user_id)
    chan_name = get_matched(text, channels.keys())[0]
    del channels[chan_name]
    with open('channels.json', 'w') as f:
        json.dump({user_id: channels}, f)


def delete_all_channels(user_id):
    with open('channels.json', 'w') as f:
        json.dump({user_id: {}}, f)


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
# TODO: подключить бд
# TODO: залить на сервер




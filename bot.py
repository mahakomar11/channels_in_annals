from re import T
import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException
import json
from collections import OrderedDict
from searcher import get_matched
from decouple import config


bot = telebot.TeleBot(config('TOKEN'))

my_commands = ['Инструкция', 'Список каналов', 'Поиск по названию', 'Добавить канал вручную', 'Удалить канал', 'Удалить все каналы']
buttons = [types.KeyboardButton(text=command) for command in my_commands]
keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(*buttons)

@bot.message_handler(commands=['start'])
def handle_command(message):
    if message.text == '/start':
        user_id = message.from_user.id
        bot.send_message(user_id, 'Привет, я — бот "Каналы в анналах".\n\n'
                                  'Я сделан, чтобы помогать Маше меньше прокрастинировать.\n\n'
                                  'Перешли мне свои каналы, и я их сохраню. '
                                  'Так ты сможешь от них отписаться, '
                                  'чтобы отвлекаться на них, только когда напишешь мне. '
                                  'Чтобы узнать как пользоваться, жми "Инструкция".',
                         reply_markup=keyboard)
        _write_channels(user_id, {})


@bot.message_handler(content_types=['text', 'photo', 'video',
                                    'document', 'sticker', 'video_note',
                                    'voice'])
def get_message(message):
    user_id = message.from_user.id
    last_message = _read_last_message(user_id)
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
    elif message.text == 'Добавить канал вручную':
        bot.send_message(user_id, 'Пришли мне ссылку на канал')
    elif message.text == 'Удалить канал':
        bot.send_message(user_id, 'Напиши ключевое слово')
    elif message.text == 'Удалить все каналы' and last_message != 'Удалить все каналы':
        bot.send_message(user_id, 'Каналы нельзя будет вернуть. Чтобы подтвердить удаление всех-всех каналов, нажми "Удалить все каналы" ещё раз')
    elif message.text == 'Удалить все каналы' and last_message == 'Удалить все каналы':
        delete_all_channels(user_id)
        bot.send_message(user_id, 'Список каналов пуст.')
    elif last_message == 'Поиск по названию':
        bot.send_message(user_id, search_channels(user_id, message.text))
    elif last_message == 'Добавить канал вручную':
        bot.send_message(user_id, add_channel_by_link(user_id, message.text))
    elif last_message == 'Удалить канал':
        inline_keyboard = types.InlineKeyboardMarkup()
        button_yes = types.InlineKeyboardButton(text='Да',
                                                callback_data=message.text)
        button_no = types.InlineKeyboardButton(text='Нет',
                                               callback_data='no')
        inline_keyboard.add(button_yes, button_no)
        answer = search_channels(user_id, message.text, max=1)
        bot.send_message(user_id, search_channels(user_id, message.text, max=1))
        if answer != 'Таких каналов не найдено, попробуй другое слово.':
            bot.send_message(user_id, 'Удалить этот канал?', reply_markup=inline_keyboard)
    elif message.forward_from_chat is None:
        bot.send_message(user_id, 'Сообщение должно быть переслано из канала.',
                         reply_markup=keyboard)
    else:
        # bot.send_message(user_id, message.forward_from_chat)  # technical message
        answer = add_channel(user_id, message.forward_from_chat)
        bot.send_message(user_id, answer, reply_markup=keyboard)
    _write_last_message(user_id, message.text)

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

def add_channel_by_link(user_id, message):
    channels = _read_channels(user_id)
    link = message.split(' ')[-1]
    if 't.me/' not in link:
        return 'Не вижу ссылки. Должна быть либо ссылка, либо "Название ссылка", через пробел.'
    if link != message:
        title = ' '.join(message.split(' ')[:-1])
    else:
        channel_id = '@' + link.split('/')[-1]
        try:
            channel_info = bot.get_chat(channel_id)
        except ApiTelegramException as e:
            return 'Не могу достать название, вероятно канал засекречен. Нажми "Добавить канал вручную" и пришли "Название ссылка", через пробел.'
        title = channel_info.title
    channels[title] = link
    _write_channels(user_id, channels)
    return f'Добавлен канал {title}!'

def add_channel_with_title(user_id, title, link):
    channels = _read_channels(user_id)
    channels[title] = link
    _write_channels(user_id, channels)
    return f'Добавлен канал {title}!'

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
    return _create_message_from_channels(found_channels, no_channels_message='Таких каналов не найдено, попробуй другое слово.')


def delete_matched_channel(user_id, text):
    channels = _read_channels(user_id)
    chan_name = get_matched(text, channels.keys())[0]
    del channels[chan_name]
    _write_channels(user_id, channels)


def delete_all_channels(user_id):
    _write_channels(user_id, {})


def _create_message_from_channels(channels, no_channels_message=None):
    if no_channels_message is None:
        no_channels_message = 'Каналы не добавлены! Чтобы добавить канал, перешли мне сообщение из него.'
    if len(channels) == 0:
        return no_channels_message
    channels_list = [f'{title}:\n\t\t\t\t\t\t\t\t\t{link}' for title, link in channels.items()]
    return '\n'.join(channels_list)


def _read_last_message(user_id):
    with open('channels.json') as f:
        users_channels = json.load(f)
    if len(users_channels) != 0:
        return users_channels[str(user_id)]['last_message']
    else:
        return None

def _read_channels(user_id):
    with open('channels.json') as f:
        users_channels = json.load(f)
    if len(users_channels) != 0:
        return users_channels[str(user_id)]['channels']
    else:
        return {}


def _write_channels(user_id, channels):
    with open('channels.json', 'r+') as f:
        users_channels = json.load(f)
        if str(user_id) not in users_channels:
            users_channels[str(user_id)] = {'channels': {}, 'last_message': '/start'}
        
        users_channels[str(user_id)]['channels'] = channels
        f.seek(0)
        json.dump(users_channels, f)
        f.truncate()


def _write_last_message(user_id, last_message):
    with open('channels.json', 'r+') as f:
        users_channels = json.load(f)
        users_channels[str(user_id)]['last_message'] = last_message
        f.seek(0)
        json.dump(users_channels, f)
        f.truncate()


bot.polling(none_stop=True, interval=0)

# TODO: обернуть операции с каналами в класс
# TODO: подключить бд
# TODO: залить на сервер
# TODO: добавить логирование
# TODO: доставать из ссылки название или из пересланного сообщения ссылку




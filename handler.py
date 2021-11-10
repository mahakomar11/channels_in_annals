import json
from collections import OrderedDict
from telebot.apihelper import ApiTelegramException
from utils import get_matched


class UserDataHandler:
    def __init__(self, user_id) -> None:
        self.user_id = str(user_id)

    def add_channel(self, channel: dict) -> str:
        channels = self._read_channels()

        if channel.username is None:
            return "Не могу достать ссылку, вероятно канал засекречен."

        channels[channel.title] = f"t.me/{channel.username}"
        self.write_channels(channels)
        return f"Добавлен канал {channel.title}!"

    def add_channel_by_link(self, message, bot) -> str:
        channels = self._read_channels()
        link = message.split(" ")[-1]

        if "t.me/" not in link:
            return (
                'Не вижу ссылки. Должна быть либо ссылка, либо "Название'
                ' ссылка", через пробел.'
            )

        if link != message:
            title = " ".join(message.split(" ")[:-1])
        else:
            channel_id = "@" + link.split("/")[-1]
            try:
                channel_info = bot.get_chat(channel_id)
            except ApiTelegramException:
                return (
                    "Не могу достать название, вероятно канал засекречен."
                    ' Нажми "Добавить канал вручную" и пришли "Название'
                    ' ссылка", через пробел.'
                )
            title = channel_info.title

        channels[title] = link
        self.write_channels(channels)
        return f"Добавлен канал {title}!"

    def add_channel_with_title(self, title, link) -> str:
        channels = self._read_channels()
        channels[title] = link
        self.write_channels(channels)
        return f"Добавлен канал {title}!"

    def display_channels(self, to_sort=False) -> str:
        channels = self._read_channels()
        if to_sort:
            channels = OrderedDict(sorted(channels.items()))
        return self._create_message_from_channels(channels)

    def search_channels(self, keyword, max_num=None) -> str:
        channels = self._read_channels()
        chan_names = get_matched(keyword, channels.keys())

        if max_num is not None:
            chan_names = chan_names[:max_num]

        found_channels = {name: channels[name] for name in chan_names}

        return self._create_message_from_channels(
            found_channels,
            no_channels_message=(
                "Таких каналов не найдено, попробуй другое слово."
            ),
        )

    def delete_matched_channel(self, keyword) -> None:
        channels = self._read_channels()
        chan_name = get_matched(keyword, channels.keys())[0]
        del channels[chan_name]
        self.write_channels(channels)

    def delete_all_channels(self) -> None:
        self.write_channels({})

    def _create_message_from_channels(
        self, channels, no_channels_message=None
    ) -> str:
        if no_channels_message is None:
            no_channels_message = (
                "Каналы не добавлены! Чтобы добавить канал, перешли мне"
                " сообщение из него."
            )

        if len(channels) == 0:
            return no_channels_message

        channels_list = [
            f"{title}:\n\t\t\t\t\t\t\t\t\t{link}"
            for title, link in channels.items()
        ]
        return "\n".join(channels_list)

    def _read_channels(self) -> dict:
        with open("channels.json") as f:
            users_channels = json.load(f)

        if self.user_id not in users_channels:
            self._add_new_user(users_channels)

        return users_channels[self.user_id]["channels"]

    def read_last_message(self) -> str:
        with open("channels.json") as f:
            users_channels = json.load(f)

        if self.user_id not in users_channels:
            self._add_new_user(users_channels)

        return users_channels[self.user_id]["last_message"]

    def write_channels(self, channels) -> None:
        with open("channels.json", "r+") as f:
            users_channels = json.load(f)

            if self.user_id not in users_channels:
                self._add_new_user(users_channels)

            users_channels[self.user_id]["channels"] = channels
            f.seek(0)
            json.dump(users_channels, f)
            f.truncate()

    def write_last_message(self, last_message) -> None:
        with open("channels.json", "r+") as f:
            users_channels = json.load(f)

            if self.user_id not in users_channels:
                self._add_new_user(users_channels)

            users_channels[self.user_id]["last_message"] = last_message
            f.seek(0)
            json.dump(users_channels, f)
            f.truncate()

    def _add_new_user(self, users_channels) -> None:
        users_channels[self.user_id] = {
            "channels": {},
            "last_message": "/start",
        }

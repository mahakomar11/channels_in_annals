from collections import OrderedDict

from telebot.apihelper import ApiTelegramException

from db import DB
from utils import get_matched


class User:
    def __init__(self, user_id: int, db: DB) -> None:
        self.user_id = user_id
        self.db = db

    def read_last_message(self) -> str:
        return self.db.get_last_message(self.user_id)

    def write_last_message(self, last_message) -> None:
        self.db.upsert_last_message(self.user_id, last_message)

    def add_channel(self, channel) -> str:
        if channel.username is None:
            return "Не могу достать ссылку, вероятно канал засекречен."

        link = f"t.me/{channel.username}"
        self.db.upsert_channel(
            self.user_id,
            channel.title,
            link,
        )
        return f"Добавлен канал {channel.title}:\n{link}"

    def add_channel_by_link(self, message, bot) -> str:
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

        self.db.upsert_channel(self.user_id, title, link)
        return f"Добавлен канал {title}!"

    def display_channels(self, to_sort=False) -> str:
        channels = self.db.get_channels(self.user_id)
        if to_sort:
            channels = OrderedDict(sorted(channels.items()))
        return self._create_message_from_channels(channels)

    def search_channels(self, keyword, max_num=None) -> str:
        channels = self.db.get_channels(self.user_id)
        chan_names = get_matched(keyword, channels.keys())

        if max_num is not None:
            chan_names = chan_names[:max_num]

        found_channels = {name: channels[name] for name in chan_names}

        return self._create_message_from_channels(
            found_channels,
            no_channels_message=("Таких каналов не найдено, попробуй другое слово."),
        )

    def delete_matched_channel(self, keyword) -> None:
        channels = self.db.get_channels(self.user_id)
        chan_name = get_matched(keyword, channels.keys())[0]
        self.db.delete_channel(self.user_id, chan_name)

    def delete_all_channels(self) -> None:
        self.db.delete_all_channels(self.user_id)

    @staticmethod
    def _create_message_from_channels(
        channels,
        no_channels_message=None,
    ) -> str:
        if no_channels_message is None:
            no_channels_message = (
                "Каналы не добавлены! Чтобы добавить канал, перешли мне"
                " сообщение из него."
            )

        if not channels:
            return no_channels_message

        channels_list = [f"{title}:\n{link}" for title, link in channels.items()]
        return "\n".join(channels_list)


if __name__ == "__main__":
    user = User(4, DB())
    user.write_last_message("")

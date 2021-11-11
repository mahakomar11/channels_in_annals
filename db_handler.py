import sqlite3
import inspect


class SQLiteConnection:
    def __init__(self, db_name) -> None:
        self.db_name = db_name
        self.con = None
        self.cur = None

    def create_last_messages(self):
        self.cur.execute(
            """
        --sql
        CREATE TABLE last_messages
        (user_id INT PRIMARY KEY, last_message TEXT)
        ;
        """
        )

    def create_channels(self):
        self.cur.execute(
            """
        --sql
        CREATE TABLE channels
        (channel_name TEXT, channel_link TEXT, user_id INT, UNIQUE(channel_name, user_id))
        ;
        """
        )

    def get_last_message(self, user_id):
        self.cur.execute(
            """
        --sql
        SELECT last_message
        FROM last_messages
        WHERE user_id=:user_id
        ;
        """,
            {"user_id": user_id},
        )

        result = self.cur.fetchone()
        if result is None:
            print(f'No user {user_id} in database. Write the last message for creating one')
            return None

        return result[0]

    def upsert_last_message(self, user_id, last_message):
        self.cur.execute(
            """
        --sql
        INSERT INTO last_messages
        VALUES (?, ?)
        ON CONFLICT (user_id) DO UPDATE SET last_message=excluded.last_message
        ;
        """,
            (user_id, last_message),
        )

    def get_channels(self, user_id):
        self.cur.execute(
            """
        --sql
        SELECT channel_name, channel_link
        FROM channels
        WHERE user_id=:user_id
        ;
        """,
            {"user_id": user_id},
        )

        return self._channels_to_dict(self.cur.fetchall())

    def upsert_channel(self, user_id, channel_name, channel_link):
        self.cur.execute(
            """
        --sql
        INSERT INTO channels (channel_name, channel_link, user_id)
        VALUES (?, ?, ?)
        ON CONFLICT (channel_name, user_id) DO UPDATE SET channel_link=excluded.channel_link
        ;
        """,
            (channel_name, channel_link, user_id),
        )

    def delete_channel(self, user_id, channel_name):
        self.cur.execute(
            """
        --sql
        DELETE FROM channels
        WHERE user_id=:user_id and channel_name=:channel_name 
        ;
        """,
            {"user_id": user_id, "channel_name": channel_name},
        )

    def delete_all_channels(self, user_id):
        self.cur.execute(
            """
        --sql
        DELETE FROM channels
        WHERE user_id=:user_id 
        ;
        """,
            {"user_id": user_id},
        )

    @staticmethod
    def _channels_to_dict(query_result):
        channels = {}
        for row in query_result:
            channels[row[0]] = row[1]
        return channels

    def __getattribute__(self, attr: str):
        method = object.__getattribute__(self, attr)
        if inspect.ismethod(method) and attr != "_decorate":
            method = self._decorate(method)
        return method

    def _decorate(self, func):
        def wrapper(*args, **kwargs):
            self.con = sqlite3.connect(self.db_name)
            self.cur = self.con.cursor()
            result = func(*args, **kwargs)
            self.con.commit()
            self.con.close()
            return result

        return wrapper


if __name__ == "__main__":
    db = SQLiteConnection("channels.db")
    print(db.get_last_message(1))

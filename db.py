from os import getenv

from sqlalchemy import create_engine
from sqlalchemy.orm import Session


class DB:
    def __init__(self) -> None:
        db_url = getenv('DATABASE_URL').split('//')[1]
        self.session = Session(create_engine(f'postgresql+psycopg2://{db_url}'))

    def setup(self):
        self.session.execute("""
        CREATE SCHEMA IF NOT EXISTS annals;
        """)
        self.session.execute("""
        CREATE TABLE IF NOT EXISTS annals.last_messages
        (user_id INT PRIMARY KEY, last_message TEXT);
        """)
        self.session.execute("""
        CREATE TABLE IF NOT EXISTS annals.channels
        (channel_name TEXT, channel_link TEXT, user_id INT, UNIQUE(channel_name, user_id));
        """)
        self.session.commit()

    def get_last_message(self, user_id):
        result = self.session.execute(f"""
        SELECT last_message
        FROM annals.last_messages
        WHERE user_id={user_id}
        ;
        """).all()

        if not result:
            print(
                f"No user {user_id} in database. Write the last message for"
                " creating one"
            )
            return None

        return result[0][0]

    def upsert_last_message(self, user_id, last_message):
        self.session.execute(f"""
        INSERT INTO annals.last_messages
        VALUES ({user_id}, '{last_message}')
        ON CONFLICT (user_id) DO UPDATE SET last_message=excluded.last_message
        ;
        """)
        self.session.commit()

    def get_channels(self, user_id):
        result = self.session.execute(f"""
        SELECT channel_name, channel_link
        FROM annals.channels
        WHERE user_id={user_id}
        ;
        """).all()

        return self._channels_to_dict(result)

    def upsert_channel(self, user_id, channel_name, channel_link):
        self.session.execute(f"""
        INSERT INTO annals.channels (channel_name, channel_link, user_id)
        VALUES ('{channel_name}', '{channel_link}', {user_id})
        ON CONFLICT (channel_name, user_id) DO UPDATE SET channel_link=excluded.channel_link
        ;
        """)
        self.session.commit()

    def delete_channel(self, user_id, channel_name):
        self.session.execute(f"""
        DELETE FROM annals.channels
        WHERE user_id={user_id} and channel_name='{channel_name}' 
        ;
        """)
        self.session.commit()

    def delete_all_channels(self, user_id):
        self.session.execute(f"""
        DELETE FROM annals.channels
        WHERE user_id={user_id} 
        ;
        """)
        self.session.commit()

    @staticmethod
    def _channels_to_dict(query_result):
        channels = {}
        for row in query_result:
            channels[row[0]] = row[1]
        return channels


if __name__ == "__main__":
    db = DB()
    lm = db.get_last_message(2)
    # db.upsert_channel(1, 'Name1', 'link1')
    db.delete_all_channels(1)

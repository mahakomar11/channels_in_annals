from os import getenv

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema
from models import AnnalsBase, LastMessages, Channels


class DB:
    def __init__(self) -> None:
        postgres_user = getenv("POSTGRES_USER")
        postgres_pass = getenv("POSTGRES_PASSWORD")
        postgres_db = getenv('POSTGRES_DB')
        db_url = f"postgresql+psycopg2://{postgres_user}:{postgres_pass}@dbpostgres:5432/{postgres_db}"
        self.session = Session(create_engine(db_url))

    def setup(self):
        if not self.session.bind.dialect.has_schema(self.session.bind, schema='annals'):
            self.session.execute(CreateSchema('annals'))
            self.session.commit()
        AnnalsBase.metadata.create_all(self.session.bind)

    def get_last_message(self, user_id):
        result = self.session.get(LastMessages, user_id)
        if not result:
            print(
                f"No user {user_id} in database. Write the last message for"
                " creating one"
            )
            return None

        return result.last_message

    def upsert_last_message(self, user_id, last_message):
        self.session.execute(LastMessages.upsert(user_id, last_message))
        self.session.commit()

    def get_channels(self, user_id):
        result = self.session.query(Channels.channel_name, Channels.channel_link).filter_by(user_id=user_id).all()
        return self._channels_to_dict(result)

    def upsert_channel(self, user_id, channel_name, channel_link):
        self.session.execute(Channels.upsert(channel_name, channel_link, user_id))
        self.session.commit()

    def delete_channel(self, user_id, channel_name):
        channel_to_delete = self.session.get(Channels, (channel_name, user_id))
        if channel_to_delete:
            self.session.delete(channel_to_delete)
            self.session.commit()

    def delete_all_channels(self, user_id):
        self.session.query(Channels).filter_by(user_id=user_id).delete()
        self.session.commit()

    @staticmethod
    def _channels_to_dict(query_result):
        channels = {}
        for row in query_result:
            channels[row[0]] = row[1]
        return channels


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    db = DB()
    db.setup()
    lm = db.get_last_message(1)
    db.upsert_last_message(1, 'b')
    db.upsert_last_message(1, 'c')
    lm = db.get_last_message(1)
    chans = db.get_channels(1)
    db.delete_channel(1, 'chan')
    db.delete_channel(1, 'chan')
    db.upsert_channel(1, 'chan2', 'link2')
    db.delete_all_channels(1)
    db.delete_channel(1, "Name'1")

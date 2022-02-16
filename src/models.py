from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData, ForeignKey, Column, Integer, String
from sqlalchemy.dialects.postgresql import insert

AnnalsBase = declarative_base(metadata=MetaData(schema="annals"))


class LastMessages(AnnalsBase):
    __tablename__ = "last_messages"

    user_id = Column(Integer, primary_key=True)
    last_message = Column(String)

    def __repr__(self):
        return f"<LastMessages(user_id={self.user_id}, last_message='{self.last_message}')>"

    @classmethod
    def upsert(cls, user_id, last_message):
        insertion = insert(cls).values(user_id=user_id, last_message=last_message)
        return insertion.on_conflict_do_update(
            index_elements=[cls.user_id], set_=dict(last_message=last_message)
        )


class Channels(AnnalsBase):
    __tablename__ = "channels"

    channel_name = Column(String, primary_key=True)
    channel_link = Column(String)
    user_id = Column(ForeignKey(LastMessages.user_id), primary_key=True)

    def __repr__(self):
        return (
            f"<Channels(channel_name={self.channel_name}, channel_link='{self.channel_link}', "
            f"user_id={self.user_id})>"
        )

    @classmethod
    def upsert(cls, channel_name, channel_link, user_id):
        insertion = insert(cls).values(
            channel_name=channel_name, channel_link=channel_link, user_id=user_id
        )
        return insertion.on_conflict_do_update(
            index_elements=[cls.channel_name, cls.user_id],
            set_=dict(channel_link=channel_link),
        )

from datetime import datetime

from peewee import *
from playhouse.sqliteq import SqliteQueueDatabase

from comments import config


db = SqliteQueueDatabase('data/comments.db')


class Comment(Model):
    """
    Simple object for storing comments and associating
    them with any given URL.
    """
    id = AutoField()
    datestamp = DateTimeField(default=datetime.utcnow)
    approved = BooleanField(default=config.AUTO_APPROVE)
    name = CharField(null=False)
    message = TextField(null=False)
    url = CharField(null=False)

    class Meta:
        database = db


db.create_tables([Comment])
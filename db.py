from peewee import *

db = SqliteDatabase('db.db')


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    user_id = IntegerField()
    verified = BooleanField()
    phone = TextField()


db.create_tables([User])

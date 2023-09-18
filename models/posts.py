from sqlalchemy import Integer, String, Date, Unicode, UnicodeText
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from sqlalchemy import Column
from db import db


class Posts(db.Model):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_date: Mapped[int] = mapped_column(Date, nullable=False, default=datetime.now())
    path: Column = Column(Unicode(128), nullable=False)
    text: Column = Column(UnicodeText)

    def __unicode__(self):
        return self.name

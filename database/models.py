import asyncio
import os
from os.path import exists
from typing import Optional, List

from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String, Text,
                        UniqueConstraint, func, join, select, LargeBinary)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import (DeclarativeBase, Mapped, declarative_base,
                            relationship, mapped_column)

load_dotenv()

engine = create_async_engine(str(os.getenv("ENGINE")))

async_session = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)
session = async_session()

async def get_session() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
            await session.close()


class Base(DeclarativeBase):
    pass

async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class Tweet(Base):
    __tablename__ = "tweets"
    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    tweet_data = Column(Text, nullable=False)
    # tweet_media_ids: Mapped[Optional[List[int]]] = Column(
    #     ARRAY(Integer), nullable=True
    # )
    tweet_media_ids: Mapped[Optional[List[int]]] = mapped_column(
        ARRAY(Integer, dimensions=1), nullable=True
    )
    created_at = Column(DateTime, default=func.now())

    user = relationship("Users", back_populates="tweets")
    likes = relationship(
        "Like", back_populates="tweet", cascade="all, delete", passive_deletes=True
    )


class Media(Base):
    __tablename__ = "medias"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file = Column(LargeBinary)
    created_at = Column(DateTime, default=func.now())


class Like(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    tweet_id = Column(
        Integer, ForeignKey("tweets.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "tweet_id", name="unique_user_tweet_like"),
    )

    user = relationship("Users", back_populates="likes")
    tweet = relationship("Tweet", back_populates="likes")


class Follow(Base):
    __tablename__ = "follows"
    id = Column(Integer, primary_key=True)
    follower_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    following_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="unique_follow"),
    )

    follower = relationship(
        "Users", foreign_keys=[follower_id], back_populates="follows_as_follower"
    )
    following = relationship(
        "Users", foreign_keys=[following_id], back_populates="follows_as_following"
    )


class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    api_key = Column(String(255), unique=True)

    # Отношения
    tweets = relationship("Tweet", back_populates="user", cascade="all, delete")
    likes = relationship("Like", back_populates="user", cascade="all, delete")
    follows_as_follower = relationship(
        "Follow",
        foreign_keys=[Follow.follower_id],
        back_populates="follower",
        cascade="all, delete",
    )
    follows_as_following = relationship(
        "Follow",
        foreign_keys=[Follow.following_id],
        back_populates="following",
        cascade="all, delete",
    )


#
# asyncio.run(create_db())

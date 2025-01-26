from sqlalchemy import Column, Integer, String
from typing import Optional, List
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, async_sessionmaker
from sqlalchemy.future import select

DATABASE_URL = "sqlite+aiosqlite:///db.sqlite3"


async_engine = create_async_engine(DATABASE_URL, echo=True)


async_session = async_sessionmaker(async_engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    tg_id: str = Column(String, unique=True, index=True)
    days_no_reply: int = Column(Integer, default=0)
    days_with_reply: int = Column(Integer, default=0)


async def create_user(tg_id: str):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(User).filter_by(tg_id=tg_id))
            user = result.scalars().first()
            if not user:
                user = User(tg_id=tg_id)
                session.add(user)
            await session.commit()
            return user


async def get_days_no_reply(tg_id: str) -> int:
    async with async_session() as session:
        result = await session.execute(select(User).filter_by(tg_id=tg_id))
        user = result.scalars().first()
        return user.days_no_reply if user else 0


async def get_days_with_reply(tg_id: str) -> int:
    async with async_session() as session:
        result = await session.execute(select(User).filter_by(tg_id=tg_id))
        user = result.scalars().first()
        return user.days_with_reply if user else 0


async def update_days_no_reply(tg_id: str):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(User).filter_by(tg_id=tg_id))
            user = result.scalars().first()
            if user:
                user.days_no_reply += 1  # Увеличиваем на 1
            await session.commit()


async def update_days_with_reply(tg_id: str):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(User).filter_by(tg_id=tg_id))
            user = result.scalars().first()
            if user:
                user.days_with_reply += 1  # Увеличиваем на 1
            await session.commit()


async def reset_days_no_reply(tg_id: str):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(User).filter_by(tg_id=tg_id))
            user = result.scalars().first()
            if user:
                user.days_no_reply = 0  # Устанавливаем дни без ответа на 0
            await session.commit()


async def async_main():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from states.states import Questions
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db.models import async_main, update_days_with_reply, update_days_no_reply, get_days_with_reply, get_days_no_reply, create_user, reset_days_no_reply

from datetime import datetime, timedelta

TOKEN = getenv(key="TOKEN")

bot = Bot(token='7061648459:AAG-6EcT5k-kl0htGid7aa2jPGtE_2q50C8', default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()
scheduler = AsyncIOScheduler()

async def send_reminder(chat_id, state):
    await update_days_no_reply(str(chat_id))
    
    job = scheduler.get_job(f"reminder_{chat_id}")
    if job:
        job.remove()
    
    if await get_days_no_reply(chat_id) >= 3:
        await bot.send_message(chat_id=chat_id, text='От вас нет активности, я прекращаю свою работу. Чтобы продолжить, нажмите /start')
        return

    await bot.send_message(chat_id=chat_id, text='Настало время отвечать на вопросы!')
    scheduler.add_job(first_question, 'date', run_date=datetime.now() + timedelta(seconds=5), args=[chat_id, state], id=f"reminder_{chat_id}") #через сутки

async def first_question(chat_id: int, state):
    if await get_days_with_reply(str(chat_id)) == 5:
        await bot.send_message(chat_id=chat_id, text='Чтобы продолжить пользоваться ботом необходимо внести оплату:')

    await bot.send_message(chat_id=chat_id, text='Напиши три вещи, за которые ты благодарен сегодня?')
    await state.set_state(Questions.first)
    scheduler.add_job(send_reminder, 'date', run_date=datetime.now() + timedelta(seconds=5), args=[chat_id, state], id=f"reminder_{chat_id}")


async def second_question(chat_id: int, state):
    await bot.send_message(chat_id=chat_id, text='Напиши 3 пункта, почему ты сегодня молодец')
    await state.set_state(Questions.second)
    scheduler.add_job(send_reminder, 'date', run_date=datetime.now() + timedelta(seconds=5), args=[chat_id, state], id=f"reminder_{chat_id}")

@dp.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    await create_user(str(message.from_user.id))
    await reset_days_no_reply(str(message.from_user.id))
    await message.answer("Добро пожаловать!")
    await first_question(chat_id=message.chat.id, state=state)


@dp.message(Questions.first)
async def handle_first_message(message: Message, state: FSMContext):
    await state.clear()
    job = scheduler.get_job(f"reminder_{message.chat.id}")
    if job:
        job.remove()
    await second_question(chat_id=message.chat.id, state=state)


@dp.message(Questions.second)
async def handle_second_message(message: Message, state: FSMContext):
    await state.clear()
    await reset_days_no_reply(str(message.from_user.id))
    job = scheduler.get_job(f"reminder_{message.chat.id}")
    if job:
        job.remove()
    await message.answer('Молодец!')
    scheduler.add_job(first_question, 'date', run_date=datetime.now() + timedelta(seconds=5), args=[message.from_user.id, state], id=f"reminder_{message.from_user.id}") #через сутки
    await update_days_with_reply(str(message.from_user.id))


@dp.message()
async def text_handler(message: Message):
    await message.answer(text='Нажмите /start чтобы нажать пользоваться ботом')

async def main():
    await async_main()
    scheduler.start()
    await dp.start_polling(bot, skip_updates=False)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
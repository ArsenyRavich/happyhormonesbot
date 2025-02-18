import asyncio
import logging
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.utils import executor

API_TOKEN = "7925232029:AAG-FLpXxN9jT4c-vbDAg_B8RzmPEkvyc30"
WEBHOOK_HOST = "https://your-vercel-app.vercel.app"
WEBHOOK_PATH = f"/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
app = FastAPI()

# Все остальное как было в вашем коде

keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[[KeyboardButton(text="Да"), KeyboardButton(text="Нет")]]
)

questions = {
    "dopamine": ["Прокрастинирую и откладываю дела на потом?", "Ощущаю недостаток мотивации и энергии?"],
    "serotonin": ["Чувствую тревогу, даже без видимой причины?", "У меня резкое падение настроения?"],
    "oxytocin": ["Мне не хватает теплых, доверительных отношений?", "Я чувствую себя одиноко даже среди людей?"],
    "endorphins": ["У меня головные боли или напряжение в теле?", "Я мало двигаюсь и редко занимаюсь спортом?"]
}

hormone_recommendations = {
    "dopamine": "Рекомендуется:\n- ставить маленькие цели...",
    "serotonin": "Рекомендуется:\n- проводить время на солнце...",
    "oxytocin": "Рекомендуется:\n- обниматься с близкими...",
    "endorphins": "Рекомендуется:\n- физическая активность..."
}

user_answers = {}
reminders = {}

@app.post("/webhook")
async def webhook(request: Request):
    json_data = await request.json()
    update = types.Update(**json_data)
    await dp.process_update(update)
    return {"status": "ok"}

@dp.message_handler(Command("start"))
async def start(message: types.Message):
    user_answers[message.chat.id] = {
        "dopamine": 0, "serotonin": 0, "oxytocin": 0, "endorphins": 0,
        "index": 0, "category": "dopamine"
    }
    await ask_question(message.chat.id)

async def ask_question(chat_id):
    user_data = user_answers.get(chat_id)
    if not user_data:
        return

    category = user_data["category"]
    index = user_data["index"]

    if index < len(questions[category]):
        question = questions[category][index]
        await bot.send_message(chat_id, question, reply_markup=keyboard)
    else:
        await next_category(chat_id)

@dp.message_handler(lambda message: message.text in ["Да", "Нет"])
async def handle_answer(message: types.Message):
    chat_id = message.chat.id
    user_data = user_answers.get(chat_id)
    if not user_data:
        return

    category = user_data["category"]
    index = user_data["index"]

    if message.text == "Да":
        user_data[category] += 1

    user_data["index"] += 1
    await ask_question(chat_id)

async def next_category(chat_id):
    user_data = user_answers.get(chat_id)
    categories = list(questions.keys())
    current_index = categories.index(user_data["category"])

    if current_index < len(categories) - 1:
        user_data["category"] = categories[current_index + 1]
        user_data["index"] = 0
        await ask_question(chat_id)
    else:
        await send_results(chat_id)

async def send_results(chat_id):
    user_data = user_answers.get(chat_id)
    if not user_data:
        return

    recommendations = [hormone_recommendations[h] for h in user_data if
                       h in hormone_recommendations and user_data[h] >= 3]

    if recommendations:
        await bot.send_message(chat_id, "\n\n".join(recommendations), reply_markup=types.ReplyKeyboardRemove())
    else:
        await bot.send_message(chat_id, "Все гормоны в норме, у вас все в порядке, поздравляю!",
                               reply_markup=types.ReplyKeyboardRemove())

    await ask_reminder(chat_id)
    del user_answers[chat_id]

async def ask_reminder(chat_id):
    reminder_keyboard = ReplyKeyboardMarkup(
        keyboard=[["Раз в день", "Раз в 3 дня"], ["Раз в неделю", "Не нужно"]],
        resize_keyboard=True
    )
    await bot.send_message(chat_id, "Хотите установить напоминание?", reply_markup=reminder_keyboard)

@dp.message_handler(lambda message: message.text in ["Раз в день", "Раз в 3 дня", "Раз в неделю", "Не нужно"])
async def set_reminder(message: types.Message):
    chat_id = message.chat.id
    if message.text == "Не нужно":
        await bot.send_message(chat_id, "Хорошо, напоминаний не будет!", reply_markup=types.ReplyKeyboardRemove())
        return

    reminders[chat_id] = {
        "frequency": message.text,
        "reminder_time": datetime.now(timezone.utc)
    }
    await bot.send_message(chat_id, f"Напоминание установлено: {message.text}",
                           reply_markup=types.ReplyKeyboardRemove())

async def send_reminders():
    while True:
        now = datetime.now(timezone.utc)
        for chat_id, reminder in reminders.items():
            frequency = reminder["frequency"]
            delta = {"Раз в день": 1, "Раз в 3 дня": 3, "Раз в неделю": 7}.get(frequency, None)
            if delta and now - reminder["reminder_time"] >= timedelta(days=delta):
                await bot.send_message(chat_id, "Это напоминание о вашем здоровье!")
                reminders[chat_id]["reminder_time"] = now
        await asyncio.sleep(60)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    asyncio.create_task(send_reminders())

if __name__ == "__main__":
    asyncio.run(main())

import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
import asyncio

API_TOKEN = "7925232029:AAG-FLpXxN9jT4c-vbDAg_B8RzmPEkvyc30"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

questions = {
    "dopamine": [
        "Прокрастинирую и откладываю дела на потом?",
        "Ощущаю недостаток мотивации и энергии?",
        "Мне сложно радоваться маленьким успехам?",
        "Чувствую скуку и апатию?",
        "Мне не хватает вдохновения и желания развиваться?"
    ],
    "serotonin": [
        "Чувствую тревогу, даже без видимой причины?",
        "У меня резкое падение настроения?",
        "У меня нет ощущения благодарности за то, что у меня есть?",
        "Сравниваю себя с другими и чувствую себя хуже?",
        "Мне кажется, что жизнь бессмысленна?"
    ],
    "oxytocin": [
        "Мне не хватает теплых, доверительных отношений?",
        "Я чувствую себя одиноко даже среди людей?",
        "Мне сложно доверять и чувствовать близость?",
        "Я не могу проявлять нежность или не чувствую её от других?",
        "Объятия и прикосновения не присутствуют в  моей жизни?"
    ],
    "endorphins": [
        "У меня головные боли или напряжение в теле?",
        "Я мало двигаюсь и редко занимаюсь спортом?",
        "Мне не хватает ощущения эйфории или удовольствия?",
        "Я не смеюсь и не испытываю чувство радости?",
        "Болезни или усталость мешают мне наслаждаться жизнью?"
    ]
}

hormone_recommendations = {
    "dopamine": "Вам может не хватать дофамина. Рекомендуется: </t>- ставить маленькие цели и достигать их </t>- радоваться даже мелким успехам </t>- заниматься творчеством </t>- пробовать новое </t>- награждать себя </t>- слушать любимую музыку </t>- продукты с  тирозином: бананы, орехи и семена, темный шоколад,соевые продукты, рыба и яйца",
    "serotonin": "Возможно, у вас низкий уровень серотонина. Рекомендуется: </t>- проводить время на солнце </t>- есть больше продуктов с триптофаном (бананы, орехи (миндаль), индейка, курица, овсянка, бобовыеб семена тыквы и кунжута) </t>- вести дневник благодарности </t>- заниматься медитацией",
    "oxytocin": "Окситоцин может быть снижен. Рекомендуется: </t>- обниматься с близкими </t>- общаться с приятными людьми </t>- заботиться о ком-то или чем-то </t>- проводить время с животными </t>- продукты, богатые омега-3 жирными кислотами, магнием и витамином D: яйца, авокадо, рыба, брокколи, шпинат, ягоды, ферментированные продукты (прим.: квашенная капуста)",
    "endorphins": "Похоже, у вас низкий уровень эндорфинов. Рекомендуется: </t>- физическая активность, спорт </t>- смех </t>- вкусная еда </t>- приятные занятия </t>- танцы </t>- шоколад (темный), пряности (прим.: чили, имбирь), ягоды, цитрусовые, яблоки, гранат"
}

user_answers = {}
reminders = {}


@dp.message_handler(commands=['start'])
def start(message: types.Message):
    user_answers[message.chat.id] = {"dopamine": 0, "serotonin": 0, "oxytocin": 0, "endorphins": 0, "index": 0,
                                     "category": "dopamine"}
    ask_question(message.chat.id)


def ask_question(chat_id):
    user_data = user_answers.get(chat_id)
    if not user_data:
        return

    category = user_data["category"]
    index = user_data["index"]

    if index < len(questions[category]):
        question = questions[category][index]
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton("Да"), KeyboardButton("Нет"))
        bot.send_message(chat_id, question, reply_markup=keyboard)
    else:
        next_category(chat_id)


def next_category(chat_id):
    user_data = user_answers.get(chat_id)
    categories = list(questions.keys())
    current_index = categories.index(user_data["category"])

    if current_index < len(categories) - 1:
        user_data["category"] = categories[current_index + 1]
        user_data["index"] = 0
        ask_question(chat_id)
    else:
        send_results(chat_id)


def send_results(chat_id):
    user_data = user_answers.get(chat_id)
    if not user_data:
        return

    max_hormone = max(user_data, key=lambda x: user_data[x] if x != "index" and x != "category" else -1)
    bot.send_message(chat_id, hormone_recommendations[max_hormone], reply_markup=types.ReplyKeyboardRemove())
    ask_reminder(chat_id)
    del user_answers[chat_id]


def ask_reminder(chat_id):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Раз в день", "Раз в 3 дня", "Раз в неделю", "Не нужно напоминать")
    bot.send_message(chat_id, "Хотите получать регулярные напоминания о прохождении опроса? Выберите частоту:",
                     reply_markup=keyboard)


@dp.message_handler()
def handle_answer(message: types.Message):
    user_data = user_answers.get(message.chat.id)
    if not user_data:
        handle_reminder(message)
        return

    if message.text == "Да":
        user_data[user_data["category"]] += 1

    user_data["index"] += 1
    ask_question(message.chat.id)


def handle_reminder(message: types.Message):
    if message.text in ["Раз в день", "Раз в 3 дня", "Раз в неделю"]:
        interval = {"Раз в день": 86400, "Раз в 3 дня": 259200, "Раз в неделю": 604800}[message.text]
        reminders[message.chat.id] = interval
        bot.send_message(message.chat.id, "Хорошо! Я буду напоминать вам.")
        asyncio.create_task(send_reminders(message.chat.id, interval))
    elif message.text == "Не нужно напоминать":
        bot.send_message(message.chat.id, "Окей, напоминать не буду.")


def send_reminders(chat_id, interval):
    while chat_id in reminders:
        asyncio.sleep(interval)
        bot.send_message(chat_id, "Пора снова пройти опрос! Напишите /start.")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

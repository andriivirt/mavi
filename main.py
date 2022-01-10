from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.filters.state import State, StatesGroup

import random
import aioschedule
import asyncio
import configparser

config = configparser.ConfigParser()
config.read("config.ini", encoding='utf-8')

admin_id = config.get("SETTING", "admin_id")
TOKEN = config.get("SETTING", "token")

bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())


# Check DM of bot
class IsPrivate(BoundFilter):
    async def check(self, message: types.Message):
        if message.chat.type == types.ChatType.PRIVATE and message.from_user.id == int(admin_id):
            return True
        else:
            return False


class Form(StatesGroup):
    form_edit_percent = State()
    form_add_words = State()
    form_remove_words = State()


main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(KeyboardButton('📃 Список'))
main_menu.add(KeyboardButton('➕ Додати'), KeyboardButton('➖ Видалити'))


async def save_config(new_config):
    with open("config.ini", "w", encoding='utf-8') as config_file:
        new_config.write(config_file)


@dp.message_handler(commands=['start'])
async def start_menu(message: types.Message):
    if message.chat.type == types.ChatType.PRIVATE and message.from_user.id == int(admin_id):
        await message.answer('Виберіть дію: ', reply_markup=main_menu)
    else:
        await message.answer('Привіт')


@dp.message_handler(IsPrivate(), text='📃 Список', state="*")
async def list_words(message: types.Message, state: FSMContext):
    try:
        await state.finish()
        words = config.get("SETTING", "word").split('|')
        if words[0] == '':
            await message.answer('⛔ Список пустий')
            return
        txt = '📃 Список : \n\n'
        for word in words:
            txt += word + '\n'
        await message.answer(txt)
    except Exception as e:
        await message.answer(f'Відправте данний текст девелоперу: list_word\n {str(e)}')


@dp.message_handler(IsPrivate(), text='➕ Додати', state="*")
async def add_words(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Введіть нову фразу: \n<code>Кожна фраза з нового рядка</code>')
    await Form.form_add_words.set()


@dp.message_handler(IsPrivate(), text='➖ Видалити', state="*")
async def del_words(message: types.Message, state: FSMContext):
    try:
        await state.finish()
        words = config.get("SETTING", "word").split('|')
        if not words:
            await message.answer('⛔ Список')
            return
        await message.answer('Введіть номер слова для видалення, можна декілька.\n'
                             'Приклад: <code>\n1\n1 2 3 4</code>')
        txt = ''
        for en, word in enumerate(config.get("SETTING", "word").split('|')):
            txt += f"{en + 1}. {word}\n"
        await message.answer(txt)
        await Form.form_remove_words.set()
    except Exception as e:
        await message.answer(f'Відправте данний текст девелоперу: del_words\n {str(e)}')


@dp.message_handler(state=Form.form_remove_words)
async def remove_words(message: types.Message, state: FSMContext):
    try:
        numbers = message.text
        if not numbers.replace(' ', '').isdigit():
            await message.answer('⛔ Введіть тільки числа')
            return

        words = config.get("SETTING", "word").split('|')

        if len(words) < int(len(numbers.split(' '))):
            await message.answer(f'⛔ Максимальне число: {len(words)}')
            return

        await state.finish()
        x = [x for en, x in enumerate(words) if en + 1 not in [int(item) for item in numbers.split(' ')]]

        config.set("SETTING", "word", '|'.join(x))
        await save_config(config)
        await message.answer('✅ Фрази успішно видалені')
    except Exception as e:
        await message.answer(f'Відправте данний текст девелоперу: remove_words\n {str(e)}')


# Add new word
@dp.message_handler(state=Form.form_add_words)
async def add_words(message: types.Message, state: FSMContext):
    try:
        await state.finish()
        words = config.get("SETTING", "word")

        new_words = '|'.join(message.text.split('\n'))

        if words:
            config.set("SETTING", "word", f"{words}|{new_words}")
        else:
            config.set("SETTING", "word", new_words)
        await save_config(config)
        await message.answer('✅ Фраза успішно додана')
    except Exception as e:
        await message.answer(f'Відправте данний текст девелоперу: add_words\n {str(e)}')


############################################## Send ##############################################

async def send_msg():
    words = config.get("SETTING", "word").split('|')
    await bot.send_message(config.get("SETTING", "chat_id"), random.choice(words))


async def scheduler():
    aioschedule.every().day.at(config.get("SETTING", "time")).do(send_msg)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)

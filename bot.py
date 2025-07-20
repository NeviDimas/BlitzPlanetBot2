import os
import zipfile
import shutil
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from aiogram.utils import executor
from processor import run_inspector, run_redactor, run_calculator

API_TOKEN = "7803508934:AAHSH4CV5Q28Lo2kYAxlIzGQjMxHgxID9po"
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.reply("Привет! Пришли ZIP-архив с реплеями (.wotbreplay), и я пришлю таблицу.")

@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_zip(message: types.Message):
    file = message.document
    if not file.file_name.endswith(".zip"):
        await message.reply("Пожалуйста, отправь .zip архив.")
        return

    temp_dir = f"temp_{message.chat.id}"
    zip_path = os.path.join(temp_dir, "replays.zip")
    os.makedirs(temp_dir, exist_ok=True)

    await file.download(destination=zip_path)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(os.path.join(temp_dir, "replays"))

        run_inspector(
            replay_dir=os.path.join(temp_dir, "replays"),
            result_dir=os.path.join(temp_dir, "jsons"),
            exe_path="your_exe/wotbreplay-inspector.exe"
        )
        run_redactor(
            result_dir=os.path.join(temp_dir, "jsons"),
            excel_dir=os.path.join(temp_dir, "excel")
        )
        result = run_calculator(os.path.join(temp_dir, "excel"))

        await message.reply_document(FSInputFile(result))
    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

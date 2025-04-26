import os
import aiohttp
import subprocess
import shutil
import tempfile
import json
from datetime import datetime
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
from uuid import uuid4
from dotenv import load_dotenv
from frontend_bot.handlers.general import bot  # Импортируем объект бота
from frontend_bot.services.gpt_assistant import format_transcript_with_gpt
from frontend_bot.utils.logger import get_logger
from frontend_bot.keyboards.reply import (
    error_keyboard,
    transcript_format_keyboard,
    history_keyboard
)
from typing import Dict
from frontend_bot.services.file_utils import is_audio_file_ffmpeg, is_valid_text_transcript
from frontend_bot.services.state_manager import set_state, get_state, clear_state

logger = get_logger('transcribe')

# Загрузка переменных окружения из .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
TRANSCRIPTS_DIR = os.path.join(STORAGE_DIR, "transcripts")
os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

MAX_CHUNK_SIZE = 24 * 1024 * 1024  # 24 МБ

# Глобальный словарь user_id -> путь к файлу транскрипта
user_transcripts: Dict[int, str] = {}

HISTORY_FILE = os.path.join(STORAGE_DIR, 'history.json')

user_states = {}


def load_history() -> dict:
    if not os.path.exists(HISTORY_FILE):
        return {}
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_history(history: dict) -> None:
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def add_history_entry(user_id: str, file: str, file_type: str, result_type: str) -> None:
    history = load_history()
    entry = {
        'file': os.path.basename(file),
        'type': file_type,
        'result': result_type,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    if user_id not in history:
        history[user_id] = []
    history[user_id].append(entry)
    save_history(history)
    logger.info(
        f"History entry added for user {user_id}: {entry}"
    )


def get_user_history(user_id: str, limit: int = 5) -> list:
    history = load_history()
    return history.get(user_id, [])[-limit:]


def remove_last_history_entry(user_id: str) -> None:
    history = load_history()
    if user_id in history and history[user_id]:
        history[user_id].pop()
        save_history(history)
        logger.info(f"Last history entry removed for user {user_id}")


def protocol_error_keyboard() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Повторить генерацию протокола"))
    markup.add(KeyboardButton("Назад"))
    return markup


@bot.message_handler(func=lambda m: m.text == "Повторить")
async def repeat_audio_instruction(message: Message):
    await bot.send_message(
        message.chat.id,
        "Пожалуйста, отправьте аудиофайл или голосовое сообщение "
        "в этот чат ещё раз.",
        reply_markup=None
    )
    logger.info(
        f"User {message.from_user.id} requested to repeat audio upload."
    )


@bot.message_handler(func=lambda m: m.text == "Главное меню")
async def back_to_main_menu_from_anywhere(message: Message):
    from handlers.general import main_menu_keyboard
    await bot.send_message(
        message.chat.id,
        "Главное меню:",
        reply_markup=main_menu_keyboard()
    )
    logger.info(f"User {message.from_user.id} returned to main menu.")


@bot.message_handler(func=lambda m: m.text == "🎤 Аудио")
async def audio_instruction(message: Message):
    set_state(message.from_user.id, 'audio_transcribe')
    await bot.send_message(
        message.chat.id,
        "Пожалуйста, отправьте аудиофайл (mp3/ogg) для расшифровки."
    )


@bot.message_handler(func=lambda m: m.text == "📄 Текстовый транскрипт")
async def text_instruction(message: Message):
    set_state(message.from_user.id, 'transcribe_txt')
    await bot.send_message(
        message.chat.id,
        "Пожалуйста, отправьте .txt-файл с транскриптом для обработки."
    )


@bot.message_handler(content_types=['voice', 'audio'])
async def transcribe_audio(message: Message):
    if get_state(message.from_user.id) != 'audio_transcribe':
        return
    clear_state(message.from_user.id)
    await bot.send_chat_action(message.chat.id, 'typing')
    await bot.send_message(
        message.chat.id,
        "⏳ Файл получен! Начинаю обработку..."
    )

    file_id = message.voice.file_id if message.voice else message.audio.file_id
    ext = ".ogg" if message.voice else ".mp3"
    temp_file = os.path.join(STORAGE_DIR, f"{uuid4()}{ext}")

    file_info = await bot.get_file(file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    with open(temp_file, "wb") as f:
        f.write(downloaded_file)

    # Проверка, что файл действительно является аудиофайлом, поддерживаемым ffmpeg
    if not is_audio_file_ffmpeg(temp_file):
        await bot.send_message(
            message.chat.id,
            "Ваш файл не является поддерживаемой аудиозаписью. "
            "Пожалуйста, загрузите аудиофайл в одном из следующих форматов: "
            "mp3, wav, ogg, m4a, flac, aac, wma, opus."
        )
        os.remove(temp_file)
        return

    # Конвертируем в mp3 для Whisper
    temp_file_mp3 = temp_file.rsplit('.', 1)[0] + '.mp3'
    subprocess.run(["ffmpeg", "-y", "-i", temp_file, temp_file_mp3])

    file_size = os.path.getsize(temp_file_mp3)
    # Оценка времени ожидания (примерно 1 минута на 5 минут аудио)
    approx_minutes = max(1, int(file_size / (1024 * 1024 * 2)))
    progress_msg = await bot.send_message(
        message.chat.id,
        f"⏳ Обработка аудиофайла...\nОжидаемое время: ~{approx_minutes} мин."
    )

    user_id = message.from_user.id
    user_dir = os.path.join(TRANSCRIPTS_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    if file_size <= 25 * 1024 * 1024:
        try:
            await bot.edit_message_text(
                "📝 Расшифровка...",
                chat_id=message.chat.id,
                message_id=progress_msg.message_id
            )
            transcription = await whisper_transcribe(temp_file_mp3)
            transcript_path = os.path.join(user_dir, f"transcript_{uuid4()}.txt")
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(transcription)
            user_transcripts[user_id] = transcript_path
            await bot.send_message(
                message.chat.id,
                "Выберите формат вывода:",
                reply_markup=transcript_format_keyboard()
            )
            add_history_entry(
                str(user_id), transcript_path, 'audio', 'transcript'
            )
        except Exception:
            await bot.edit_message_text(
                "Что-то пошло не так. Попробуйте ещё раз или "
                "обратитесь в поддержку.",
                chat_id=message.chat.id,
                message_id=progress_msg.message_id,
                reply_markup=error_keyboard()
            )
        finally:
            os.remove(temp_file)
            os.remove(temp_file_mp3)
        return

    # Если файл большой — разбиваем по паузам через ffmpeg
    await bot.edit_message_text(
        "🔪 Нарезка аудио по паузам...",
        chat_id=message.chat.id,
        message_id=progress_msg.message_id
    )
    chunk_dir = os.path.join(STORAGE_DIR, f"chunks_{uuid4()}")
    os.makedirs(chunk_dir, exist_ok=True)
    chunk_paths = split_audio_by_silence_ffmpeg(temp_file, chunk_dir)
    os.remove(temp_file)
    os.remove(temp_file_mp3)

    await bot.edit_message_text(
        f"🔪 Нарезка завершена. Кусков: {len(chunk_paths)}.\n"
        "Начинаю расшифровку..."
    )

    transcribed_text = ""
    for i, part_path in enumerate(chunk_paths):
        # Конвертируем каждый кусок в mp3
        part_path_mp3 = part_path.rsplit('.', 1)[0] + '.mp3'
        subprocess.run(["ffmpeg", "-y", "-i", part_path, part_path_mp3])
        # Проверяем размер каждого куска
        if os.path.getsize(part_path_mp3) > 25 * 1024 * 1024:
            await bot.send_message(
                message.chat.id,
                f"❌ Кусок {i+1} слишком большой для обработки. "
                "Пропущен."
            )
            os.remove(part_path)
            os.remove(part_path_mp3)
            continue
        try:
            await bot.edit_message_text(
                f"⏳ Обработка куска {i+1}/{len(chunk_paths)}...",
                chat_id=message.chat.id,
                message_id=progress_msg.message_id
            )
            part_text = await whisper_transcribe(part_path_mp3)
            transcribed_text += f"\n--- Часть {i+1} ---\n{part_text}\n"
        except Exception:
            await bot.send_message(
                message.chat.id,
                "Что-то пошло не так. Попробуйте ещё раз или "
                "обратитесь в поддержку.",
                reply_markup=error_keyboard()
            )
            transcribed_text += (
                f"\n--- Часть {i+1} ---\nОшибка при расшифровке.\n"
            )
        finally:
            os.remove(part_path)
            os.remove(part_path_mp3)
    shutil.rmtree(chunk_dir, ignore_errors=True)
    await bot.edit_message_text(
        f"\u2705 Расшифровка завершена!\n\n"
        f"{transcribed_text[:1000]}...\n(текст обрезан)",
        chat_id=message.chat.id,
        message_id=progress_msg.message_id,
        reply_markup=transcript_format_keyboard()
    )
    transcript_path = os.path.join(user_dir, f"transcript_{uuid4()}.txt")
    with open(transcript_path, 'w', encoding='utf-8') as f:
        f.write(transcribed_text)
    user_transcripts[user_id] = transcript_path
    await bot.send_message(
        message.chat.id,
        f"\u2705 Итоговый транскрипт сохранён:"
        f"\n{transcript_path}"
    )
    add_history_entry(
        str(user_id), transcript_path, 'audio', 'transcript'
    )


def split_audio_by_silence_ffmpeg(
    input_path, output_dir, min_silence_len=0.7, silence_thresh=-30
):
    """
    Нарезает аудиофайл на части по паузам с помощью ffmpeg.
    min_silence_len — минимальная длина тишины (секунды)
    silence_thresh — уровень тишины в dB (относительно 0)
    """
    # 1. Получаем длительность файла
    duration = get_audio_duration(input_path)
    # 2. Запускаем ffmpeg для поиска пауз
    command = [
        "ffmpeg", "-i", input_path,
        "-af", f"silencedetect=noise={silence_thresh}dB:d={min_silence_len}",
        "-f", "null", "-"
    ]
    result = subprocess.run(command, stderr=subprocess.PIPE, text=True)
    silence_starts = []
    silence_ends = []
    for line in result.stderr.splitlines():
        if "silence_start" in line:
            silence_starts.append(float(line.split("silence_start: ")[-1]))
        if "silence_end" in line:
            silence_ends.append(
                float(line.split("silence_end: ")[-1].split(" |")[0])
            )
    # Формируем интервалы для нарезки
    segments = []
    prev_end = 0.0
    for start in silence_starts:
        segments.append((prev_end, start))
        prev_end = start
    # Добавляем последний кусок
    if prev_end < duration:
        segments.append((prev_end, duration))
    # Нарезаем аудио
    chunk_paths = []
    for i, (start, end) in enumerate(segments):
        out_path = os.path.join(output_dir, f"chunk_{i+1}.ogg")
        subprocess.run([
            "ffmpeg", "-y", "-i", input_path,
            "-ss", str(start), "-to", str(end),
            "-c", "copy", out_path
        ])
        chunk_paths.append(out_path)
    return chunk_paths


def get_audio_duration(path):
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", path
        ],
        stdout=subprocess.PIPE, text=True
    )
    return float(result.stdout.strip())


async def whisper_transcribe(audio_path: str) -> str:
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    
    async with aiohttp.ClientSession() as session:
        with open(audio_path, "rb") as f:
            form = aiohttp.FormData()
            form.add_field("file", f, filename=os.path.basename(audio_path))
            form.add_field("model", "whisper-1")
            async with session.post(url, data=form, headers=headers) as resp:
                resp.raise_for_status()
                response = await resp.json()
                return response["text"]


@bot.message_handler(func=lambda m: m.text == "Полный официальный транскрипт")
async def send_full_official_transcript(message: Message):
    user_id = message.from_user.id
    transcript_path = user_transcripts.get(user_id)
    if not transcript_path or not os.path.exists(transcript_path):
        await bot.send_message(
            message.chat.id,
            "Нет сохранённого транскрипта. Пожалуйста, отправьте аудиофайл "
            "ещё раз.",
            reply_markup=transcript_format_keyboard()
        )
        return
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = f.read()
    await bot.send_chat_action(message.chat.id, 'typing')
    await bot.send_message(
        message.chat.id,
        "🤖 Формирую полный официальный транскрипт с помощью GPT..."
    )

    try:
        full_prompt = (
            "Ты — профессиональный аналитик и бизнес-ассистент. "
            "На вход подаётся текст стенограммы рабочей встречи в "
            "неструктурированном виде (реплики участников идут сплошняком, "
            "без указания говорящего и без форматирования).\n"
            "Твоя задача:\n"
            "1. Выделить **участников встречи** и их роли (если указано).\n"
            "2. Сформировать **читабельный, логически разбитый транскрипт**, "
            "выделяя:\n"
            "   - Кто говорит (например, **Игорь:**).\n"
            "   - Темы обсуждения (блоками: 🔹 Архитектура, 🔹 Сроки, "
            "🔹 Организация работы и т.п.).\n"
            "3. Минимально редактировать речь: убрать повторы, «э-э», "
            "вводные слова, но не искажать смысл.\n"
            "4. Сохранить **хронологический порядок** и ключевые детали "
            "договорённостей.\n"
            "5. В финале — выделить **итоги встречи** и следующие шаги.\n"
            "Сохраняй деловой стиль, избегай художественности.\n\n"
            "Пример форматирования:\n---\n"
            "## 🗓 Название встречи  \n"
            "**Формат:** Онлайн  \n"
            "**Участники:**  \n"
            "– Иван (PM), – Ольга (Аналитик), – Сергей (Dev)\n\n"
            "### 🔹 Обсуждение архитектуры  \n"
            "**Ольга:** Обновили стек, теперь используем React и WebView...  \n"
            "**Сергей:** Нужно отдельный репозиторий, там уже есть наброски...\n\n"
            "### 🔹 Дальнейшие шаги  \n"
            "- Создать форк на Android  \n"
            "- Подготовить URL для WebView  \n---\n\n"
            "Начни с анализа участников, потом переходи к структурированной "
            "расшифровке. Входной текст ниже:"
        )

        formatted = await format_transcript_with_gpt(
            transcript,
            custom_prompt=full_prompt,
            temperature=0.2,
            top_p=0.7
        )

        with tempfile.NamedTemporaryFile(
            'w+', delete=False, suffix='.txt', encoding='utf-8'
        ) as f:
            f.write(formatted)
            temp_filename = f.name

        with open(temp_filename, 'rb') as f:
            await bot.send_document(
                message.chat.id,
                f,
                caption="📝 Полный официальный транскрипт",
                reply_markup=transcript_format_keyboard()
            )
        os.remove(temp_filename)

    except Exception:
        await bot.send_message(
            message.chat.id,
            "Что-то пошло не так. Попробуйте ещё раз или "
            "обратитесь в поддержку.",
            reply_markup=error_keyboard()
        )


@bot.message_handler(func=lambda m: m.text == "Сводка на 1 страницу")
async def send_short_summary(message: Message):
    user_id = message.from_user.id
    transcript_path = user_transcripts.get(user_id)
    if not transcript_path or not os.path.exists(transcript_path):
        await bot.send_message(
            message.chat.id,
            "Нет сохранённого транскрипта. Пожалуйста, отправьте аудиофайл "
            "ещё раз.",
            reply_markup=transcript_format_keyboard()
        )
        return
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = f.read()
    await bot.send_chat_action(message.chat.id, 'typing')
    await bot.send_message(
        message.chat.id,
        "🤖 Формирую сводку на 1 страницу с помощью GPT..."
    )
    try:
        summary_prompt = (
            "Ты — эксперт по обработке деловой расшифровки. "
            "Твоя задача — сделать краткую сводку встречи на 1 страницу для "
            "топ-менеджмента. Структурируй текст, выдели ключевые решения, "
            "задачи, сроки, ответственных. Будь лаконичен, избегай лишних "
            "деталей."
        )
        summary = await format_transcript_with_gpt(
            transcript,
            custom_prompt=summary_prompt,
            temperature=0.3,
            top_p=0.7
        )
        with tempfile.NamedTemporaryFile(
            'w+', delete=False, suffix='.txt', encoding='utf-8'
        ) as f:
            f.write(summary)
            temp_filename = f.name
        with open(temp_filename, 'rb') as f:
            await bot.send_document(
                message.chat.id,
                f,
                caption="📝 Сводка на 1 страницу",
                reply_markup=transcript_format_keyboard()
            )
        os.remove(temp_filename)
    except Exception:
        await bot.send_message(
            message.chat.id,
            "Что-то пошло не так. Попробуйте ещё раз или "
            "обратитесь в поддержку.",
            reply_markup=error_keyboard()
        )


@bot.message_handler(func=lambda m: m.text == "Сформировать MoM")
async def send_mom(message: Message):
    user_id = message.from_user.id
    transcript_path = user_transcripts.get(user_id)
    if not transcript_path or not os.path.exists(transcript_path):
        await bot.send_message(
            message.chat.id,
            "Нет сохранённого транскрипта. Пожалуйста, отправьте аудиофайл "
            "ещё раз.",
            reply_markup=transcript_format_keyboard()
        )
        return
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = f.read()
    await bot.send_chat_action(message.chat.id, 'typing')
    await bot.send_message(
        message.chat.id,
        "🤖 Формирую MoM (Minutes of Meeting) с помощью GPT..."
    )
    try:
        mom_prompt = (
            "Ты — ассистент, который составляет MoM (Minutes of Meeting) по "
            "деловой встрече. Выдели основные решения, задачи, ответственных, "
            "сроки и ключевые обсуждения. Структурируй результат по пунктам: "
            "Решения, Задачи, Ответственные, Сроки, Краткое содержание "
            "обсуждений. Оформи MoM лаконично и понятно для всех участников."
        )
        mom_text = await format_transcript_with_gpt(
            transcript,
            custom_prompt=mom_prompt,
            temperature=0.2,
            top_p=0.6
        )
        with tempfile.NamedTemporaryFile(
            'w+', delete=False, suffix='.txt', encoding='utf-8'
        ) as f:
            f.write(mom_text)
            temp_filename = f.name
        with open(temp_filename, 'rb') as f:
            await bot.send_document(
                message.chat.id,
                f,
                caption="📝 MoM (Minutes of Meeting)",
                reply_markup=transcript_format_keyboard()
            )
        os.remove(temp_filename)
    except Exception:
        await bot.send_message(
            message.chat.id,
            "Что-то пошло не так. Попробуйте ещё раз или "
            "обратитесь в поддержку.",
            reply_markup=error_keyboard()
        )


@bot.message_handler(func=lambda m: m.text == "Сформировать ToDo-план с чеклистами")
async def send_todo_checklist(message: Message):
    user_id = message.from_user.id
    transcript_path = user_transcripts.get(user_id)
    if not transcript_path or not os.path.exists(transcript_path):
        await bot.send_message(
            message.chat.id,
            "Нет сохранённого транскрипта. Пожалуйста, отправьте аудиофайл "
            "ещё раз.",
            reply_markup=transcript_format_keyboard()
        )
        return
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = f.read()
    await bot.send_chat_action(message.chat.id, 'typing')
    await bot.send_message(
        message.chat.id,
        "🤖 Формирую ToDo-план с чеклистами с помощью GPT..."
    )
    try:
        todo_prompt = (
            "Ты — ассистент, который составляет ToDo-план по результатам "
            "встречи. Выдели все задачи, которые обсуждались, и оформи их в "
            "виде чеклистов с ответственными и сроками. Структурируй результат "
            "по категориям, если это уместно. Используй формат чекбоксов "
            "(например, [ ] Задача). Будь креативен в формулировках, если "
            "задача неявно сформулирована."
        )
        todo_text = await format_transcript_with_gpt(
            transcript,
            custom_prompt=todo_prompt,
            temperature=0.5,
            top_p=0.9
        )
        with tempfile.NamedTemporaryFile(
            'w+', delete=False, suffix='.txt', encoding='utf-8'
        ) as f:
            f.write(todo_text)
            temp_filename = f.name
        with open(temp_filename, 'rb') as f:
            await bot.send_document(
                message.chat.id,
                f,
                caption="📝 ToDo-план с чеклистами",
                reply_markup=transcript_format_keyboard()
            )
        os.remove(temp_filename)
    except Exception:
        await bot.send_message(
            message.chat.id,
            "Что-то пошло не так. Попробуйте ещё раз или "
            "обратитесь в поддержку.",
            reply_markup=error_keyboard()
        )


@bot.message_handler(content_types=['document'])
async def handle_text_transcript_file(message: Message):
    if get_state(message.from_user.id) != 'transcribe_txt':
        return
    if not message.document or not message.document.file_name.endswith('.txt'):
        return
    clear_state(message.from_user.id)
    user_id = message.from_user.id
    user_dir = os.path.join(TRANSCRIPTS_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    file_info = await bot.get_file(message.document.file_id)
    file_path = os.path.join(user_dir, f"transcript_{uuid4()}.txt")
    downloaded_file = await bot.download_file(file_info.file_path)
    with open(file_path, "wb") as f:
        f.write(downloaded_file)
    user_transcripts[user_id] = file_path
    await bot.send_message(
        message.chat.id,
        "\u2705 Текстовый файл успешно загружен и сохранён как транскрипт.\n"
        "Выберите дальнейшее действие:",
        reply_markup=transcript_format_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "ℹ️ О форматах")
async def formats_info(message: Message):
    await bot.send_message(
        message.chat.id,
        "📚 Описание форматов:\n\n"
        "📝 Полный официальный транскрипт — структурированный текст встречи с "
        "выделением участников, тем и итогов.\n\n"
        "📄 Сводка на 1 страницу — краткое резюме для руководства.\n\n"
        "📋 MoM — протокол встречи с решениями и задачами.\n\n"
        "✅ ToDo-план — чеклист задач по итогам встречи.\n\n"
        "Выберите нужный формат ниже!",
        reply_markup=transcript_format_keyboard()
    )


@bot.message_handler(commands=['history'])
async def show_history(message: Message):
    user_id = message.from_user.id
    entries = get_user_history(str(user_id))
    if entries:
        msg = 'Последние файлы:\n'
        for e in reversed(entries):
            msg += (
                f"\n📄 {e['file']} | {e['type']} | {e['result']} | {e['date']}"
            )
        await bot.send_message(
            message.chat.id,
            msg,
            reply_markup=history_keyboard()
        )
    else:
        await bot.send_message(
            message.chat.id,
            "У вас нет обработанных файлов.",
            reply_markup=history_keyboard()
        )


@bot.message_handler(func=lambda m: m.text == "🗑 Удалить мой файл")
async def delete_my_file(message: Message):
    user_id = message.from_user.id
    transcript_path = user_transcripts.get(user_id)
    if transcript_path and os.path.exists(transcript_path):
        os.remove(transcript_path)
        user_transcripts.pop(user_id, None)
        remove_last_history_entry(str(user_id))
        await bot.send_message(
            message.chat.id,
            "Ваш последний файл удалён.",
            reply_markup=history_keyboard()
        )
    else:
        await bot.send_message(
            message.chat.id,
            "Нет файла для удаления.",
            reply_markup=history_keyboard()
        )


@bot.message_handler(func=lambda m: m.text == "Протокол заседания (Word)")
async def send_meeting_protocol(message: Message):
    user_id = message.from_user.id
    transcript_path = user_transcripts.get(user_id)
    if not transcript_path or not os.path.exists(transcript_path):
        await bot.send_message(
            message.chat.id,
            "Нет сохранённого транскрипта. Пожалуйста, отправьте аудиофайл "
            "или текстовый файл ещё раз.",
            reply_markup=transcript_format_keyboard()
        )
        return
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = f.read()
    await bot.send_chat_action(message.chat.id, 'typing')
    await bot.send_message(
        message.chat.id,
        "🤖 Формирую официальный протокол заседания (Word)..."
    )
    try:
        protocol_prompt = (
            "Ты — деловой помощник, создающий официальные документы. "
            "На вход подаётся текст неструктурированной стенограммы совещания. "
            "Твоя задача — составить официальный Протокол заседания рабочей "
            "группы в формате, принятом для муниципальных учреждений (как в "
            "образце).\n\n"
            "❗️Обязательные требования:\n"
            "1. Оформи документ в виде строгого протокола с пунктами, датой, "
            "составом группы и повесткой.\n"
            "2. Сохрани официальный стиль (как в документах учреждений: без "
            "личных местоимён, формулировки — 'Признать работу "
            "удовлетворительной', 'Голосовали: за – единогласно' и т.п.).\n"
            "3. Разделы:\n"
            "   - Название организации (можно оставить [Уточнить название])\n"
            "   - Название документа: 'Протокол заседания рабочей группы по ...'\n"
            "   - Дата\n"
            "   - Состав рабочей группы (председатель, секретарь, члены)\n"
            "   - Повестка дня\n"
            "   - Ход заседания (по пунктам)\n"
            "   - Решения и голосование\n"
            "   - Подписи\n\n"
            "📌 Пример структуры:\n"
            "Муниципальное бюджетное учреждение\n[Уточнить название]\n"
            "Протокол заседания рабочей группы по [уточнить тему]\n[Дата]\n\n"
            "Рабочая группа в составе:\n- Председатель — [ФИО]\n- Секретарь — [ФИО]\n"
            "- Члены: [перечислить]\n\n"
            "Повестка дня: [перечислить 1–2 пункта]\n\n"
            "Ход заседания:\n1. Обсудили...\n2. Принято решение...\n"
            "3. Голосование: 'За' – единогласно, 'Против' – нет, 'Воздержались' "
            "– нет\n\n"
            "Председатель: _______________\nСекретарь: _______________\n\n"
            "🔽 Ниже текст стенограммы встречи:\n"
        )
        # Получаем текст протокола через GPT
        protocol_text = await format_transcript_with_gpt(
            transcript,
            custom_prompt=protocol_prompt,
            temperature=0.2,
            top_p=0.7
        )
        # Генерируем Word-файл
        from docx import Document
        doc = Document()
        for line in protocol_text.split('\n'):
            doc.add_paragraph(line)
        with tempfile.NamedTemporaryFile(
            'wb', delete=False, suffix='.docx'
        ) as f:
            doc.save(f)
            temp_filename = f.name
        with open(temp_filename, 'rb') as f:
            await bot.send_document(
                message.chat.id,
                f,
                caption="📄 Протокол заседания (Word)",
                reply_markup=transcript_format_keyboard()
            )
        os.remove(temp_filename)
        add_history_entry(
            str(user_id), temp_filename, 'word', 'protocol'
        )
    except Exception:
        await bot.send_message(
            message.chat.id,
            "Что-то пошло не так при формировании протокола. "
            "Вы можете повторить попытку или выбрать другой формат.",
            reply_markup=protocol_error_keyboard()
        )


@bot.message_handler(func=lambda m: m.text == "Повторить генерацию протокола")
async def retry_meeting_protocol(message: Message):
    # Просто повторяем вызов генерации протокола
    await send_meeting_protocol(message)

import re
from typing import Optional
from openai import AsyncOpenAI
from frontend_bot.config import ASSISTANT_ID, OPENAI_API_KEY
import asyncio

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

def format_transcript_text(text: str) -> str:
    """
    Форматирует транскрибированный текст для лучшей читаемости:
    - Разделяет на абзацы
    - Выделяет реплики спикеров
    - Добавляет маркеры для новых спикеров
    - Преобразует перечисления в списки
    - Выделяет цитаты
    Возвращает Markdown-текст.
    """
    lines = text.split('\n')
    formatted = []
    last_speaker = None
    bullet_patterns = [
        r"^\s*\d+\. ",
        r"^\s*[-—•] ",
        r"^\s*\([a-zA-Zа-яА-Я]\) ",
        r"^\s*\* "
    ]
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        # Определяем спикера
        speaker_match = re.match(r"^([А-ЯЁA-Z][а-яёa-zA-Z]+):", line)
        if speaker_match:
            speaker = speaker_match.group(1)
            content = line[len(speaker)+1:].strip()
            if speaker != last_speaker:
                formatted.append(f"\n👤 **{speaker}:** {content}")
                last_speaker = speaker
            else:
                formatted.append(f"**{speaker}:** {content}")
            continue
        # Списки
        if any(re.match(pat, line) for pat in bullet_patterns):
            formatted.append(f"- {line}")
            continue
        # Цитаты (например, если строка начинается с '>' или содержит 'цитата:')
        if line.startswith('>') or 'цитата:' in line.lower():
            formatted.append(f"> {line}")
            continue
        # Длинные предложения — абзац
        if len(line) > 100:
            formatted.append(f"\n{line}\n")
        else:
            formatted.append(line)
    return '\n'.join(formatted)

async def format_transcript_with_gpt(
    transcript: str,
    ready_transcript: Optional[str] = None,
    custom_prompt: Optional[str] = None,
    temperature: float = 0.2,
    top_p: float = 0.8
) -> str:
    """
    Если передан ready_transcript — форматирует и возвращает его.
    Иначе — выполняет транскрибацию через OpenAI и форматирует результат.
    """
    if ready_transcript is not None:
        return format_transcript_text(ready_transcript)
    restriction = (
        "Внимание: Отвечай только по теме задачи. Если вопрос не по теме, отвечай: 'Я могу отвечать только по теме встречи/задачи.'"
    )
    if not custom_prompt:
        return "Ошибка: Не передан промпт для задачи."
    prompt = custom_prompt + '\n' + restriction
    thread = await client.beta.threads.create()
    thread_id = thread.id
    await client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=f"{prompt}\n\n{transcript}"
    )
    run = await client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID,
        temperature=temperature,
        top_p=top_p
    )
    while True:
        run_status = await client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        if run_status.status in [
            "completed",
            "failed",
            "cancelled",
            "expired"
        ]:
            break
        await asyncio.sleep(1)
    messages = await client.beta.threads.messages.list(thread_id=thread_id)
    for msg in reversed(messages.data):
        if msg.role == "assistant":
            raw_text = msg.content[0].text.value
            return format_transcript_text(raw_text)
    return "Ошибка: ассистент не вернул ответ."

# with open(
#     "test_transcript.txt", "r", encoding="utf-8"
# ) as f:
#     transcript_text = f.read()

# result = await format_transcript_with_gpt(
#     "", ready_transcript=transcript_text
# )
# print(result)

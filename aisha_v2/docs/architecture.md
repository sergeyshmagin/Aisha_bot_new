# Архитектура хранения транскриптов и форматов (v2)

## Основные принципы
- В БД хранятся только метаданные транскрипта:
  - transcript_id (UUID)
  - user_id
  - object_name (путь в MinIO, например, transcripts/{user_id}/{transcript_id}.txt)
  - created_at, updated_at
  - source, length, status и др.
- В MinIO хранятся сами файлы:
  - transcripts/{user_id}/{transcript_id}.txt — основной текст
  - transcripts/{user_id}/summary_{transcript_id}.txt — summary
  - transcripts/{user_id}/todo_{transcript_id}.txt — список задач
  - transcripts/{user_id}/protocol_{transcript_id}.txt — протокол

## Сценарии работы
1. После транскрибации аудио:
   - Сохраняем текст в MinIO
   - В БД сохраняем только метаданные и object_name
2. Для получения текста:
   - По transcript_id ищем object_name в БД
   - Через MinIO API скачиваем файл
3. Для форматов (summary, todo, protocol):
   - Загружаем основной текст из MinIO
   - Обрабатываем (ML/AI/алгоритм)
   - Сохраняем результат в MinIO (summary_{transcript_id}.txt и т.д.)
   - (Опционально) сохраняем ссылку на файл формата в БД

## Пример использования TranscriptService
```python
from aisha_v2.app.services.transcript.service import TranscriptService
from aisha_v2.app.services.storage.minio import MinioStorage
from aisha_v2.app.core.di import get_db_session

minio_storage = MinioStorage()
db_session = await get_db_session()
transcript_service = TranscriptService(minio_storage, db_session)

# Сохранить транскрипт
await transcript_service.save_transcript(
    user_id=message.from_user.id,
    transcript_id=transcript_id,
    text=transcript_text,
    source="audio",
    status="ready"
)

# Получить текст транскрипта
text = await transcript_service.get_transcript_text(transcript_id)

# Сохранить summary
await transcript_service.save_format(
    user_id=message.from_user.id,
    transcript_id=transcript_id,
    format_type="summary",
    text=summary_text
)

# Получить summary
summary = await transcript_service.get_format_text(
    user_id=message.from_user.id,
    transcript_id=transcript_id,
    format_type="summary"
)
```

## Схема работы с MinIO
1. Все большие тексты (транскрипты, summary, todo, protocol) хранятся только в MinIO.
2. В БД — только метаданные и object_name.
3. Для получения любого формата — сначала ищем object_name в БД, затем скачиваем файл из MinIO.

## LEGACY
- Все старые методы, где текст транскрипта хранился в БД, помечены как LEGACY и подлежат удалению после полной миграции на MinIO.

## Пример кода
```python
# Сохранение транскрипта
object_name = f"transcripts/{user_id}/{transcript_id}.txt"
await minio_storage.upload_file("your-bucket", object_name, transcript_text.encode("utf-8"))
await transcript_service.create_transcript(
    transcript_id=transcript_id,
    user_id=user_id,
    object_name=object_name,
    created_at=now,
    source="audio",
    length=len(transcript_text),
    status="ready"
)

# Получение текста
object_name = await transcript_service.get_object_name(transcript_id)
data = await minio_storage.download_file("your-bucket", object_name)
text = data.decode("utf-8")

# Сохранение формата
summary_object_name = f"transcripts/{user_id}/summary_{transcript_id}.txt"
await minio_storage.upload_file("your-bucket", summary_object_name, summary_text.encode("utf-8"))
```

## Best practices
- Не хранить большие тексты в БД — только в MinIO.
- Все операции с текстом транскрипта — через MinIO.
- Метаданные — только для поиска и отображения.
- Для всех форматов (summary, todo, protocol) — отдельные файлы в MinIO.
- Для пользователя — только красивые сообщения, .txt-файлы, кнопки. 
from app.services.storage.minio import MinioStorage
from app.core.di import get_db_session

class TranscriptService:
    def __init__(self, minio_storage: MinioStorage, db_session):
        self.minio = minio_storage
        self.db = db_session

    async def save_transcript(self, user_id: int, transcript_id: str, text: str, **meta):
        """
        Сохраняет текст транскрипта в MinIO и метаданные в БД.
        """
        object_name = f"transcripts/{user_id}/{transcript_id}.txt"
        await self.minio.upload_file("your-bucket", object_name, text.encode("utf-8"))
        await self.db.create_transcript(
            transcript_id=transcript_id,
            user_id=user_id,
            object_name=object_name,
            length=len(text),
            **meta
        )

    async def get_transcript_text(self, transcript_id: str) -> str:
        """
        Получает текст транскрипта из MinIO по object_name из БД.
        """
        object_name = await self.db.get_object_name(transcript_id)
        data = await self.minio.download_file("your-bucket", object_name)
        return data.decode("utf-8")

    async def save_format(self, user_id: int, transcript_id: str, format_type: str, text: str):
        """
        Сохраняет формат (summary, todo, protocol) в MinIO.
        """
        object_name = f"transcripts/{user_id}/{format_type}_{transcript_id}.txt"
        await self.minio.upload_file("your-bucket", object_name, text.encode("utf-8"))
        # (опционально) сохранить ссылку на формат в БД

    async def get_format_text(self, user_id: int, transcript_id: str, format_type: str) -> str:
        """
        Получает текст формата из MinIO.
        """
        object_name = f"transcripts/{user_id}/{format_type}_{transcript_id}.txt"
        data = await self.minio.download_file("your-bucket", object_name)
        return data.decode("utf-8") 
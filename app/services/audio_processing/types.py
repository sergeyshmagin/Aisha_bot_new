"""
Типы и интерфейсы для модуля обработки аудио
"""
from typing import List, Optional, Protocol, NamedTuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AudioMetadata:
    """Метаданные аудио файла"""
    duration: float
    format: str
    sample_rate: int
    channels: int
    bitrate: int
    created_at: datetime

class TranscribeResult(NamedTuple):
    """Результат транскрибации"""
    success: bool
    text: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[AudioMetadata] = None

class AudioConverter(Protocol):
    """Интерфейс для конвертации аудио"""
    async def convert_to_mp3(self, audio_data: bytes) -> bytes: ...
    async def detect_format(self, audio_data: bytes) -> str: ...
    async def get_metadata(self, audio_data: bytes) -> AudioMetadata: ...

class AudioRecognizer(Protocol):
    """Интерфейс для распознавания речи"""
    async def transcribe(self, audio_data: bytes, language: str) -> TranscribeResult: ...
    async def transcribe_chunk(self, audio_data: bytes, language: str) -> TranscribeResult: ...

class AudioProcessor(Protocol):
    """Интерфейс для обработки аудио"""
    async def split_audio(self, audio_data: bytes) -> List[bytes]: ...
    async def normalize_audio(self, audio_data: bytes) -> bytes: ...
    async def remove_silence(self, audio_data: bytes) -> bytes: ...

class AudioStorage(Protocol):
    """Интерфейс для хранения аудио"""
    async def save(self, audio_data: bytes, filename: str) -> str: ...
    async def load(self, filename: str) -> bytes: ...
    async def delete(self, filename: str) -> bool: ...

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from aiogram import Bot
from aiogram.types import Message, File

from app.services.audio_processing.service import AudioProcessingService
from app.services.storage.minio import MinioStorage

@pytest.fixture
def minio_storage():
    return AsyncMock(spec=MinioStorage)

@pytest.fixture
def audio_service(minio_storage):
    return AudioProcessingService(minio_storage=minio_storage)

@pytest.fixture
def bot():
    return AsyncMock(spec=Bot)

@pytest.mark.asyncio
async def test_save_audio_file(audio_service, minio_storage, bot):
    """Тест сохранения аудиофайла."""
    # Arrange
    file_id = "test_file_id"
    ext = ".ogg"
    bot.get_file.return_value = File(file_id="test", file_path="test/path")
    bot.download_file.return_value = b"test_audio_data"
    
    # Act
    result = await audio_service.save_audio_file(file_id, ext, bot)
    
    # Assert
    assert result.endswith(ext)
    assert os.path.exists(result)
    minio_storage.upload_file.assert_called_once()
    
    # Cleanup
    os.remove(result)

@pytest.mark.asyncio
async def test_convert_to_mp3(audio_service):
    """Тест конвертации в mp3."""
    # Arrange
    input_path = "test.ogg"
    with open(input_path, "wb") as f:
        f.write(b"test_audio_data")
    
    # Mock ffmpeg
    with patch("asyncio.create_subprocess_exec") as mock_subprocess:
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"")
        mock_proc.returncode = 0
        mock_subprocess.return_value = mock_proc
        
        # Act
        result = await audio_service.convert_to_mp3(input_path)
        
        # Assert
        assert result.endswith(".mp3")
        mock_subprocess.assert_called_once()
        
    # Cleanup
    os.remove(input_path)
    if os.path.exists(result):
        os.remove(result)

@pytest.mark.asyncio
async def test_split_by_silence(audio_service):
    """Тест разделения аудио на части по паузам."""
    # Arrange
    input_path = "test.mp3"
    with open(input_path, "wb") as f:
        f.write(b"test_audio_data")
    
    # Mock ffprobe and ffmpeg
    with patch("asyncio.create_subprocess_exec") as mock_subprocess:
        mock_proc = AsyncMock()
        mock_proc.communicate.side_effect = [
            (b"10.0", b""),  # ffprobe duration
            (b"", b"silence_start: 2.0\nsilence_end: 3.0\n"),  # ffmpeg silencedetect
            (b"", b"")  # ffmpeg chunk
        ]
        mock_proc.returncode = 0
        mock_subprocess.return_value = mock_proc
        
        # Act
        result = await audio_service.split_by_silence(input_path)
        
        # Assert
        assert len(result) > 0
        assert all(path.endswith(".mp3") for path in result)
        assert mock_subprocess.call_count == 3
        
    # Cleanup
    os.remove(input_path)
    for chunk in result:
        if os.path.exists(chunk):
            os.remove(chunk)

@pytest.mark.asyncio
async def test_recognize_audio(audio_service):
    """Тест распознавания аудио через Whisper API."""
    # Arrange
    audio_path = "test.mp3"
    with open(audio_path, "wb") as f:
        f.write(b"test_audio_data")
    
    # Mock aiohttp.ClientSession
    with patch("aiohttp.ClientSession") as mock_session:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json.return_value = {"text": "test transcript"}
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_resp
        
        # Act
        result = await audio_service.recognize_audio(audio_path)
        
        # Assert
        assert result == "test transcript"
        
    # Cleanup
    os.remove(audio_path)

@pytest.mark.asyncio
async def test_process_audio(audio_service, minio_storage, bot):
    """Тест полного процесса обработки аудио."""
    # Arrange
    message = MagicMock(spec=Message)
    message.voice = MagicMock(file_id="test_file_id")
    message.audio = None
    
    bot.get_file.return_value = File(file_id="test", file_path="test/path", file_size=1024)
    bot.download_file.return_value = b"test_audio_data"
    
    # Mock all subprocess calls
    with patch("asyncio.create_subprocess_exec") as mock_subprocess:
        mock_proc = AsyncMock()
        mock_proc.communicate.side_effect = [
            (b"10.0", b""),  # ffprobe duration
            (b"", b"silence_start: 2.0\nsilence_end: 3.0\n"),  # ffmpeg silencedetect
            (b"", b""),  # ffmpeg chunk
            (b"", b"")  # ffmpeg convert
        ]
        mock_proc.returncode = 0
        mock_subprocess.return_value = mock_proc
        
        # Mock aiohttp.ClientSession
        with patch("aiohttp.ClientSession") as mock_session:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json.return_value = {"text": "test transcript"}
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_resp
            
            # Act
            success, error, transcript_path = await audio_service.process_audio(
                message=message,
                bot=bot,
                user_id="test_user"
            )
            
            # Assert
            assert success
            assert not error
            assert transcript_path
            assert os.path.exists(transcript_path)
            
            # Cleanup
            if os.path.exists(transcript_path):
                os.remove(transcript_path)

@pytest.mark.asyncio
async def test_check_ffmpeg(audio_service):
    """Тест проверки наличия ffmpeg."""
    # Arrange
    with patch("asyncio.create_subprocess_exec") as mock_subprocess:
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"")
        mock_proc.returncode = 0
        mock_subprocess.return_value = mock_proc
        
        # Act
        result = await audio_service._check_ffmpeg()
        
        # Assert
        assert result
        mock_subprocess.assert_called_once_with(
            "ffmpeg",
            "-version",
            stdout=pytest.ANY,
            stderr=pytest.ANY
        )

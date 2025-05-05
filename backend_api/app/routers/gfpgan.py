"""
GFPGAN FastAPI router: обработка фото через docker-контейнер GFPGAN.
"""

import tempfile
import subprocess
from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import Response
import shutil
import os
import logging
from backend_api.app.config import (
    GFPGAN_DOCKER_IMAGE,
    GFPGAN_WEIGHTS_PATH,
    GFPGAN_DEFAULT_UPSCALE,
    GFPGAN_DEFAULT_ONLY_CENTER_FACE,
    GFPGAN_DEFAULT_EXT,
    GFPGAN_DEFAULT_AUTO,
    GFPGAN_SCRIPT_PATH,
)
from typing import Tuple
from PIL import Image
import cv2
import numpy as np

# Настройка логгера для отдельного файла
os.makedirs("logs", exist_ok=True)
gfpgan_log_path = os.path.join("logs", "gfpgan.log")
file_handler = logging.FileHandler(gfpgan_log_path, encoding="utf-8")
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
file_handler.setFormatter(formatter)
logger = logging.getLogger("gfpgan")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    logger.addHandler(file_handler)

router = APIRouter()

def detect_faces_opencv(image_path: str) -> int:
    try:
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        return len(faces)
    except Exception as e:
        logger.warning(f"Ошибка при определении лиц: {e}")
        return 0

def auto_gfpgan_params(image_path: str) -> Tuple[int, bool, str]:
    img = Image.open(image_path)
    width, height = img.size
    # Определяем upscale
    if width < 256 or height < 256:
        upscale = 4
    elif width < 512 or height < 512:
        upscale = 2
    else:
        upscale = 1
    # Определяем количество лиц
    n_faces = detect_faces_opencv(image_path)
    only_center_face = n_faces > 1
    # Формат результата
    ext = 'png' if image_path.lower().endswith('.png') else 'jpg'
    logger.info(f"Автоподбор: width={width}, height={height}, faces={n_faces}, "
                f"upscale={upscale}, only_center_face={only_center_face}, ext={ext}")
    return upscale, only_center_face, ext

@router.post("/gfpgan-enhance")
async def gfpgan_enhance(
    file: UploadFile = File(...),
    upscale: int = Query(GFPGAN_DEFAULT_UPSCALE, ge=1, le=4, description="Масштаб увеличения (1-4)"),
    only_center_face: bool = Query(GFPGAN_DEFAULT_ONLY_CENTER_FACE, description="Только центральное лицо"),
    ext: str = Query(GFPGAN_DEFAULT_EXT, regex="^(jpg|png)$", description="Формат результата: jpg или png"),
    auto: bool = Query(GFPGAN_DEFAULT_AUTO, description="Автоматический подбор параметров")
):
    """
    Принимает фото. Запускает docker-контейнер GFPGAN для улучшения.
    Поддерживает параметры: upscale, only_center_face, ext, auto.
    Возвращает улучшенное изображение.
    """
    try:
        logger.info(f"Получен файл: {file.filename}")
        logger.info(f"Параметры: upscale={upscale}, only_center_face={only_center_face}, ext={ext}, auto={auto}")
        with tempfile.TemporaryDirectory() as input_dir, \
                tempfile.TemporaryDirectory() as output_dir:
            input_path = os.path.join(input_dir, file.filename)
            with open(input_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            logger.info(f"Файл сохранён во временную папку: {input_path}")

            # Автоподбор параметров
            if auto:
                upscale, only_center_face, ext = auto_gfpgan_params(input_path)
                logger.info(f"Автоматически выбраны параметры: upscale={upscale}, only_center_face={only_center_face}, ext={ext}")

            command = [
                "docker", "run", "--rm",
                "-v", f"{GFPGAN_WEIGHTS_PATH}:/GFPGAN.pth",
                "-v", f"{input_dir}:/app/inputs",
                "-v", f"{output_dir}:/app/results",
                GFPGAN_DOCKER_IMAGE,
                "python3", GFPGAN_SCRIPT_PATH,
                "--upscale", str(upscale),
                "-i", "inputs",
                "-o", "results",
                "--ext", ext
            ]
            if only_center_face:
                command.append("--only_center_face")
            logger.info(
                "Запуск docker-команды: %s", ' '.join(command)
            )
            proc = subprocess.run(command, capture_output=True)
            if proc.returncode != 0:
                logger.error(
                    "Ошибка GFPGAN (docker): %s", proc.stderr.decode()
                )
                return Response(
                    content=f"Ошибка GFPGAN (docker): {proc.stderr.decode()}",
                    media_type="text/plain",
                    status_code=500
                )

            result_files = [
                f for f in os.listdir(output_dir)
                if f.endswith(f".{ext}")
            ]
            if not result_files:
                logger.error("Файл результата не найден в output_dir")
                return Response(
                    content=(
                        "Файл результата не найден. "
                        "Возможно, изображение не содержит лица или параметры некорректны."
                    ),
                    media_type="text/plain",
                    status_code=500
                )
            result_path = os.path.join(output_dir, result_files[0])
            logger.info(f"Результат найден: {result_path}")
            with open(result_path, "rb") as f:
                media_type = "image/jpeg" if ext == "jpg" else "image/png"
                return Response(content=f.read(), media_type=media_type)
    except Exception as e:
        logger.exception(f"Внутренняя ошибка обработки GFPGAN: {e}")
        return Response(
            content=(
                f"Внутренняя ошибка обработки GFPGAN: {e}. "
                "Проверьте параметры запроса и повторите попытку."
            ),
            media_type="text/plain",
            status_code=500
        ) 
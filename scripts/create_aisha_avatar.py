#!/usr/bin/env python3
"""
Скрипт для создания аватара Аиши
"""
import os
import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw, ImageFont
from app.core.static_resources import StaticResources

def create_aisha_avatar():
    """Создает простой аватар для Аиши"""
    
    # Размеры изображения
    width, height = 400, 400
    
    # Создаем новое изображение с градиентным фоном
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Создаем градиентный фон (от светло-голубого к фиолетовому)
    for y in range(height):
        ratio = y / height
        r = int(200 + (150 - 200) * ratio)  # от 200 до 150
        g = int(220 + (100 - 220) * ratio)  # от 220 до 100  
        b = int(255 + (200 - 255) * ratio)  # от 255 до 200
        draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))
    
    # Рисуем круг для лица
    face_radius = 120
    face_center = (width // 2, height // 2 - 30)
    
    # Лицо (светло-персиковый цвет)
    draw.ellipse([
        face_center[0] - face_radius,
        face_center[1] - face_radius,
        face_center[0] + face_radius,
        face_center[1] + face_radius
    ], fill=(255, 220, 200))
    
    # Глаза
    eye_y = face_center[1] - 30
    left_eye = (face_center[0] - 35, eye_y)
    right_eye = (face_center[0] + 35, eye_y)
    
    # Белки глаз
    draw.ellipse([left_eye[0] - 15, left_eye[1] - 10, left_eye[0] + 15, left_eye[1] + 10], fill='white')
    draw.ellipse([right_eye[0] - 15, right_eye[1] - 10, right_eye[0] + 15, right_eye[1] + 10], fill='white')
    
    # Зрачки
    draw.ellipse([left_eye[0] - 8, left_eye[1] - 6, left_eye[0] + 8, left_eye[1] + 6], fill='black')
    draw.ellipse([right_eye[0] - 8, right_eye[1] - 6, right_eye[0] + 8, right_eye[1] + 6], fill='black')
    
    # Блики в глазах
    draw.ellipse([left_eye[0] - 3, left_eye[1] - 3, left_eye[0] + 3, left_eye[1] + 3], fill='white')
    draw.ellipse([right_eye[0] - 3, right_eye[1] - 3, right_eye[0] + 3, right_eye[1] + 3], fill='white')
    
    # Нос (маленький треугольник)
    nose_points = [
        (face_center[0], face_center[1] - 5),
        (face_center[0] - 5, face_center[1] + 5),
        (face_center[0] + 5, face_center[1] + 5)
    ]
    draw.polygon(nose_points, fill=(255, 200, 180))
    
    # Рот (улыбка)
    draw.arc([
        face_center[0] - 30, face_center[1] + 10,
        face_center[0] + 30, face_center[1] + 40
    ], start=0, end=180, fill=(255, 100, 100), width=3)
    
    # Волосы (темно-коричневые)
    hair_points = [
        (face_center[0] - face_radius + 10, face_center[1] - face_radius + 10),
        (face_center[0] - face_radius - 20, face_center[1] - face_radius - 30),
        (face_center[0], face_center[1] - face_radius - 40),
        (face_center[0] + face_radius + 20, face_center[1] - face_radius - 30),
        (face_center[0] + face_radius - 10, face_center[1] - face_radius + 10),
    ]
    draw.polygon(hair_points, fill=(101, 67, 33))
    
    # Добавляем текст "AI" в нижней части
    try:
        # Пытаемся использовать системный шрифт
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except:
        try:
            # Альтернативный шрифт для Windows
            font = ImageFont.truetype("arial.ttf", 48)
        except:
            # Если шрифт не найден, используем стандартный
            font = ImageFont.load_default()
    
    text = "AI"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    text_x = (width - text_width) // 2
    text_y = height - 80
    
    # Тень для текста
    draw.text((text_x + 2, text_y + 2), text, font=font, fill=(0, 0, 0, 128))
    # Основной текст
    draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))
    
    # Сохраняем изображение
    avatar_path = StaticResources.get_aisha_avatar_path()
    image.save(avatar_path, 'JPEG', quality=95)
    print(f"✅ Аватар Аиши создан: {avatar_path}")
    
    return avatar_path

if __name__ == "__main__":
    try:
        create_aisha_avatar()
    except Exception as e:
        print(f"❌ Ошибка создания аватара: {e}")
        sys.exit(1) 
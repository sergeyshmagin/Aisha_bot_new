"""
Модуль форматирования карточек изображений
Быстрое и безопасное форматирование текста
"""
from typing import List, Optional
from datetime import datetime

from app.database.models import ImageGeneration
from app.core.logger import get_logger


class CardFormatter:
    """Форматирование карточек изображений"""
    
    @staticmethod
    def format_image_card_text_fast(
        generation: ImageGeneration, 
        img_idx: int, 
        total_images: int
    ) -> str:
        """Быстрое форматирование текста карточки"""
        
        # Безопасное название аватара
        avatar_name = generation.avatar.name if generation.avatar and generation.avatar.name else "Неизвестно"
        
        # Статус избранного
        favorite_status = "❤️ В избранном" if getattr(generation, 'is_favorite', False) else ""
        
        # Размер
        aspect_ratio = getattr(generation, 'aspect_ratio', '1:1')
        
        # Быстрая сборка текста
        text_parts = [
            f"🖼️ *Изображение {img_idx + 1} из {total_images}*",
            "",
            f"🎭 *Аватар:* {avatar_name}",
            f"📐 *Размер:* {aspect_ratio}"
        ]
        
        if favorite_status:
            text_parts.append("")
            text_parts.append(favorite_status)
        
        return "\n".join(text_parts)
    
    @staticmethod
    def format_image_card_text_detailed(
        generation: ImageGeneration, 
        img_idx: int, 
        total_images: int
    ) -> str:
        """Детальное форматирование текста карточки (как в оригинальном коде)"""
        
        # Безопасное название аватара (БЕЗ экранирования)
        avatar_name = generation.avatar.name if generation.avatar and generation.avatar.name else "Неизвестно"
        
        # Статус избранного
        favorite_status = "❤️ В избранном" if getattr(generation, 'is_favorite', False) else ""
        
        # Размер (безопасно)
        aspect_ratio = getattr(generation, 'aspect_ratio', '1:1')
        
        # Формируем упрощенную карточку БЕЗ промпта (есть кнопка "Промпт")
        text_parts = [
            f"🖼️ *Изображение {img_idx + 1} из {total_images}*",
            "",
            f"🎭 *Аватар:* {avatar_name}",
            f"📐 *Размер:* {aspect_ratio}"
        ]
        
        # Добавляем статус избранного если есть
        if favorite_status:
            text_parts.append("")
            text_parts.append(favorite_status)
        
        return "\n".join(text_parts) 
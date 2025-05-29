"""
Скрипт для инициализации базовых данных системы генерации изображений
"""
import asyncio
import sys
import os

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_session
from app.database.models.generation import StyleCategory, StyleSubcategory, StyleTemplate
from app.core.logger import get_logger

logger = get_logger(__name__)


async def init_generation_data():
    """Инициализирует базовые данные для системы генерации"""
    
    try:
        async with get_session() as session:
            logger.info("Начинаем инициализацию данных генерации...")
            
            # 1. Деловой стиль
            business_category = StyleCategory(
                id="business",
                name="👔 Деловой стиль",
                icon="👔",
                description="Профессиональные образы для работы и карьеры",
                sort_order=1
            )
            session.add(business_category)
            
            # Подкатегории делового стиля
            office_subcategory = StyleSubcategory(
                id="office",
                category_id="business",
                name="🏢 Офисные образы",
                sort_order=1
            )
            session.add(office_subcategory)
            
            dresscode_subcategory = StyleSubcategory(
                id="dresscode",
                category_id="business",
                name="👗 Дресс-код",
                sort_order=2
            )
            session.add(dresscode_subcategory)
            
            # Шаблоны офисных образов
            templates_office = [
                StyleTemplate(
                    id="presentation",
                    subcategory_id="office",
                    name="📊 Презентация",
                    prompt="professional presentation, business attire, confident pose, office background, studio lighting",
                    tags=["презентация", "офис", "деловой", "уверенность"],
                    popularity=95,
                    sort_order=1
                ),
                StyleTemplate(
                    id="negotiation",
                    subcategory_id="office",
                    name="💼 Переговоры",
                    prompt="business meeting, professional attire, handshake, conference room, natural lighting",
                    tags=["переговоры", "встреча", "деловой", "рукопожатие"],
                    popularity=87,
                    sort_order=2
                ),
                StyleTemplate(
                    id="success",
                    subcategory_id="office",
                    name="📈 Успех",
                    prompt="successful business person, achievement pose, modern office, professional lighting",
                    tags=["успех", "достижение", "карьера", "офис"],
                    popularity=82,
                    sort_order=3
                )
            ]
            
            # Шаблоны дресс-кода
            templates_dresscode = [
                StyleTemplate(
                    id="formal",
                    subcategory_id="dresscode",
                    name="👔 Строгий",
                    prompt="formal business attire, suit, professional headshot, corporate style",
                    tags=["строгий", "костюм", "корпоративный", "формальный"],
                    popularity=92,
                    sort_order=1
                ),
                StyleTemplate(
                    id="elegant",
                    subcategory_id="dresscode",
                    name="👗 Элегантный",
                    prompt="elegant business attire, sophisticated style, professional portrait",
                    tags=["элегантный", "изысканный", "стильный", "профессиональный"],
                    popularity=78,
                    sort_order=2
                ),
                StyleTemplate(
                    id="business_casual",
                    subcategory_id="dresscode",
                    name="🧥 Business Casual",
                    prompt="business casual attire, smart casual, relaxed professional style",
                    tags=["casual", "непринужденный", "умный", "стиль"],
                    popularity=74,
                    sort_order=3
                )
            ]
            
            for template in templates_office + templates_dresscode:
                session.add(template)
            
            # 2. Праздники
            celebration_category = StyleCategory(
                id="celebration",
                name="🎉 Праздники",
                icon="🎉",
                description="Праздничные и торжественные образы",
                sort_order=2
            )
            session.add(celebration_category)
            
            # Подкатегории праздников
            new_year_subcategory = StyleSubcategory(
                id="new_year",
                category_id="celebration",
                name="🎄 Новый год",
                sort_order=1
            )
            session.add(new_year_subcategory)
            
            birthday_subcategory = StyleSubcategory(
                id="birthday",
                category_id="celebration",
                name="🎂 День рождения",
                sort_order=2
            )
            session.add(birthday_subcategory)
            
            # Шаблоны праздников
            templates_celebration = [
                StyleTemplate(
                    id="new_year_party",
                    subcategory_id="new_year",
                    name="🥂 Новогодняя вечеринка",
                    prompt="new year celebration, festive attire, party atmosphere, champagne, elegant lighting",
                    tags=["новый год", "вечеринка", "праздник", "шампанское"],
                    popularity=89,
                    sort_order=1
                ),
                StyleTemplate(
                    id="winter_magic",
                    subcategory_id="new_year",
                    name="❄️ Зимняя магия",
                    prompt="winter wonderland, snow, magical atmosphere, festive mood, cozy lighting",
                    tags=["зима", "снег", "магия", "уют"],
                    popularity=76,
                    sort_order=2
                ),
                StyleTemplate(
                    id="birthday_celebration",
                    subcategory_id="birthday",
                    name="🎈 Празднование",
                    prompt="birthday celebration, festive mood, cake, balloons, joyful expression",
                    tags=["день рождения", "торт", "праздник", "радость"],
                    popularity=76,
                    sort_order=1
                )
            ]
            
            for template in templates_celebration:
                session.add(template)
            
            # 3. Городской стиль
            urban_category = StyleCategory(
                id="urban",
                name="🏙️ Городской стиль",
                icon="🏙️",
                description="Современные городские образы",
                sort_order=3
            )
            session.add(urban_category)
            
            # Подкатегории городского стиля
            street_subcategory = StyleSubcategory(
                id="street",
                category_id="urban",
                name="🚶 Уличный стиль",
                sort_order=1
            )
            session.add(street_subcategory)
            
            cafe_subcategory = StyleSubcategory(
                id="cafe",
                category_id="urban",
                name="☕ В кафе",
                sort_order=2
            )
            session.add(cafe_subcategory)
            
            # Шаблоны городского стиля
            templates_urban = [
                StyleTemplate(
                    id="street_fashion",
                    subcategory_id="street",
                    name="👟 Стрит-фэшн",
                    prompt="street fashion, urban style, casual wear, city background, natural lighting",
                    tags=["уличный", "мода", "город", "casual"],
                    popularity=84,
                    sort_order=1
                ),
                StyleTemplate(
                    id="city_walk",
                    subcategory_id="street",
                    name="🌆 Прогулка по городу",
                    prompt="city walk, urban exploration, modern architecture, street photography style",
                    tags=["город", "прогулка", "архитектура", "улица"],
                    popularity=71,
                    sort_order=2
                ),
                StyleTemplate(
                    id="coffee_shop",
                    subcategory_id="cafe",
                    name="☕ Кофейня",
                    prompt="coffee shop atmosphere, casual attire, cozy interior, warm lighting",
                    tags=["кафе", "кофе", "уютно", "атмосфера"],
                    popularity=78,
                    sort_order=1
                ),
                StyleTemplate(
                    id="morning_coffee",
                    subcategory_id="cafe",
                    name="🌅 Утренний кофе",
                    prompt="morning coffee, breakfast time, natural light, relaxed mood",
                    tags=["утро", "кофе", "завтрак", "расслабленность"],
                    popularity=65,
                    sort_order=2
                )
            ]
            
            for template in templates_urban:
                session.add(template)
            
            # 4. Творчество
            creative_category = StyleCategory(
                id="creative",
                name="🎨 Творчество",
                icon="🎨",
                description="Художественные и творческие образы",
                sort_order=4
            )
            session.add(creative_category)
            
            # Подкатегории творчества
            art_subcategory = StyleSubcategory(
                id="art",
                category_id="creative",
                name="🖼️ Искусство",
                sort_order=1
            )
            session.add(art_subcategory)
            
            music_subcategory = StyleSubcategory(
                id="music",
                category_id="creative",
                name="🎵 Музыка",
                sort_order=2
            )
            session.add(music_subcategory)
            
            # Шаблоны творчества
            templates_creative = [
                StyleTemplate(
                    id="artist_studio",
                    subcategory_id="art",
                    name="🎨 Художник в студии",
                    prompt="artist in studio, creative workspace, paintbrush, artistic atmosphere",
                    tags=["художник", "студия", "творчество", "искусство"],
                    popularity=73,
                    sort_order=1
                ),
                StyleTemplate(
                    id="gallery_opening",
                    subcategory_id="art",
                    name="🖼️ Открытие галереи",
                    prompt="art gallery opening, sophisticated attire, cultural event, elegant atmosphere",
                    tags=["галерея", "культура", "событие", "элегантность"],
                    popularity=68,
                    sort_order=2
                ),
                StyleTemplate(
                    id="musician_portrait",
                    subcategory_id="music",
                    name="🎸 Портрет музыканта",
                    prompt="musician portrait, instrument, creative lighting, artistic mood",
                    tags=["музыкант", "инструмент", "портрет", "творчество"],
                    popularity=70,
                    sort_order=1
                ),
                StyleTemplate(
                    id="concert_backstage",
                    subcategory_id="music",
                    name="🎤 За кулисами",
                    prompt="backstage atmosphere, concert preparation, artistic lighting, music venue",
                    tags=["концерт", "кулисы", "музыка", "атмосфера"],
                    popularity=64,
                    sort_order=2
                )
            ]
            
            for template in templates_creative:
                session.add(template)
            
            # Сохраняем все изменения
            await session.commit()
            
            logger.info("✅ Данные генерации успешно инициализированы!")
            logger.info("Создано:")
            logger.info("- 4 категории стилей")
            logger.info("- 8 подкатегорий")
            logger.info("- 13 шаблонов")
            
    except Exception as e:
        logger.exception(f"Ошибка инициализации данных генерации: {e}")
        raise


async def check_existing_data():
    """Проверяет существующие данные"""
    
    try:
        async with get_session() as session:
            from sqlalchemy import select
            
            # Проверяем категории
            stmt = select(StyleCategory)
            result = await session.execute(stmt)
            categories = result.scalars().all()
            
            if categories:
                logger.info(f"Найдено {len(categories)} существующих категорий:")
                for cat in categories:
                    logger.info(f"  - {cat.name} ({cat.id})")
                
                response = input("Данные уже существуют. Перезаписать? (y/N): ")
                if response.lower() != 'y':
                    logger.info("Инициализация отменена")
                    return False
                
                # Удаляем существующие данные
                logger.info("Удаляем существующие данные...")
                for cat in categories:
                    await session.delete(cat)
                await session.commit()
                logger.info("Существующие данные удалены")
            
            return True
            
    except Exception as e:
        logger.exception(f"Ошибка проверки существующих данных: {e}")
        return False


async def main():
    """Главная функция"""
    
    logger.info("🚀 Инициализация данных системы генерации изображений")
    
    # Проверяем существующие данные
    if not await check_existing_data():
        return
    
    # Инициализируем новые данные
    await init_generation_data()
    
    logger.info("🎉 Инициализация завершена успешно!")


if __name__ == "__main__":
    asyncio.run(main()) 
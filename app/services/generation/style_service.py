"""
Сервис для работы со стилями и шаблонами генерации изображений
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.core.logger import get_logger
from app.database.models.generation import (
    StyleCategory, StyleSubcategory, StyleTemplate, UserFavoriteTemplate
)

logger = get_logger(__name__)class StyleService:
    """Сервис для работы со стилями и шаблонами"""
    
    async def get_popular_categories(self, limit: int = 4) -> List[StyleCategory]:
        """
        Получает популярные категории стилей
        
        Args:
            limit: Максимальное количество категорий
            
        Returns:
            List[StyleCategory]: Список популярных категорий
        """
        try:
            async with get_session() as session:
                # Получаем категории с подкатегориями и шаблонами
                stmt = (
                    select(StyleCategory)
                    .options(
                        selectinload(StyleCategory.subcategories)
                        .selectinload(StyleSubcategory.templates)
                    )
                    .where(StyleCategory.is_active == True)
                    .order_by(StyleCategory.sort_order, StyleCategory.name)
                    .limit(limit)
                )
                
                result = await session.execute(stmt)
                categories = result.scalars().all()
                
                logger.info(f"Получено {len(categories)} популярных категорий")
                return list(categories)
                
        except Exception as e:
            logger.exception(f"Ошибка получения популярных категорий: {e}")
            return []
    
    async def get_all_categories(self) -> List[StyleCategory]:
        """
        Получает все активные категории стилей
        
        Returns:
            List[StyleCategory]: Список всех категорий
        """
        try:
            async with get_session() as session:
                stmt = (
                    select(StyleCategory)
                    .options(
                        selectinload(StyleCategory.subcategories)
                        .selectinload(StyleSubcategory.templates)
                    )
                    .where(StyleCategory.is_active == True)
                    .order_by(StyleCategory.sort_order, StyleCategory.name)
                )
                
                result = await session.execute(stmt)
                categories = result.scalars().all()
                
                logger.info(f"Получено {len(categories)} категорий")
                return list(categories)
                
        except Exception as e:
            logger.exception(f"Ошибка получения всех категорий: {e}")
            return []
    
    async def get_category_with_templates(self, category_id: str) -> Optional[StyleCategory]:
        """
        Получает категорию с шаблонами
        
        Args:
            category_id: ID категории
            
        Returns:
            Optional[StyleCategory]: Категория с шаблонами или None
        """
        try:
            async with get_session() as session:
                stmt = (
                    select(StyleCategory)
                    .options(
                        selectinload(StyleCategory.subcategories)
                        .selectinload(StyleSubcategory.templates)
                    )
                    .where(
                        and_(
                            StyleCategory.id == category_id,
                            StyleCategory.is_active == True
                        )
                    )
                )
                
                result = await session.execute(stmt)
                category = result.scalar_one_or_none()
                
                if category:
                    logger.info(f"Получена категория {category_id} с {len(category.subcategories)} подкатегориями")
                else:
                    logger.warning(f"Категория {category_id} не найдена")
                
                return category
                
        except Exception as e:
            logger.exception(f"Ошибка получения категории {category_id}: {e}")
            return None
    
    async def get_template_by_id(self, template_id: str) -> Optional[StyleTemplate]:
        """
        Получает шаблон по ID
        
        Args:
            template_id: ID шаблона
            
        Returns:
            Optional[StyleTemplate]: Шаблон или None
        """
        try:
            async with get_session() as session:
                stmt = (
                    select(StyleTemplate)
                    .options(selectinload(StyleTemplate.subcategory))
                    .where(
                        and_(
                            StyleTemplate.id == template_id,
                            StyleTemplate.is_active == True
                        )
                    )
                )
                
                result = await session.execute(stmt)
                template = result.scalar_one_or_none()
                
                if template:
                    logger.info(f"Получен шаблон {template_id}: {template.name}")
                else:
                    logger.warning(f"Шаблон {template_id} не найден")
                
                return template
                
        except Exception as e:
            logger.exception(f"Ошибка получения шаблона {template_id}: {e}")
            return None
    
    async def search_templates(self, query: str, limit: int = 10) -> List[StyleTemplate]:
        """
        Поиск шаблонов по названию и тегам
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            
        Returns:
            List[StyleTemplate]: Список найденных шаблонов
        """
        try:
            async with get_session() as session:
                # Поиск по названию и тегам
                search_term = f"%{query.lower()}%"
                
                stmt = (
                    select(StyleTemplate)
                    .options(selectinload(StyleTemplate.subcategory))
                    .where(
                        and_(
                            StyleTemplate.is_active == True,
                            func.lower(StyleTemplate.name).like(search_term)
                        )
                    )
                    .order_by(StyleTemplate.popularity.desc(), StyleTemplate.name)
                    .limit(limit)
                )
                
                result = await session.execute(stmt)
                templates = result.scalars().all()
                
                logger.info(f"Найдено {len(templates)} шаблонов по запросу '{query}'")
                return list(templates)
                
        except Exception as e:
            logger.exception(f"Ошибка поиска шаблонов по запросу '{query}': {e}")
            return []
    
    async def get_user_favorites(self, user_id: UUID) -> List[StyleTemplate]:
        """
        Получает избранные шаблоны пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[StyleTemplate]: Список избранных шаблонов
        """
        try:
            async with get_session() as session:
                stmt = (
                    select(StyleTemplate)
                    .join(UserFavoriteTemplate)
                    .options(selectinload(StyleTemplate.subcategory))
                    .where(
                        and_(
                            UserFavoriteTemplate.user_id == user_id,
                            StyleTemplate.is_active == True
                        )
                    )
                    .order_by(UserFavoriteTemplate.created_at.desc())
                )
                
                result = await session.execute(stmt)
                templates = result.scalars().all()
                
                logger.info(f"Получено {len(templates)} избранных шаблонов для пользователя {user_id}")
                return list(templates)
                
        except Exception as e:
            logger.exception(f"Ошибка получения избранных шаблонов для пользователя {user_id}: {e}")
            return []
    
    async def add_to_favorites(self, user_id: UUID, template_id: str) -> bool:
        """
        Добавляет шаблон в избранное
        
        Args:
            user_id: ID пользователя
            template_id: ID шаблона
            
        Returns:
            bool: True если успешно добавлено
        """
        try:
            async with get_session() as session:
                # Проверяем, что шаблон еще не в избранном
                existing_stmt = select(UserFavoriteTemplate).where(
                    and_(
                        UserFavoriteTemplate.user_id == user_id,
                        UserFavoriteTemplate.template_id == template_id
                    )
                )
                
                existing_result = await session.execute(existing_stmt)
                if existing_result.scalar_one_or_none():
                    logger.info(f"Шаблон {template_id} уже в избранном у пользователя {user_id}")
                    return True
                
                # Добавляем в избранное
                favorite = UserFavoriteTemplate(
                    user_id=user_id,
                    template_id=template_id
                )
                
                session.add(favorite)
                await session.commit()
                
                logger.info(f"Шаблон {template_id} добавлен в избранное пользователя {user_id}")
                return True
                
        except Exception as e:
            logger.exception(f"Ошибка добавления шаблона {template_id} в избранное пользователя {user_id}: {e}")
            return False
    
    async def remove_from_favorites(self, user_id: UUID, template_id: str) -> bool:
        """
        Удаляет шаблон из избранного
        
        Args:
            user_id: ID пользователя
            template_id: ID шаблона
            
        Returns:
            bool: True если успешно удалено
        """
        try:
            async with get_session() as session:
                stmt = select(UserFavoriteTemplate).where(
                    and_(
                        UserFavoriteTemplate.user_id == user_id,
                        UserFavoriteTemplate.template_id == template_id
                    )
                )
                
                result = await session.execute(stmt)
                favorite = result.scalar_one_or_none()
                
                if favorite:
                    await session.delete(favorite)
                    await session.commit()
                    logger.info(f"Шаблон {template_id} удален из избранного пользователя {user_id}")
                    return True
                else:
                    logger.warning(f"Шаблон {template_id} не найден в избранном пользователя {user_id}")
                    return False
                
        except Exception as e:
            logger.exception(f"Ошибка удаления шаблона {template_id} из избранного пользователя {user_id}: {e}")
            return False
    
    async def is_template_favorite(self, user_id: UUID, template_id: str) -> bool:
        """
        Проверяет, находится ли шаблон в избранном у пользователя
        
        Args:
            user_id: ID пользователя
            template_id: ID шаблона
            
        Returns:
            bool: True если шаблон в избранном
        """
        try:
            async with get_session() as session:
                stmt = select(UserFavoriteTemplate).where(
                    and_(
                        UserFavoriteTemplate.user_id == user_id,
                        UserFavoriteTemplate.template_id == template_id
                    )
                )
                
                result = await session.execute(stmt)
                favorite = result.scalar_one_or_none()
                
                return favorite is not None
                
        except Exception as e:
            logger.exception(f"Ошибка проверки избранного шаблона {template_id} для пользователя {user_id}: {e}")
            return False
    
    async def increment_template_popularity(self, template_id: str) -> bool:
        """
        Увеличивает популярность шаблона
        
        Args:
            template_id: ID шаблона
            
        Returns:
            bool: True если успешно обновлено
        """
        try:
            async with get_session() as session:
                stmt = select(StyleTemplate).where(StyleTemplate.id == template_id)
                result = await session.execute(stmt)
                template = result.scalar_one_or_none()
                
                if template:
                    template.popularity += 1
                    await session.commit()
                    logger.info(f"Популярность шаблона {template_id} увеличена до {template.popularity}")
                    return True
                else:
                    logger.warning(f"Шаблон {template_id} не найден для увеличения популярности")
                    return False
                
        except Exception as e:
            logger.exception(f"Ошибка увеличения популярности шаблона {template_id}: {e}")
            return False

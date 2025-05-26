"""
Модуль обработчиков аватаров
"""
from .training_type_selection import router as training_type_router
from .create import router as create_router
from .main import router as main_router, avatar_main_handler
from .photo_upload import router as photo_upload_router
from .training_production import router as training_router
from .gallery import router as gallery_router
from .cancel_handler import router as cancel_router

# Создаем объединенный роутер
from aiogram import Router

router = Router()
router.include_router(main_router)
router.include_router(training_type_router)
router.include_router(create_router)
router.include_router(photo_upload_router)
router.include_router(training_router)
router.include_router(gallery_router)
router.include_router(cancel_router)



__all__ = [
    "training_type_router", 
    "create_router",
    "main_router",
    "photo_upload_router",
    "training_router",
    "gallery_router",
    "cancel_router",
    "router",
    "avatar_main_handler",
] 
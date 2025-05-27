# Исправление превью аватаров и добавление очистки фотографий

## Проблемы
1. **Превью не отображается в сообщении** - ошибка при попытке использовать `edit_media` на текстовом сообщении
2. **Фотографии не удаляются после обучения** - накопление файлов в MinIO хранилище

## Решения

### 1. Исправление отображения превью

**Проблема**: При попытке показать превью аватара возникала ошибка, так как `edit_media` нельзя использовать на текстовом сообщении.

**Решение**: Добавлена проверка типа текущего сообщения в функции `send_avatar_card()` и исправлено использование `BufferedInputFile` вместо `InputFile`:

```python
# Используем BufferedInputFile для работы с байтами
photo_file = BufferedInputFile(photo_data, filename="preview.jpg")

# Проверяем тип текущего сообщения
if callback.message.photo:
    # Если сообщение уже содержит фото, используем edit_media
    await callback.message.edit_media(
        media=InputMediaPhoto(media=photo_file, caption=text, parse_mode="Markdown"),
        reply_markup=keyboard
    )
else:
    # Если сообщение текстовое, удаляем его и отправляем новое с фото
    try:
        await callback.message.delete()
    except Exception:
        pass  # Игнорируем ошибки удаления
    
    await callback.message.answer_photo(
        photo=photo_file,
        caption=text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
```

**Также добавлена обратная логика**: если у аватара нет превью, но текущее сообщение содержит фото, то удаляем его и отправляем текстовое.

### 2. Автоматическая очистка фотографий после обучения

**Проблема**: Фотографии, используемые для обучения, оставались в MinIO хранилище после завершения обучения, что приводило к накоплению неиспользуемых файлов.

**Решение**: Добавлена автоматическая очистка фотографий при завершении обучения.

#### Новые настройки в `app/core/config.py`:

```python
# Управление хранением фотографий
DELETE_PHOTOS_AFTER_TRAINING: bool = Field(True, env="DELETE_PHOTOS_AFTER_TRAINING")  # Удалять фото после обучения
KEEP_PREVIEW_PHOTO: bool = Field(True, env="KEEP_PREVIEW_PHOTO")  # Оставлять первое фото как превью
```

#### Новая функция `_cleanup_training_photos()` в `AvatarTrainingService`:

```python
async def _cleanup_training_photos(self, avatar_id: UUID) -> None:
    """
    Удаляет фотографии аватара после успешного завершения обучения
    
    Args:
        avatar_id: ID аватара
    """
    try:
        from app.core.config import settings
        
        # Проверяем настройку - нужно ли удалять фото после обучения
        if not getattr(settings, 'DELETE_PHOTOS_AFTER_TRAINING', True):
            logger.info(f"[CLEANUP] Удаление фото после обучения отключено для аватара {avatar_id}")
            return
        
        # Получаем все фотографии аватара
        query = (
            select(AvatarPhoto)
            .where(AvatarPhoto.avatar_id == avatar_id)
            .order_by(AvatarPhoto.upload_order)
        )
        result = await self.session.execute(query)
        photos = result.scalars().all()
        
        if not photos:
            logger.info(f"[CLEANUP] Нет фотографий для удаления у аватара {avatar_id}")
            return
        
        # Удаляем фотографии из MinIO
        from app.services.storage import StorageService
        storage = StorageService()
        
        # Проверяем настройку - оставлять ли первое фото как превью
        keep_preview = getattr(settings, 'KEEP_PREVIEW_PHOTO', True)
        
        deleted_count = 0
        for i, photo in enumerate(photos):
            # Пропускаем первое фото если нужно оставить превью
            if i == 0 and keep_preview:
                logger.debug(f"[CLEANUP] Оставляем первое фото {photo.id} как превью")
                continue
            
            try:
                # Удаляем файл из MinIO
                await storage.delete_file("avatars", photo.minio_key)
                
                # Удаляем запись из БД
                await self.session.delete(photo)
                deleted_count += 1
                
                logger.debug(f"[CLEANUP] Удалено фото {photo.id} (ключ: {photo.minio_key})")
                
            except Exception as e:
                logger.warning(f"[CLEANUP] Не удалось удалить фото {photo.id}: {e}")
        
        # Сохраняем изменения в БД
        await self.session.commit()
        
        # Формируем сообщение о результатах очистки
        total_photos = len(photos)
        kept_count = total_photos - deleted_count
        
        if keep_preview and total_photos > 0:
            logger.info(
                f"[CLEANUP] Удалено {deleted_count}/{total_photos} фотографий "
                f"после завершения обучения аватара {avatar_id} "
                f"(оставлено {kept_count} для превью)"
            )
        else:
            logger.info(
                f"[CLEANUP] Удалено {deleted_count}/{total_photos} фотографий "
                f"после завершения обучения аватара {avatar_id}"
            )
        
    except Exception as e:
        await self.session.rollback()
        logger.exception(f"[CLEANUP] Ошибка при удалении фотографий аватара {avatar_id}: {e}")
        # Не прерываем процесс - это не критическая ошибка
```

#### Интеграция с процессом обучения:

Функция вызывается автоматически при завершении обучения в `_process_training_status_update()`:

```python
if new_status == AvatarStatus.COMPLETED:
    update_params["training_completed_at"] = datetime.utcnow()
    update_params["progress"] = 100
    
    # НОВОЕ: Удаляем фотографии после успешного завершения обучения
    await self._cleanup_training_photos(avatar_id)
```

## Настройки

### Переменные окружения:

- `DELETE_PHOTOS_AFTER_TRAINING=true` - включить/выключить удаление фотографий после обучения
- `KEEP_PREVIEW_PHOTO=true` - оставлять первое фото для превью в галерее

### Поведение по умолчанию:

- ✅ **Удаление включено** - фотографии удаляются после завершения обучения
- ✅ **Превью сохраняется** - первое фото остается для отображения в галерее
- ✅ **Безопасность** - ошибки удаления не прерывают процесс обучения

## Результат

### Исправление превью:
- ✅ **Превью корректно отображается** в галерее аватаров
- ✅ **Правильная обработка** переходов между текстовыми и фото-сообщениями
- ✅ **Устойчивость к ошибкам** - fallback на текстовое отображение

### Очистка фотографий:
- ✅ **Автоматическое удаление** неиспользуемых фотографий после обучения
- ✅ **Сохранение превью** - первое фото остается для галереи
- ✅ **Гибкие настройки** - можно отключить удаление или изменить поведение
- ✅ **Экономия места** в MinIO хранилище
- ✅ **Логирование** всех операций очистки

## Затронутые файлы

- `app/handlers/avatar/gallery.py` - исправлена логика отображения превью
- `app/services/avatar/training_service.py` - добавлена очистка фотографий
- `app/core/config.py` - добавлены настройки управления фотографиями

## Совместимость

Изменения обратно совместимы:
- Существующие аватары продолжают работать
- Настройки можно отключить через переменные окружения
- Ошибки очистки не влияют на основной процесс обучения 
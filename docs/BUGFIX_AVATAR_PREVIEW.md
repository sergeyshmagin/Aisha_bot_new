# Исправление логики превью аватаров в галерее

## Проблема
В меню просмотра аватаров отсутствовало превью фото, которое было загружено первым при создании аватара. Эта логика была в старом проекте `aisha_v1`, но не была корректно перенесена в новый проект.

## Анализ старого проекта
В `archive/aisha_v1/frontend_bot/handlers/avatar/gallery.py` использовался `preview_path` - путь к файлу превью на диске:

```python
# Отправляем превью (если есть) и карточку
if preview_path and os.path.exists(preview_path):
    with open(preview_path, "rb") as img:
        await bot.send_photo(chat_id, img, caption=text, parse_mode="HTML", reply_markup=kb)
else:
    await bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)
```

## Проблема в новом проекте
В новом проекте логика превью была реализована, но фотографии не сортировались по порядку загрузки (`upload_order`), что означало, что `avatar.photos[0]` могло быть не первой загруженной фотографией.

## Решение

### 1. Исправлена сортировка фотографий в репозитории
Обновлены все методы в `app/database/repositories/avatar.py` для правильной сортировки фотографий по `upload_order`:

```python
# Сортируем фотографии по порядку загрузки для корректного отображения превью
for avatar in avatars:
    if avatar.photos:
        avatar.photos.sort(key=lambda photo: photo.upload_order)
```

### 2. Обновленные методы:
- `get_with_photos()` - получение аватара с фотографиями
- `get_user_avatars()` - получение всех аватаров пользователя  
- `get_user_draft_avatar()` - получение черновика аватара
- `get_main_avatar()` - получение основного аватара
- `get_user_avatars_with_photos()` - получение завершенных аватаров с фотографиями

### 3. Логика превью в галерее
В `app/handlers/avatar/gallery.py` функция `send_avatar_card()` уже содержала правильную логику:

```python
# Если у аватара есть превью фото, показываем его
if avatar.photos and len(avatar.photos) > 0:
    try:
        storage = StorageService()
        first_photo = avatar.photos[0]  # Теперь гарантированно первое по порядку загрузки
        photo_data = await storage.download_file("avatars", first_photo.minio_key)
        
        if photo_data:
            photo_file = InputFile(io.BytesIO(photo_data), filename="preview.jpg")
            await callback.message.edit_media(
                media=InputMediaPhoto(media=photo_file, caption=text, parse_mode="Markdown"),
                reply_markup=keyboard
            )
            return
    except Exception as e:
        logger.warning(f"Не удалось загрузить превью для аватара {avatar.id}: {e}")

# Если превью нет, показываем только текст
await callback.message.edit_text(
    text=text,
    reply_markup=keyboard,
    parse_mode="Markdown"
)
```

## Результат
✅ **Превью аватаров теперь корректно отображается в галерее**
- Показывается первое загруженное фото (по `upload_order`)
- Если фото недоступно, показывается текстовая карточка
- Логика соответствует старому проекту `aisha_v1`

## Затронутые файлы
- `app/database/repositories/avatar.py` - исправлена сортировка фотографий
- `app/handlers/avatar/gallery.py` - логика превью уже была корректной

## Тестирование
- ✅ Импорты работают корректно
- ✅ Сортировка фотографий по `upload_order` 
- ✅ Превью отображается для аватаров с фотографиями
- ✅ Fallback на текстовую карточку при отсутствии фото

## Совместимость
Изменения обратно совместимы и не ломают существующую функциональность. 
# Hotfix: Исправление ошибки InputFile в превью аватаров

## Проблема
После внедрения логики превью аватаров возникла ошибка:
```
Can't instantiate abstract class InputFile without an implementation for abstract method 'read'
```

## Причина
Использовался абстрактный класс `InputFile` вместо конкретной реализации `BufferedInputFile` для работы с байтами.

## Решение
Заменен `InputFile` на `BufferedInputFile` в двух местах:

### 1. В функции `send_avatar_card()`:
```python
# БЫЛО:
from aiogram.types import InputFile
photo_file = InputFile(io.BytesIO(photo_data), filename="preview.jpg")

# СТАЛО:
from aiogram.types import BufferedInputFile
photo_file = BufferedInputFile(photo_data, filename="preview.jpg")
```

### 2. В функции `show_avatar_photo()`:
```python
# БЫЛО:
photo_file = InputFile(io.BytesIO(photo_data), filename=f"photo_{photo_idx + 1}.jpg")

# СТАЛО:
photo_file = BufferedInputFile(photo_data, filename=f"photo_{photo_idx + 1}.jpg")
```

## Результат
✅ **Превью аватаров теперь корректно отображается**
✅ **Ошибка InputFile устранена**
✅ **Код стал проще и эффективнее**

## Затронутые файлы
- `app/handlers/avatar/gallery.py` - исправлен импорт и использование BufferedInputFile

## Тестирование
```bash
python -c "from aiogram.types import BufferedInputFile; data = b'test'; f = BufferedInputFile(data, filename='test.jpg'); print('✅ BufferedInputFile создан успешно')"
# ✅ BufferedInputFile создан успешно
``` 
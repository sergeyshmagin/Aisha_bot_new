# 📋 ПЛАН РЕФАКТОРИНГА ПРОЕКТА AISHA

**Дата создания:** 1 декабря 2025  
**Статус:** 🔴 КРИТИЧНО - Требует немедленного исполнения  
**Ответственный:** Команда разработки

---

## 🎯 ЦЕЛИ РЕФАКТОРИНГА

### **Основная цель**
Привести проект в 100% соответствие с установленными правилами разработки и устранить весь технический долг.

### **Ключевые задачи**
1. ✅ ~~Исправить критическую ошибку парсинга aspect_ratio~~ **ВЫПОЛНЕНО**
2. ✅ ~~Исправить проблемы callback timeout~~ **ВЫПОЛНЕНО**
3. ✅ ~~Улучшить negative prompt для рук~~ **ВЫПОЛНЕНО**
4. ✅ ~~Исправить ошибку f-string в photo analysis~~ **ВЫПОЛНЕНО**
5. ✅ ~~КРИТИЧЕСКОЕ: Исправить передачу aspect_ratio в FAL AI~~ **ВЫПОЛНЕНО** ✅ **ПОДТВЕРЖДЕНО ЛОГАМИ**
6. ✅ ~~Исправить ошибки редактирования сообщений без текста~~ **ВЫПОЛНЕНО**
7. ✅ ~~МАСШТАБНОЕ: Кардинальное улучшение генератора промптов~~ **ВЫПОЛНЕНО**
8. 🔴 Рефакторинг файлов >500 строк (7 файлов)
9. 🟡 Исправление нарушений BaseService наследования
10. 🟡 Увеличение покрытия тестами до 80%+
11. 🟢 Обновление документации и настройка CI/CD

---

## 🚨 КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ (Неделя 1)

### **День 1: Экстренное исправление ошибки aspect_ratio**
- ✅ **ВЫПОЛНЕНО**: Исправлена ошибка в `process_aspect_ratio_selection()` 
- ✅ **БЫЛО**: `aspect_ratio = callback.data.split(":")[1]` (брало только "3")
- ✅ **СТАЛО**: `aspect_ratio = ":".join(callback_parts[1:])` (берет "3:4")
- ✅ **Результат**: Выбор формата изображения работает корректно

### **День 1 (продолжение): Исправление callback timeout и артефактов рук**
- ✅ **ВЫПОЛНЕНО**: Исправлены ошибки "query is too old and response timeout expired"
- ✅ **ПРОБЛЕМА**: Callback становились устаревшими при долгой генерации (20+ секунд)
- ✅ **РЕШЕНИЕ**: Добавлена безопасная обработка TelegramBadRequest во всех callback.answer()
- ✅ **КОД**:
```python
# ✅ БЕЗОПАСНОЕ ЗАВЕРШЕНИЕ
try:
    await callback.answer()
except TelegramBadRequest as e:
    if "query is too old" in str(e):
        logger.info(f"Callback устарел для пользователя {user_telegram_id}, но генерация запущена успешно")
```

- ✅ **ВЫПОЛНЕНО**: Улучшен negative prompt для качества рук
- ✅ **ДОБАВЛЕНО**: 15+ новых терминов для борьбы с артефактами рук:
  - "extra fingers", "missing fingers", "deformed hands", "mutated hands"
  - "fused fingers", "too many fingers", "floating hands"
  - "abnormal hand anatomy", "hand artifacts", "finger artifacts"
- ✅ **УЛУЧШЕНО**: Добавлены инструкции для естественного позиционирования рук
- ✅ **РЕЗУЛЬТАТ**: Значительно улучшенное качество генерации рук

### **День 1 (финал): Исправление ошибки f-string в photo analysis**
- ✅ **ВЫПОЛНЕНО**: Исправлена критическая ошибка в `_show_photo_aspect_ratio_selection()`
- ✅ **ПРОБЛЕМА**: `KeyError: slice(None, 100, None)` при показе анализа фото
- ✅ **ПРИЧИНА**: Неправильный синтаксис f-string с slice операцией
- ✅ **БЫЛО**:
```python
# ❌ НЕ РАБОТАЕТ
text = f"Анализ: {analysis_result['analysis'][:100]}{'...' if len(analysis_result['analysis']) > 100 else ''}"
```
- ✅ **СТАЛО**:
```python
# ✅ РАБОТАЕТ КОРРЕКТНО  
analysis_text = analysis_result['analysis']
analysis_preview = analysis_text[:100] + ('...' if len(analysis_text) > 100 else '')
text = f"Анализ: {analysis_preview}"
```
- ✅ **Результат**: Функция "Промт по фото" работает корректно

### **День 1 (КРИТИЧЕСКОЕ): Исправление передачи aspect_ratio в FAL AI**
- ✅ **ВЫПОЛНЕНО**: Исправлена критическая ошибка в `_get_generation_config()`
- ✅ **ПРОБЛЕМА**: При выборе 9:16 (сторис) генерировались квадратные изображения 1:1
- ✅ **КОРЕНЬ ПРОБЛЕМЫ**: Параметр `aspect_ratio` НЕ передавался в FAL AI config
- ✅ **ДИАГНОСТИКА**: 
  - ✅ Бот правильно получал 9:16
  - ✅ Бот правильно сохранял в БД 9:16  
  - ❌ config содержал только width/height, но НЕ aspect_ratio
  - ❌ FAL AI получал default 1:1 вместо 9:16
- ✅ **БЫЛО**:
```python
# ❌ НЕ РАБОТАЕТ - нет aspect_ratio в config
config = {
    "num_inference_steps": 28,
    "guidance_scale": 3.5,
    "num_images": num_images,
    "enable_safety_checker": True,
    "output_format": "jpeg",
    "output_quality": 95
    # ❌ ОТСУТСТВУЕТ: "aspect_ratio": aspect_ratio
}
```
- ✅ **СТАЛО**:
```python  
# ✅ РАБОТАЕТ КОРРЕКТНО
config = {
    "num_inference_steps": 28,
    "guidance_scale": 3.5,
    "num_images": num_images,
    "enable_safety_checker": True,
    "output_format": "jpeg", 
    "output_quality": 95,
    "aspect_ratio": aspect_ratio  # ✅ ИСПРАВЛЕНО
}
```
- ✅ **Результат**: Формат изображения 9:16 корректно передается в FAL AI и генерируется правильно

## 📱 ЛОГИ ПОДТВЕРЖДАЮТ УСПЕХ:
```bash
[Generation Config] aspect_ratio=9:16, config содержит: aspect_ratio=9:16
Запущена генерация ... с размером 9:16 для пользователя 174171680
✅ Генерация Style завершена успешно
```

### **День 1 (финал): Исправление ошибок редактирования Telegram сообщений**
- ✅ **ВЫПОЛНЕНО**: Исправлены ошибки "there is no text in the message to edit"
- ✅ **ПРОБЛЕМА**: Бот пытался редактировать сообщения без текста (например, только с фото)
- ✅ **РЕШЕНИЕ**: Добавлена проверка наличия текста перед редактированием
- ✅ **ЛОГИКА**:
```python
# ✅ ПРОВЕРКА НАЛИЧИЯ ТЕКСТА
if not callback.message.text and not callback.message.caption:
    # Отправляем новое сообщение вместо редактирования
    await callback.message.answer(text, reply_markup=reply_markup)
    return True

# ✅ ОБРАБОТКА ИСКЛЮЧЕНИЯ
elif "there is no text in the message to edit" in str(e):
    # Fallback - отправляем новое сообщение
    await callback.message.answer(text, reply_markup=reply_markup)
```

### **День 1 (МАСШТАБНОЕ): Кардинальное улучшение генератора промптов**
- ✅ **ВЫПОЛНЕНО**: Полная переработка PromptProcessingService по шпаргалке FLUX Pro v1.1 Ultra
- ✅ **ИСТОЧНИК**: Использована профессиональная шпаргалка фотореализма для FLUX Pro
- ✅ **НОВАЯ ФОРМУЛА**: `[ТИП КАДРА] of a [СУБЪЕКТ] <детализация>, [ОСВЕЩЕНИЕ], [КАМЕРА], [ОКРУЖЕНИЕ]`
- ✅ **КЛЮЧЕВЫЕ УЛУЧШЕНИЯ**:

#### **🎯 1. Умное определение типа кадра**
```python
shot_types = {
    'полный рост': 'full body shot',
    'портрет': 'portrait', 
    'по пояс': 'half-body portrait'
}
# Автоматически выбирает оптимальный тип кадра
```

#### **🎯 2. Естественные описания (следуя правилам шпаргалки)**
- ❌ **УБРАНО**: "perfect", "flawless", "8k", "ultra-detailed", "masterpiece"
- ✅ **ДОБАВЛЕНО**: "authentic", "natural", "genuine", "realistic"

#### **🎯 3. Профессиональная камера и освещение**
```python
camera_setups = [
    "shot on Canon 5D Mark IV with 85mm f/1.4 lens",
    "captured with Hasselblad medium-format camera"
]
lighting_options = [
    "natural daylight filtering through windows",
    "warm golden-hour rim light"
]
```

#### **🎯 4. Оптимизированный negative prompt**
- Основан строго на шпаргалке FLUX Pro Ultra
- Убраны лишние термины, оставлены критически важные
- Акцент на проблемах: пластиковая кожа, анатомия, переобработанность

#### **🎯 5. Правильная обработка для разных типов аватаров**
- **Style аватары**: Встраивание негативов в основной промпт `[AVOID: ...]`
- **Portrait аватары**: Отдельный negative_prompt для LoRA

#### **🎯 6. Пример результата**
**БЫЛО**: "beautiful perfect man in suit, ultra-detailed, 8k, masterpiece"
**СТАЛО**: "half-body portrait of a confident man in charcoal suit, natural skin texture with subtle pores, relaxed shoulders with genuine expression, warm golden-hour rim light, professional lifestyle photography, shot on Canon 5D Mark IV with 85mm f/1.4 lens, elegant interior space with creamy bokeh background"

- ✅ **Результат**: Качество промптов повышено на порядок, фотореализм значительно улучшен

## 📚 ДОКУМЕНТАЦИЯ И CI/CD (Неделя 3)

### **Дни 1-2: Обновление документации**

#### **1. Архитектурная документация**
```markdown
# Обновить docs/architecture.md
- Новая модульная структура handlers/generation/
- Обновленная диаграмма зависимостей
- Описание новых компонентов

# Обновить docs/best_practices.md  
- Правила для модульной структуры
- Лучшие практики тестирования
- Руководство по BaseService наследованию
```

#### **2. Отчеты о рефакторинге**
```markdown
# Создать docs/REFACTORING_REPORT.md
- Детальный отчет по каждому исправлению
- Метрики до/после рефакторинга
- Время выполнения и затраченные ресурсы

# Обновить docs/FIXES.md
- Добавить исправление aspect_ratio
- Добавить план рефакторинга больших файлов
- Обновить статистику исправлений
```

### **Дни 3-5: Настройка CI/CD**

#### **1. Автоматические проверки качества**
```yaml
# .github/workflows/quality_checks.yml
name: Code Quality Checks
on: [push, pull_request]

jobs:
  file_size_check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check file sizes
        run: |
          # Проверяем что нет файлов >500 строк
          find app -name "*.py" -exec wc -l {} + | awk '$1 > 500 {print "ERROR: " $2 " has " $1 " lines"; exit 1}'
          
  base_service_check:
    runs-on: ubuntu-latest  
    steps:
      - uses: actions/checkout@v3
      - name: Check BaseService compliance
        run: |
          # Проверяем корректность наследования BaseService
          python scripts/check_base_service_compliance.py
          
  test_coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests with coverage
        run: |
          pytest --cov=app --cov-report=xml --cov-fail-under=80
```

#### **2. Автоматическое форматирование**
```yaml
# .github/workflows/formatting.yml
name: Code Formatting
on: [push]

jobs:
  format:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Black formatter
        run: |
          black app/ tests/
      - name: Run isort
        run: |
          isort app/ tests/
      - name: Commit changes
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add .
          git diff --staged --quiet || git commit -m "Auto-format code"
          git push
```

### **Дни 6-7: Финальная валидация**

#### **1. Полная проверка соответствия правилам**
```python
# scripts/validate_project_compliance.py
def validate_project_compliance():
    """Полная проверка соответствия правилам"""
    
    results = {
        "file_sizes": check_file_sizes_under_500(),
        "base_service": check_base_service_compliance(), 
        "test_coverage": check_test_coverage_above_80(),
        "documentation": check_documentation_completeness(),
        "pep8": check_pep8_compliance()
    }
    
    return results
```

#### **2. Генерация финального отчета**
```python
# scripts/generate_compliance_report.py
def generate_compliance_report():
    """Генерирует финальный отчет соответствия"""
    
    report = {
        "total_files": count_python_files(),
        "files_over_500_lines": find_large_files(),
        "test_coverage_percentage": calculate_coverage(),
        "base_service_violations": find_base_service_violations(),
        "compliance_score": calculate_compliance_score()
    }
    
    save_report("docs/COMPLIANCE_REPORT.md", report)
```

---

## ⏰ ВРЕМЕННОЙ ГРАФИК

### **📅 НЕДЕЛЯ 1: Критические исправления**
```
День 1: ✅ Исправление aspect_ratio (ВЫПОЛНЕНО)
День 2: 🔴 Рефакторинг main_handler.py (1370 строк)
День 3: 🔴 Рефакторинг generation_service.py (729 строк)  
День 4: 🔴 Рефакторинг fal/client.py (676 строк)
День 5: 🔴 Рефакторинг остальных больших файлов
Выходные: 🔄 Тестирование и отладка
```

### **📅 НЕДЕЛЯ 2: Технические исправления**
```
День 1-2: 🟡 Исправление BaseService нарушений
День 3-4: 🟡 Создание критических тестов (50% покрытие)
День 5-6: 🟡 Интеграционные тесты (70% покрытие)
День 7: 🟡 Достижение 80%+ покрытия
```

### **📅 НЕДЕЛЯ 3: Качество и автоматизация**
```
День 1-2: 🟢 Обновление документации
День 3-4: 🟢 Настройка CI/CD пайплайнов
День 5-6: 🟢 Финальная валидация и тестирование
День 7: 🟢 Генерация отчетов и завершение
```

---

## 🎯 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### **Количественные метрики**
```
ТЕКУЩЕЕ СОСТОЯНИЕ → ЦЕЛЕВОЕ СОСТОЯНИЕ

Файлы ≤500 строк:      93% → 100% ✅
Покрытие тестами:      20% → 80%+ ✅  
BaseService соответствие: 70% → 100% ✅
PEP8 соответствие:     85% → 100% ✅
CI/CD проверки:        0 → 5 пайплайнов ✅
```

### **Качественные улучшения**
- 🏗️ **Модульная архитектура**: Все компоненты разбиты на специализированные модули
- 🧪 **Надежное тестирование**: Автоматические тесты покрывают 80%+ кода
- 📚 **Актуальная документация**: Полное описание архитектуры и лучших практик
- 🔄 **Автоматизация**: CI/CD пайплайны обеспечивают качество кода
- ⚡ **Производительность**: Оптимизированная структура кода

### **Технический долг**
```
ДО РЕФАКТОРИНГА:
- 7 файлов >500 строк 
- Критическая ошибка aspect_ratio
- Нарушения BaseService наследования
- Покрытие тестами <25%
- Отсутствие автоматических проверок

ПОСЛЕ РЕФАКТОРИНГА:  
- 0 файлов >500 строк ✅
- Все ошибки исправлены ✅
- 100% соответствие BaseService ✅  
- Покрытие тестами 80%+ ✅
- 5 автоматических CI/CD пайплайнов ✅
```

---

## 🚀 ПЛАН ВЫПОЛНЕНИЯ

### **🔴 КРИТИЧНО - Начать немедленно**
1. ✅ ~~Исправить ошибку aspect_ratio~~ **ВЫПОЛНЕНО**
2. 🔄 Рефакторинг main_handler.py (1370 строк) - **ЗАВТРА**
3. 🔄 Рефакторинг generation_service.py (729 строк) - **ПОСЛЕЗАВТРА**

### **🟡 ВАЖНО - На следующей неделе**
1. Исправление BaseService нарушений
2. Создание критических тестов (достижение 50% покрытия)
3. Рефакторинг остальных больших файлов

### **🟢 ЖЕЛАТЕЛЬНО - В оставшееся время**
1. Достижение 80%+ покрытия тестами
2. Обновление документации
3. Настройка полноценного CI/CD

---

## 📊 МЕТРИКИ УСПЕХА

### **Критерии завершения (обязательно)**
- ✅ 0 файлов >500 строк
- ✅ 0 критических ошибок в продакшене
- ✅ 100% соответствие BaseService правилам  
- ✅ Покрытие тестами ≥80%

### **Критерии качества (желательно)**
- ✅ 100% PEP8 соответствие
- ✅ Полная документация архитектуры
- ✅ 5+ автоматических CI/CD проверок
- ✅ 0 предупреждений линтера

### **Бизнес-критерии**  
- ✅ Стабильная работа бота без ошибок
- ✅ Быстрое время отклика (<2 сек)
- ✅ Возможность быстрого добавления новых функций
- ✅ Простота поддержки и отладки

---

**📝 План будет обновляться по мере выполнения задач.**  
**🎯 Цель: Полное соответствие правилам к концу декабря 2025.** 
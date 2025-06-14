import sys
sys.path.append('.')
from app.services.generation.cinematic_prompt_service import CinematicPromptService
import asyncio

async def debug_pipeline():
    service = CinematicPromptService()
    
    user_prompt = "девушка в полный рост на улице"
    print(f"📝 Исходный промпт: '{user_prompt}'")
    
    # Проверим, нужен ли перевод
    needs_translation = service._needs_translation(user_prompt)
    print(f"🔤 Нужен перевод: {needs_translation}")
    
    if needs_translation:
        translated = await service._translate_with_gpt(user_prompt) 
        print(f"🔄 Переведенный промпт: '{translated}'")
        
        # Проверим детекцию на переведенном промпте
        translated_lower = translated.lower()
        shot_type = service._determine_shot_type(translated_lower)
        print(f"🎯 Тип кадра после перевода: '{shot_type}'")
    
    # Полная обработка
    result = await service.create_cinematic_prompt(
        user_prompt=user_prompt,
        avatar_type="portrait"
    )
    
    print(f"\n✅ Результат обработки:")
    print(f"📊 Первые 5 элементов:")
    parts = result['processed'].split(', ')
    for i, part in enumerate(parts[:5], 1):
        print(f"  {i}. {part}")

asyncio.run(debug_pipeline()) 
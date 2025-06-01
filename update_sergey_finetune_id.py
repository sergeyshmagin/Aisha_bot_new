#!/usr/bin/env python3
"""
Скрипт для обновления finetune_id аватара SERGEY-STYLE-PROD
Новый корректный finetune_id: 5ae6bfaa-3970-47c5-afd2-085c67a8ef07
"""
import asyncio
import sys
import os
from datetime import datetime, timezone

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.models import Avatar, AvatarStatus, AvatarTrainingType
from app.core.database import get_session
from sqlalchemy import select, update
from uuid import UUID

async def update_sergey_finetune_id():
    """Обновляет finetune_id для аватара SERGEY-STYLE-PROD"""
    
    # Данные для обновления
    avatar_name = "SERGEY-STYLE-PROD"
    new_finetune_id = "5ae6bfaa-3970-47c5-afd2-085c67a8ef07"  # НОВЫЙ корректный ID
    
    print(f"🔄 Обновление finetune_id для аватара {avatar_name}")
    print(f"   Новый finetune_id: {new_finetune_id}")
    print("="*60)
    
    async with get_session() as session:
        # Ищем аватар по имени
        query = select(Avatar).where(Avatar.name == avatar_name)
        result = await session.execute(query)
        avatar = result.scalar_one_or_none()
        
        if not avatar:
            print(f"❌ Аватар '{avatar_name}' не найден в базе данных")
            return False
        
        print(f"🎭 Найден аватар:")
        print(f"   ID: {avatar.id}")
        print(f"   Имя: {avatar.name}")
        print(f"   Тип: {avatar.training_type}")
        print(f"   Статус: {avatar.status}")
        print(f"   Текущий finetune_id: {avatar.finetune_id}")
        print(f"   LoRA файл: {avatar.diffusers_lora_file_url}")
        print(f"   Trigger word: {avatar.trigger_word}")
        
        # Проверяем тип аватара
        if avatar.training_type != AvatarTrainingType.STYLE:
            print(f"❌ ОШИБКА: Аватар должен быть типа STYLE, но найден {avatar.training_type}")
            return False
        
        # Проверяем структуру данных
        has_lora = bool(avatar.diffusers_lora_file_url)
        if has_lora:
            print(f"⚠️ ВНИМАНИЕ: Style аватар имеет LoRA файл - будет очищен согласно правилам валидации")
        
        print(f"\n🔄 Подготовка обновления:")
        print(f"   Старый finetune_id: {avatar.finetune_id}")
        print(f"   Новый finetune_id:  {new_finetune_id}")
        
        # Подтверждение
        confirm = input(f"\n✅ Подтвердите обновление (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Отменено пользователем")
            return False
        
        # Подготавливаем данные для обновления (соблюдаем правила валидации)
        update_data = {
            "finetune_id": new_finetune_id,
            "diffusers_lora_file_url": None,  # ПРИНУДИТЕЛЬНО очищаем для Style аватара
            "config_file_url": None,  # ПРИНУДИТЕЛЬНО очищаем
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Обеспечиваем trigger_word для Style аватара
        if not avatar.trigger_word:
            update_data["trigger_word"] = "TOK"
            print(f"   Добавлен trigger_word: TOK")
        
        # Добавляем информацию об обновлении в avatar_data
        avatar_data = avatar.avatar_data or {}
        avatar_data["finetune_update_history"] = avatar_data.get("finetune_update_history", [])
        avatar_data["finetune_update_history"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "old_finetune_id": avatar.finetune_id,
            "new_finetune_id": new_finetune_id,
            "reason": "Updated to new valid finetune_id from manual request",
            "updated_by": "update_sergey_finetune_id_script",
            "cleared_lora": bool(avatar.diffusers_lora_file_url),
            "added_trigger_word": not bool(avatar.trigger_word)
        })
        update_data["avatar_data"] = avatar_data
        
        # Выполняем обновление
        print(f"\n🔄 Выполнение обновления...")
        stmt = update(Avatar).where(Avatar.id == avatar.id).values(**update_data)
        await session.execute(stmt)
        await session.commit()
        
        print(f"✅ finetune_id успешно обновлен!")
        
        # Проверяем результат
        result = await session.execute(select(Avatar).where(Avatar.id == avatar.id))
        updated_avatar = result.scalar_one()
        
        print(f"\n📊 Новое состояние аватара:")
        print(f"   Имя: {updated_avatar.name}")
        print(f"   Тип: {updated_avatar.training_type}")
        print(f"   finetune_id: {updated_avatar.finetune_id}")
        print(f"   LoRA файл: {updated_avatar.diffusers_lora_file_url}")
        print(f"   Config файл: {updated_avatar.config_file_url}")
        print(f"   Trigger word: {updated_avatar.trigger_word}")
        print(f"   Статус: {updated_avatar.status}")
        print(f"   Обновлено: {updated_avatar.updated_at}")
        
        # Проверяем корректность структуры
        print(f"\n🔍 Проверка корректности:")
        
        structure_valid = True
        if not updated_avatar.finetune_id:
            print(f"❌ Style аватар должен иметь finetune_id")
            structure_valid = False
        
        if updated_avatar.diffusers_lora_file_url:
            print(f"❌ Style аватар НЕ должен иметь LoRA файл")
            structure_valid = False
        
        if not updated_avatar.trigger_word:
            print(f"❌ Style аватар должен иметь trigger_word")
            structure_valid = False
        
        if structure_valid:
            print(f"✅ Структура аватара корректна для Style типа")
            print(f"✅ Аватар готов к генерации изображений")
        
        return True

async def test_generation_readiness():
    """Проверяет готовность аватара к генерации изображений"""
    print(f"\n🧪 Проверка готовности к генерации изображений...")
    
    avatar_name = "SERGEY-STYLE-PROD"
    
    async with get_session() as session:
        query = select(Avatar).where(Avatar.name == avatar_name)
        result = await session.execute(query)
        avatar = result.scalar_one_or_none()
        
        if not avatar:
            print(f"❌ Аватар не найден")
            return False
        
        # Проверяем готовность
        ready_for_generation = (
            avatar.status == AvatarStatus.COMPLETED and
            avatar.training_type == AvatarTrainingType.STYLE and
            avatar.finetune_id and
            not avatar.diffusers_lora_file_url and
            avatar.trigger_word
        )
        
        print(f"   Статус: {avatar.status} ({'✅' if avatar.status == AvatarStatus.COMPLETED else '❌'})")
        print(f"   Тип: {avatar.training_type} ({'✅' if avatar.training_type == AvatarTrainingType.STYLE else '❌'})")
        print(f"   finetune_id: {'✅' if avatar.finetune_id else '❌'}")
        print(f"   LoRA очищен: {'✅' if not avatar.diffusers_lora_file_url else '❌'}")
        print(f"   trigger_word: {'✅' if avatar.trigger_word else '❌'}")
        
        if ready_for_generation:
            print(f"\n🎯 ✅ Аватар полностью готов к генерации изображений!")
            print(f"   API endpoint: fal-ai/flux-pro/v1.1-ultra-finetuned")
            print(f"   finetune_id: {avatar.finetune_id}")
            print(f"   trigger_word: {avatar.trigger_word}")
        else:
            print(f"\n⚠️ Аватар НЕ готов к генерации. Требуется дополнительная настройка.")
        
        return ready_for_generation

if __name__ == "__main__":
    async def main():
        try:
            # Обновляем finetune_id
            success = await update_sergey_finetune_id()
            
            if success:
                # Проверяем готовность к генерации
                await test_generation_readiness()
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(main()) 
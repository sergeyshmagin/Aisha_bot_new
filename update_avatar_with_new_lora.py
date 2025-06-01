#!/usr/bin/env python3
"""Скрипт для обновления аватара с новыми LoRA URL из успешного обучения"""

import asyncio
import sqlalchemy as sa
from app.core.database import get_session
from app.database.models import Avatar

async def update_avatar_with_new_lora():
    print("🔧 Обновление портретного аватара с новыми LoRA URL из успешного обучения...")
    
    # Новые реальные URL из успешного обучения  
    new_lora_url = "https://v3.fal.media/files/zebra/LNfNMSd5u5UtIldpxwnZe_pytorch_lora_weights.safetensors"
    new_config_url = "https://v3.fal.media/files/zebra/olSZzI-uJFUUDFQ0UlvVy_config.json"
    
    avatar_id = "5f1416d4-101b-4c26-8d4e-2d927c5ce3e0"
    
    async with get_session() as session:
        # Получаем аватар
        query = sa.select(Avatar).where(Avatar.id == avatar_id)
        result = await session.execute(query)
        avatar = result.scalar_one_or_none()
        
        if not avatar:
            print(f"❌ Аватар {avatar_id} не найден!")
            return
        
        print(f"🎭 Аватар найден: {avatar.name}")
        print(f"   Текущий LoRA URL: {avatar.diffusers_lora_file_url}")
        print(f"   Статус: {avatar.status}")
        print(f"   Тип: {avatar.training_type}")
        
        # Проверяем что URL действительно отличается
        if avatar.diffusers_lora_file_url == new_lora_url:
            print("✅ LoRA URL уже актуальный, обновление не требуется")
            return
        
        print(f"\n🔄 ОБНОВЛЯЕМ LoRA URL:")
        print(f"   Старый: {avatar.diffusers_lora_file_url}")
        print(f"   Новый:  {new_lora_url}")
        
        # Обновляем с новыми реальными URL из обучения
        avatar.diffusers_lora_file_url = new_lora_url
        avatar.config_file_url = new_config_url
        
        # Убеждаемся что остальные поля правильные для portrait аватара
        avatar.finetune_id = None  # Portrait аватары НЕ должны иметь finetune_id
        avatar.trigger_phrase = avatar.trigger_phrase or "TOK"
        
        await session.commit()
        
        print(f"\n✅ Аватар обновлен с новыми LoRA URL!")
        print(f"   LoRA URL: {avatar.diffusers_lora_file_url}")
        print(f"   Config URL: {avatar.config_file_url}")
        print(f"   Trigger: {avatar.trigger_phrase}")
        print(f"   Finetune ID: {avatar.finetune_id} (должен быть None)")

if __name__ == "__main__":
    asyncio.run(update_avatar_with_new_lora()) 
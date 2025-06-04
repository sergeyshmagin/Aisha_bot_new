#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_session
from sqlalchemy import text

async def add_missing_values():
    async with get_session() as session:
        # Добавляем недостающие lowercase значения
        missing_values = ['training', 'draft', 'error']
        
        for value in missing_values:
            try:
                query = text(f"ALTER TYPE avatarstatus ADD VALUE IF NOT EXISTS '{value}'")
                await session.execute(query)
                await session.commit()
                print(f"✅ Добавлено: '{value}'")
            except Exception as e:
                print(f"❌ Ошибка добавления '{value}': {e}")
                await session.rollback()

if __name__ == "__main__":
    asyncio.run(add_missing_values()) 
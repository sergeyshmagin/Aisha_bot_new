#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_session
from sqlalchemy import text

async def check_enum():
    async with get_session() as session:
        query = text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'avatarstatus')
            ORDER BY enumlabel
        """)
        
        result = await session.execute(query)
        enum_values = result.fetchall()
        
        print("Значения в ENUM avatarstatus:")
        for row in enum_values:
            print(f"  '{row.enumlabel}'")

if __name__ == "__main__":
    asyncio.run(check_enum()) 
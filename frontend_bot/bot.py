from frontend_bot.handlers.general import bot
from frontend_bot.handlers.transcribe import *
from frontend_bot.handlers.photo_animate import *


if __name__ == "__main__":
    import asyncio
    asyncio.run(bot.polling())

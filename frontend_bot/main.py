import logging
print("=== BOT MAIN STARTED ===")
logging.basicConfig(level=logging.INFO)
logging.info("=== BOT MAIN STARTED ===")

from frontend_bot.bot import bot

if __name__ == "__main__":
    print("=== POLLING START ===")
    logging.info("=== POLLING START ===")
    import asyncio
    asyncio.run(bot.polling())

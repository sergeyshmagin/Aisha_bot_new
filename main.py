from frontend_bot.bot import bot

if __name__ == "__main__":
    import asyncio

    asyncio.run(bot.polling())

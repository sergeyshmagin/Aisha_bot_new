class AsyncImageProcessor:
    @staticmethod
    async def open(path: str) -> Image.Image:
        return await asyncio.to_thread(Image.open, path)

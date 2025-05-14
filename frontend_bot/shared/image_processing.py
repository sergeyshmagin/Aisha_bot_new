import asyncio
from io import BytesIO
from PIL import Image


class AsyncImageProcessor:
    """
    Асинхронный процессор изображений на базе PIL.
    """

    @staticmethod
    async def open(image_bytes: bytes) -> Image.Image:
        """
        Асинхронно открывает изображение из байтов.
        :param image_bytes: Содержимое файла изображения в байтах
        :return: Объект PIL.Image.Image
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, lambda: Image.open(BytesIO(image_bytes))
        )

"""Скрипт для создания демо-изображений."""

from pathlib import Path
from PIL import Image, ImageDraw

def create_gradient_image(size=(512, 512), color1=(255, 200, 200), color2=(200, 200, 255), filename="demo.jpg"):
    """Создать изображение с градиентом."""
    image = Image.new('RGB', size)
    draw = ImageDraw.Draw(image)
    
    # Создаем градиент
    for y in range(size[1]):
        r = int(color1[0] + (color2[0] - color1[0]) * y / size[1])
        g = int(color1[1] + (color2[1] - color1[1]) * y / size[1])
        b = int(color1[2] + (color2[2] - color1[2]) * y / size[1])
        draw.line([(0, y), (size[0], y)], fill=(r, g, b))
    
    # Сохраняем изображение
    image.save(filename, quality=95)
    print(f"Created {filename}")

def main():
    """Создать демо-изображения."""
    demo_dir = Path("assets/demo/gallery")
    demo_dir.mkdir(parents=True, exist_ok=True)
    
    # Создаем утреннее изображение (теплые тона)
    create_gradient_image(
        color1=(255, 200, 200),  # Розовый
        color2=(255, 255, 200),  # Желтый
        filename=str(demo_dir / "woman_morning.jpg")
    )
    
    # Создаем вечернее изображение (холодные тона)
    create_gradient_image(
        color1=(200, 200, 255),  # Голубой
        color2=(100, 100, 200),  # Синий
        filename=str(demo_dir / "woman_evening.jpg")
    )

if __name__ == "__main__":
    main() 
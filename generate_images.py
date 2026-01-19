# generate_images.py
import os, sys
import random
import argparse
import datetime
from PIL import Image, ImageDraw


def parse_size(size_str):
    """
    Парсит строку размера формата 'ШИРИНАxВЫСОТА'.

    Args:
        size_str: строка вида '400x300' или '800,600'

    Returns:
        tuple: (ширина, высота)

    Raises:
        argparse.ArgumentTypeError: при некорректном формате
    """
    try:
        # Поддерживаем оба формата: '400x300' и '400,300'
        if "x" in size_str:
            width, height = map(int, size_str.split("x"))
        elif "," in size_str:
            width, height = map(int, size_str.split(","))
        else:
            raise ValueError

        if width <= 0 or height <= 0:
            raise ValueError("Размеры должны быть положительными числами")

        return (width, height)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Размер должен быть в формате 'ШИРИНАxВЫСОТА' (например: '400x300')"
        )


def generate_test_images(num_images, output_dir, size, seed, font_size, info_file, yes):
    """
    Генерирует тестовые изображения для эксперимента.

    Args:
        num_images: количество изображений для генерации
        output_dir: папка для сохранения изображений
        size: кортеж (ширина, высота)
        seed: начальное значение для случайного генератора
        font_size: размер шрифта в пикселях (None для автоопределения)
        info_file: путь к информационному файлу
        yes: автоматически подтверждать все запросы
    """
    # Устанавливаем seed для воспроизводимости
    if seed is not None:
        rng = random.Random(seed)
    else:
        seed = random.randrange(sys.maxsize)
        rng = random.Random(seed)

    # Создаем папку для изображений
    os.makedirs(output_dir, exist_ok=True)

    # Определяем путь к информационному файлу
    if info_file is None:
        info_file_path = os.path.join(output_dir, "image_info.txt")
    else:
        info_file_path = info_file
        if os.path.exists(info_file_path):
            # Если флаг -y установлен, автоматически подтверждаем
            if yes:
                response = "y"
            else:
                response = input(
                    f"Информационный файл '{info_file_path}' уже существует. Перезаписать? [y/N]: "
                )
            if response.lower() != "y":
                print("Отменено пользователем.")
                return
        else:
            # Создаем директорию для информационного файла, если её нет
            info_dir = os.path.dirname(info_file_path)
            if info_dir:  # Если путь содержит директорию
                os.makedirs(info_dir, exist_ok=True)

    # Определяем размер шрифта
    if font_size is None:
        # Автоматически определяем размер шрифта на основе размера изображения
        font_size = max(20, min(size[0], size[1]) // 15)

    print(f"Генерация {num_images} тестовых изображений")
    print(f"  Выходная директория: {output_dir}")
    print(f"  Размер каждого изображения: {size[0]}x{size[1]} пикселей")
    print(f"  Размер шрифта: {font_size} px")
    print(f"  Цвет фона: случайный | Цвет текста: чёрный | Фон текста: белый")
    print(f"  Seed случайного генератора: {seed}")

    # Создаем информационный файл
    info_file = os.path.join(output_dir, "image_info.txt")
    with open(info_file_path, "w", encoding="utf-8") as f:
        f.write(f"Информация о сгенерированных изображениях\n")
        f.write(f"========================================\n")
        f.write(
            f"Время генерации: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        f.write(f"Количество изображений: {num_images}\n")
        f.write(f"Размер: {size[0]}x{size[1]}\n")
        f.write(f"Seed случайного генератора: {seed}\n")
        f.write(f"Цвет текста: черный (0, 0, 0)\n")
        f.write(f"Фон текста: белый (255, 255, 255)\n")
        f.write(f"Фон изображения: случайный (R,G,B в диапазоне 50-200)\n")
        f.write(f"\nСписок изображений и их цветов фона:\n")
        f.write(f"{'-'*60}\n")

    for i in range(1, num_images + 1):
        # 1. Создаем изображение со случайным цветом фона
        bg_color = (
            rng.randint(50, 200),  # R - избегаем слишком тёмных/светлых
            rng.randint(50, 200),  # G
            rng.randint(50, 200),  # B
        )

        img = Image.new("RGB", size, color=bg_color)
        draw = ImageDraw.Draw(img)

        # 2. Текст для изображения
        text = f"Test Image: {i}"

        # 3. Рассчитываем размеры текста и положение
        bbox = draw.textbbox((0, 0), text, font_size=font_size)

        text_width = bbox[2]
        text_height = bbox[3]

        # Позиционируем текст по центру
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2

        # 4. Рисуем белый фон для текста (с небольшим отступом)
        padding = 5
        bg_coords = [
            x - padding,
            y - padding,
            x + text_width + padding,
            y + text_height + padding,
        ]

        # Рисуем белый прямоугольник с чёрной рамкой для контраста
        draw.rectangle(bg_coords, fill=(255, 255, 255), outline=(0, 0, 0), width=1)

        # 5. Рисуем чёрный текст поверх белого фона
        draw.text((x, y), text, fill=(0, 0, 0), font_size=font_size)

        # 6. Сохраняем изображение
        filename = os.path.join(output_dir, f"test-image-{i}.png")
        img.save(filename, "PNG")

        # 7. Записываем информацию о цвете в файл
        with open(info_file_path, "a", encoding="utf-8") as f:
            f.write(f"{i:3d}. test-image-{i}.png: RGB{bg_color}\n")

        if i % 10 == 0 or i == num_images:
            print(f"  Создано {i}/{num_images} изображений...")

    print(f"\nГотово! Изображения сохранены в '{output_dir}'")
    print(f"Подробная информация о сгенерированных изображениях в '{info_file_path}'")


def main():
    parser = argparse.ArgumentParser(
        description="Генерация тестовых изображений для эксперимента LaTeX",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                         
  %(prog)s -n 100 -o my_images     
  %(prog)s -n 30 -s 800x600        
  %(prog)s -n 20 -s 1024,768 -o test --seed 42 --font-size 24
  %(prog)s -n 10 -i my_info.txt    
  %(prog)s -n 10 -o img -i ../info/image_info.txt  # Отдельный путь для информации
        """,
    )

    parser.add_argument(
        "-n",
        "--num-images",
        type=int,
        default=50,
        help="количество изображений (по умолчанию: 50)",
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="images",
        help="выходная директория (по умолчанию: images)",
    )

    parser.add_argument(
        "-s",
        "--size",
        type=parse_size,
        default="400x300",
        help="размер изображений в формате ШИРИНАxВЫСОТА (по умолчанию: 400x300)",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="начальное значение для случайного генератора (для воспроизводимости)",
    )

    parser.add_argument(
        "--font-size",
        type=int,
        default=None,
        help="размер шрифта в пикселях (автоматически определяется по умолчанию)",
    )

    parser.add_argument(
        "-i",
        "--info-file",
        type=str,
        default=None,
        help="путь к информационному файлу (по умолчанию: <output_dir>/image_info.log)",
    )

    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="автоматически подтверждать все запросы (не спрашивать подтверждение)",
    )

    args = parser.parse_args()

    # Проверяем, существует ли директория
    if os.path.exists(args.output_dir) and os.listdir(args.output_dir):
        if args.yes:
            response = "y"
        else:
            response = input(
                f"Директория '{args.output_dir}' не пуста. Перезаписать? [y/N]: "
            )
        if response.lower() != "y":
            print("Отменено пользователем.")
            return

    # Генерируем изображения
    generate_test_images(
        num_images=args.num_images,
        output_dir=args.output_dir,
        size=args.size,
        seed=args.seed,
        font_size=args.font_size,
        info_file=args.info_file,
        yes=args.yes,
    )


if __name__ == "__main__":
    main()

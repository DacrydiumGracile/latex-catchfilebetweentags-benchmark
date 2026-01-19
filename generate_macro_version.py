# generate_macro_version.py
import os
import argparse
import shutil
import sys
from lipsum import paragraphs


def copy_required_images(src_dir, dst_dir, num_images):
    """
    Копирует необходимое количество изображений.

    Args:
        src_dir: исходная директория с изображениями
        dst_dir: целевая директория
        num_images: необходимое количество изображений

    Returns:
        bool: True если успешно, False если ошибка
    """
    # Создаем целевую директорию
    os.makedirs(dst_dir, exist_ok=True)

    print(f"Копирование {num_images} изображений...")

    for i in range(1, num_images + 1):
        image_name = f"test-image-{i}.png"
        src_path = os.path.join(src_dir, image_name)
        dst_path = os.path.join(dst_dir, image_name)

        # Проверяем существование файла
        if not os.path.exists(src_path):
            print(f"Ошибка: Не найден файл {image_name}")
            print(f"   Требуется: {num_images}, найдено: {i-1}")
            return False

        # Копируем файл
        try:
            shutil.copy2(src_path, dst_path)
        except Exception as e:
            print(f"Ошибка при копировании {image_name}: {e}")
            return False

    print(f"Успешно скопировано {num_images} изображений")
    return True


def generate_macro_tex(images_dir, output_dir, num_blocks, output_tex):
    """
    Генерирует версию LaTeX-документа с макросами \\def вместо catchfilebetweentags.

    Args:
        images_dir: путь к папке с изображениями
        output_dir: выходная директория
        num_blocks: количество блоков (и изображений)
        output_tex: путь к выходному .tex файлу

    Returns:
        tuple: Возвращаем пути до файлов: output_tex, des_path, data_path
    """
    # Определяем путь к выходному .tex файлу
    if output_tex is None:
        output_tex = os.path.join(output_dir, "main.tex")

    # Проверяем и создаем структуру папок
    os.makedirs(output_dir, exist_ok=True)

    # Создаем подпапку для изображений в выходной директории
    images_dest = os.path.join(output_dir, "images")

    # Копируем только необходимое количество изображений
    if not copy_required_images(images_dir, images_dest, num_blocks):
        print("Не удалось скопировать изображения. Завершение работы.")
        sys.exit(1)

    # Генерируем des.tex с макросами
    des_content = ""
    for i in range(1, num_blocks + 1):
        lipsum_idx = (i % 5) + 1
        paragraph_idx = (lipsum_idx - 1) % len(paragraphs)
        des_content += f"""\\@namedef{{desDes{i}}}{{%
{paragraphs[paragraph_idx]}%
}}

"""

    des_path = os.path.join(output_dir, "des.tex")
    with open(des_path, "w", encoding="utf-8") as f:
        f.write(des_content)

    # Генерируем data.tex с макросами
    data_content = ""
    for i in range(1, num_blocks + 1):
        lipsum_idx = (i % 5) + 2  # Используем следующий параграф
        paragraph_idx = (lipsum_idx - 1) % len(paragraphs)
        data_content += f"""\\@namedef{{dataData{i}}}{{%
{paragraphs[paragraph_idx]}%
}}

"""

    data_path = os.path.join(output_dir, "data.tex")
    with open(data_path, "w", encoding="utf-8") as f:
        f.write(data_content)

    # Генерируем основной LaTeX файл
    tex_content = r"""\documentclass[a4paper]{report}
\usepackage{graphicx}
\usepackage{geometry}
\usepackage{float}
\usepackage[language=english]{lipsum}
\usepackage{etoolbox}
\usepackage{l3benchmark}

\makeatletter
\newcommand{\fig}[1]{\begin{figure}[H]\includegraphics{#1}\end{figure}}
\newcommand{\merge}[4]{\par\textbf{#1}\par\fig{#2}\@nameuse{#3}\par\@nameuse{#4}\par}
\makeatother
% See
% https://tex.stackexchange.com/questions/505770/how-to-measure-the-compilation-time-of-a-document
\ExplSyntaxOn
\AfterEndDocument { \benchmark_toc: }
\use:n
  {
    \benchmark_tic:
  }
\ExplSyntaxOff
\begin{document}
\makeatletter
% Загружаем все макросы из внешних файлов
\input{des.tex}
\input{data.tex}
\makeatother
"""

    # Добавляем блоки
    for i in range(1, num_blocks + 1):
        block_num = f"Block {i}"
        image_name = f"test-image-{i}.png"
        image_path = f"images/{image_name}"
        tag_num = f"{i}"

        # Используем прямые вызовы макросов
        tex_content += f"\n\\merge{{{block_num}}}{{{image_path}}}{{desDes{tag_num}}}{{dataData{tag_num}}}\n"

    tex_content += r"""
\end{document}
"""

    # Сохраняем основной файл
    try:
        with open(output_tex, "w", encoding="utf-8") as f:
            f.write(tex_content)
    except Exception as e:
        print(f"Ошибка при сохранении файла {output_tex}: {e}")
        sys.exit(1)

    return output_tex, des_path, data_path


def main():
    parser = argparse.ArgumentParser(
        description="Генерация версии LaTeX-документа с макросами \\def вместо catchfilebetweentags",
        epilog="""
Примеры использования:
  %(prog)s --images-dir images --num-blocks 50
  %(prog)s -i images -n 100 -o macro_version
  %(prog)s -i images -n 30 -t my_macro_document.tex
        """,
    )

    parser.add_argument(
        "-i",
        "--images-dir",
        type=str,
        default="images",
        help="путь к папке с сгенерированными изображениями (по умолчанию: images)",
    )

    parser.add_argument(
        "-n",
        "--num-blocks",
        type=int,
        default=50,
        help="количество блоков/изображений для использования (по умолчанию: 50)",
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="macrodef",
        help="выходная директория (по умолчанию: macrodef)",
    )

    parser.add_argument(
        "-t",
        "--output-tex",
        type=str,
        default=None,
        help="путь к выходному .tex файлу (по умолчанию: <output_dir>/main.tex)",
    )

    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="автоматически подтверждать все запросы",
    )

    args = parser.parse_args()

    # Проверяем корректность количества блоков
    if args.num_blocks <= 0:
        print("Ошибка: Количество блоков должно быть положительным числом")
        sys.exit(1)

    # Проверяем существование директории с изображениями
    if not os.path.exists(args.images_dir):
        print(f"Ошибка: Директория с изображениями '{args.images_dir}' не существует")
        sys.exit(1)

    # Проверяем, существует ли выходная директория и не пуста ли она
    if os.path.exists(args.output_dir) and os.listdir(args.output_dir):
        # Если флаг -y установлен, автоматически подтверждаем
        if args.yes:
            response = "y"
        else:
            response = input(
                f"Директория '{args.output_dir}' не пуста. Перезаписать? [y/N]: "
            )
        if response.lower() != "y":
            print("Отменено пользователем.")
            sys.exit(0)

    print(f"Генерация версии документа с макросами:")
    print(f"  Папка с изображениями: {args.images_dir}")
    print(f"  Выходная директория: {args.output_dir}")
    print(f"  Используются макросы \\def вместо catchfilebetweentags")

    # Генерируем документ
    main_tex_path, des_tex_path, data_tex_path = generate_macro_tex(
        images_dir=args.images_dir,
        output_dir=args.output_dir,
        num_blocks=args.num_blocks,
        output_tex=args.output_tex,
    )

    print(f"\nВерсия с макросами успешно сгенерирована!")
    print(f"  Основной файл: {main_tex_path}")
    print(f"  Файл описаний: {des_tex_path}")
    print(f"  Файл данных: {data_tex_path}")
    print(f"  Изображения скопированы в: {os.path.join(args.output_dir, 'images')}")
    print(f"  Всего блоков: {args.num_blocks}")


if __name__ == "__main__":
    main()

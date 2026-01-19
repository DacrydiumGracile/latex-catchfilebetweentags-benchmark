# generate_flat_version.py
import os
import argparse
import shutil
import sys


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
            # if i % 20 == 0:
            #     print(f"  Скопировано {i}/{num_images} изображений...")
        except Exception as e:
            print(f"Ошибка при копировании {image_name}: {e}")
            return False

    print(f"Успешно скопировано {num_images} изображений")
    return True


def generate_flat_tex(images_dir, output_dir, num_blocks, output_tex, inner):
    """
    Генерирует плоскую версию LaTeX-документа.

    Args:
        images_dir: путь к папке с изображениями
        output_dir: выходная директория
        num_blocks: количество блоков (и изображений)
        output_tex: путь к выходному .tex файлу
        inner: если True, вставляет непосредственно текст вместо команды \\lipsum
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

    # Генерируем основной LaTeX файл
    tex_content = r"""\documentclass[a4paper]{report}
\usepackage{graphicx}
\usepackage{geometry}
\usepackage{float}
\usepackage[language=english]{lipsum}
\usepackage{etoolbox}
\usepackage{l3benchmark}

\newcommand{\fig}[1]{\begin{figure}[H]\includegraphics{#1}\end{figure}}
\newcommand{\merge}[4]{\par\textbf{#1}\par\fig{#2}#3\par#4\par}
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

"""
    # Импортируем paragraphs для режима inner
    if inner:
        from lipsum import paragraphs

    # Добавляем блоки
    for i in range(1, num_blocks + 1):
        block_num = f"Block {i}"
        image_path = f"images/test-image-{i}.png"

        # Используем разные параграфы lipsum для разнообразия
        lipsum_idx = (i % 5) + 1  # Берем параграфы 1-5 по кругу

        if inner:
            # Вставляем непосредственно текст
            des_idx = (lipsum_idx - 1) % len(paragraphs)
            data_idx = (lipsum_idx) % len(paragraphs)

            des_text = paragraphs[des_idx]
            data_text = paragraphs[data_idx]

            tex_content += f"""
\\merge{{{block_num}}}{{{image_path}}}{{%
{des_text}%
}}{{%
{data_text}%
}}
"""
        else:
            # Используем команду \lipsum
            tex_content += f"\n\\merge{{{block_num}}}{{{image_path}}}{{\\lipsum[{lipsum_idx}]}}{{\\lipsum[{lipsum_idx+1}]}}\n"

    tex_content += r"""
\end{document}
"""

    # Сохраняем файл
    output_path = os.path.join(output_dir, "main.tex")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(tex_content)

    print(f"\nПлоская версия успешно сгенерирована в '{output_dir}'")
    print(f"  Количество блоков: {num_blocks}")
    print(
        f"  Режим: {'inner (непосредственный текст)' if inner else 'обычный (команда \\lipsum)'}"
    )
    print(f"  Основной файл: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Генерация плоской версии LaTeX-документа для тестирования производительности",
        epilog="""
Примеры использования:
  %(prog)s --images-dir images --num-blocks 50
  %(prog)s -i images -n 100 -o flat_version
  %(prog)s -i images -n 30 -t my_document.tex
  %(prog)s -i images -n 50 --inner
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
        default="flat",
        help="выходная директория (по умолчанию: flat)",
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

    parser.add_argument(
        "--inner",
        action="store_true",
        help="использовать непосредственно текст вместо команды \\lipsum",
    )

    args = parser.parse_args()

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

    print(f"Генерация плоской версии документа:")
    print(f"  Папка с изображениями: {args.images_dir}")
    print(f"  Количество блоков: {args.num_blocks}")
    print(f"  Выходная директория: {args.output_dir}")
    if args.inner:
        print(f"  Режим: inner (непосредственный текст вместо \\lipsum)")
    else:
        print(f"  Режим: обычный (команда \\lipsum)")

    # Генерируем документ
    generate_flat_tex(
        images_dir=args.images_dir,
        output_dir=args.output_dir,
        num_blocks=args.num_blocks,
        output_tex=args.output_tex,
        inner=args.inner,
    )


if __name__ == "__main__":
    main()

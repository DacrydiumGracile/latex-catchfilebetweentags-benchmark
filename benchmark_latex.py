# benchmark_latex.py
import os
import sys
import csv
import subprocess
import time
import re
import argparse
import shutil
from pathlib import Path
from statistics import mean


def run_generate_document(n, images_dir, base_output_dir, doc_type, yes=False):
    """
    Генерирует документ указанного типа с N блоками.

    Args:
        n: количество блоков
        images_dir: путь к папке с изображениями
        base_output_dir: базовая выходная директория
        doc_type: тип документа ('flat', 'flat_inner', 'modular', 'modular_inner', 'modular_inner_last', 'macrodef')
        yes: автоматическое подтверждение

    Returns:
        Path: путь к сгенерированной директории
    """
    # Определяем имя подпапки и команду генерации
    if doc_type == "flat":
        output_subdir = f"flat_{n}"
        generator_script = "generate_flat_version.py"
        cmd = [
            sys.executable,
            generator_script,
            "-i",
            str(images_dir),
            "-n",
            str(n),
            "-o",
            str(Path(base_output_dir) / output_subdir),
        ]
    elif doc_type == "flat_inner":
        output_subdir = f"flat_inner_{n}"
        generator_script = "generate_flat_version.py"
        cmd = [
            sys.executable,
            generator_script,
            "-i",
            str(images_dir),
            "-n",
            str(n),
            "-o",
            str(Path(base_output_dir) / output_subdir),
            "--inner",
        ]
    elif doc_type == "modular":
        output_subdir = f"modular_{n}"
        generator_script = "generate_modular_version.py"
        cmd = [
            sys.executable,
            generator_script,
            "-i",
            str(images_dir),
            "-n",
            str(n),
            "-o",
            str(Path(base_output_dir) / output_subdir),
        ]
    elif doc_type == "modular_inner":
        output_subdir = f"modular_inner_{n}"
        generator_script = "generate_modular_version.py"
        cmd = [
            sys.executable,
            generator_script,
            "-i",
            str(images_dir),
            "-n",
            str(n),
            "-o",
            str(Path(base_output_dir) / output_subdir),
            "--inner",
        ]
    elif doc_type == "modular_inner_last":
        output_subdir = f"modular_inner_last_{n}"
        generator_script = "generate_modular_version.py"
        cmd = [
            sys.executable,
            generator_script,
            "-i",
            str(images_dir),
            "-n",
            str(n),
            "-o",
            str(Path(base_output_dir) / output_subdir),
            "--inner",
            "--last-tag",
        ]
    elif doc_type == "macrodef":
        output_subdir = f"macrodef_{n}"
        generator_script = "generate_macro_version.py"
        cmd = [
            sys.executable,
            generator_script,
            "-i",
            str(images_dir),
            "-n",
            str(n),
            "-o",
            str(Path(base_output_dir) / output_subdir),
        ]
    else:
        raise ValueError(f"Неизвестный тип документа: {doc_type}")

    output_dir = Path(base_output_dir) / output_subdir

    # Удаляем старую директорию если существует
    if output_dir.exists():
        shutil.rmtree(output_dir)

    if yes:
        cmd.append("-y")

    print(f"\n{'='*60}")
    print(f"Генерация {doc_type} версии с N={n}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print(f"stderr: {result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при генерации документа: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return None

    return output_dir


def run_pdflatex_k_times(output_dir, k, latex_cmd="pdflatex"):
    """
    Запускает pdflatex K раз и собирает данные о времени.

    Args:
        output_dir: директория с .tex файлом
        k: количество запусков
        latex_cmd: команда LaTeX (pdflatex, lualatex, xelatex)

    Returns:
        tuple: (список time результатов, список benchmark результатов)
    """
    main_tex = output_dir / "main.tex"

    if not main_tex.exists():
        print(f"Файл {main_tex} не найден")
        return [], []

    time_results = []
    benchmark_results = []

    print(f"Запуск компиляции {k} раз...")

    for i in range(1, k + 1):
        print(f"\nЗапуск {i}/{k}...")

        # Формируем команду pdflatex
        pdflatex_cmd = [
            "time",
            "-p",
            latex_cmd,
            "-interaction=nonstopmode",
            "-output-directory",
            str(output_dir),
            str(main_tex),
        ]

        try:
            # Запускаем команду и захватываем вывод
            process = subprocess.run(
                " ".join(pdflatex_cmd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300,  # 5 минут таймаут на компиляцию
                shell=True,
                executable="/bin/bash",
            )

            # Используем замер времени из Python
            time_output = process.stderr
            real_time_match = re.search(r"real\s+(\d+\.?\d+)", time_output)

            if real_time_match:
                time_real = float(real_time_match.group(1))
                time_results.append(time_real)
                print(f"  time (real): {time_real:.2f} сек")
            else:
                print(f"Не найдено 'time (real)' время")
                time_results.append(None)

            # Парсим лог-файл для benchmark времени
            log_file = output_dir / "main.log"
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    log_content = f.read()

                # Ищем строку с (l3benchmark) + TOC:
                benchmark_match = re.search(
                    r"\(l3benchmark\) \+ TOC:\s+(\d+\.?\d+)\s+s", log_content
                )

                if benchmark_match:
                    benchmark_time = float(benchmark_match.group(1))
                    benchmark_results.append(benchmark_time)
                    print(f"  l3benchmark: {benchmark_time:.2f} сек")
                else:
                    print(f"  Не найдено l3benchmark время в лог-файле")
                    benchmark_results.append(None)
            else:
                print(f"  Лог-файл не найден: {log_file}")
                benchmark_results.append(None)

        except subprocess.TimeoutExpired:
            print(f"  Таймаут компиляции (более 5 минут)")
            time_results.append(None)
            benchmark_results.append(None)
        except Exception as e:
            print(f"  Ошибка при выполнении pdflatex: {e}")
            time_results.append(None)
            benchmark_results.append(None)

    return time_results, benchmark_results


def calculate_statistics(values):
    """
    Вычисляет статистику для списка значений.

    Args:
        values: список числовых значений

    Returns:
        dict: статистика (среднее, минимум, максимум)
    """
    # Фильтруем None значения
    filtered_values = [v for v in values if v is not None]

    if not filtered_values:
        return {"mean": None, "min": None, "max": None, "count": 0}

    return {
        "mean": mean(filtered_values),
        "min": min(filtered_values),
        "max": max(filtered_values),
        "count": len(filtered_values),
    }


def save_results_to_csv(results, output_csv, k, doc_type):
    """
    Сохраняет результаты в CSV файл.

    Args:
        results: список результатов для каждого N
        output_csv: путь к CSV файлу
        k: количество запусков
        doc_type: тип документа
    """
    # Создаем заголовок CSV
    headers = ["N", "doc_type"]

    # Добавляем столбцы для time результатов
    for i in range(1, k + 1):
        headers.append(f"time_run_{i}")

    # Добавляем столбцы для benchmark результатов
    for i in range(1, k + 1):
        headers.append(f"benchmark_run_{i}")

    # Добавляем статистику
    headers.extend(
        [
            "time_mean",
            "time_min",
            "time_max",
            "benchmark_mean",
            "benchmark_min",
            "benchmark_max",
            "time_count",
            "benchmark_count",
        ]
    )

    # Создаем данные для CSV
    rows = []
    for result in results:
        n = result["N"]
        time_vals = result["time_values"]
        benchmark_vals = result["benchmark_values"]
        time_stats = result["time_stats"]
        benchmark_stats = result["benchmark_stats"]

        # Создаем строку с данными
        row = [n, doc_type]

        # Добавляем time значения (заполняем None если недостаточно)
        for i in range(k):
            if i < len(time_vals):
                row.append(time_vals[i])
            else:
                row.append(None)

        # Добавляем benchmark значения
        for i in range(k):
            if i < len(benchmark_vals):
                row.append(benchmark_vals[i])
            else:
                row.append(None)

        # Добавляем статистику
        row.extend(
            [
                time_stats["mean"],
                time_stats["min"],
                time_stats["max"],
                benchmark_stats["mean"],
                benchmark_stats["min"],
                benchmark_stats["max"],
                time_stats["count"],
                benchmark_stats["count"],
            ]
        )

        rows.append(row)

    # Записываем в CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"\n✓ Результаты сохранены в {output_csv}")


def main():
    parser = argparse.ArgumentParser(
        description="Тестирование производительности компиляции LaTeX-документов",
        epilog="""
Примеры использования:
  python benchmark_latex.py 
  python benchmark_latex.py -t modular -i images -k 5 -o results_modular.csv
  python benchmark_latex.py -t modular_inner -i images -k 3 -o results_inner.csv
  python benchmark_latex.py -t modular_inner_last -i images -k 3 -o results_inner_last.csv
  python benchmark_latex.py -t all -i images -k 3 -o results_all.csv
        """,
    )

    parser.add_argument(
        "-t",
        "--type",
        type=str,
        choices=[
            "flat",
            "flat_inner",
            "modular",
            "modular_inner",
            "modular_inner_last",
            "macrodef",
            "all",
        ],
        default="flat",
        help="тип документа для тестирования (flat, modular, modular_inner, modular_inner_last, macrodef, all) (по умолчанию: flat)",
    )

    parser.add_argument(
        "-i",
        "--images-dir",
        type=str,
        default="images",
        help="путь к папке с изображениями (по умолчанию: images)",
    )

    parser.add_argument(
        "-k",
        "--runs",
        type=int,
        default=3,
        help="количество запусков компиляции для каждого N (по умолчанию: 3)",
    )

    parser.add_argument(
        "-o",
        "--output-csv",
        type=str,
        default="benchmark_results.csv",
        help="выходной CSV файл (по умолчанию: benchmark_results.csv)",
    )

    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="автоматически подтверждать все запросы",
    )

    parser.add_argument(
        "--latex-cmd",
        type=str,
        default="pdflatex",
        help="команда LaTeX (по умолчанию: pdflatex)",
    )

    parser.add_argument(
        "--base-dir",
        type=str,
        default="experiment",
        help="базовая директория для тестов (по умолчанию: experiment)",
    )

    parser.add_argument(
        "--n-values",
        type=str,
        default="10,20,30,50,70,100,200,500,750,1000,1250,1500,1750,2000",
        help="значения N через запятую (по умолчанию: 10,20,30,50,70,100,200,500,750,1000,1250,1500,1750,2000)",
    )

    args = parser.parse_args()

    # Проверяем существование директории с изображениями
    if not os.path.exists(args.images_dir):
        print(f"Ошибка: Директория с изображениями '{args.images_dir}' не существует")
        sys.exit(1)

    # Проверяем существование скриптов генерации
    if args.type in ["flat", "flat_inner", "all"] and not os.path.exists(
        "generate_flat_version.py"
    ):
        print("Ошибка: Файл generate_flat_version.py не найден в текущей директории")
        sys.exit(1)

    if args.type in ["modular", "modular_inner", "all"] and not os.path.exists(
        "generate_modular_version.py"
    ):
        print("Ошибка: Файл generate_modular_version.py не найден в текущей директории")
        sys.exit(1)

    if args.type in ["macrodef", "all"] and not os.path.exists(
        "generate_macro_version.py"
    ):
        print("Ошибка: Файл generate_macro_version.py не найден в текущей директории")
        sys.exit(1)

    # Проверяем, существует ли директория
    output_csv_dir = os.path.dirname(args.output_csv)
    if not os.path.exists(output_csv_dir):
        os.makedirs(output_csv_dir, exist_ok=True)

    # Парсим значения N
    try:
        n_values = [int(n.strip()) for n in args.n_values.split(",")]
    except ValueError:
        print("Ошибка: Неверный формат --n-values. Используйте числа через запятую")
        sys.exit(1)

    # Определяем типы документов для тестирования
    if args.type == "all":
        doc_types = [
            "flat",
            "flat_inner",
            "modular",
            "modular_inner",
            "modular_inner_last",
            "macrodef",
        ]
    else:
        doc_types = [args.type]

    print(f"Тестирование производительности LaTeX-документов")
    print(f"{'='*60}")
    print(f"Тип(ы) документа: {', '.join(doc_types)}")
    print(f"Директория с изображениями: {args.images_dir}")
    print(f"Количество запусков для каждого N: {args.runs}")
    print(f"Команда LaTeX: {args.latex_cmd}")
    print(f"Базовая директория тестов: {args.base_dir}")
    print(f"Значения N: {n_values}")
    print(f"{'='*60}")

    for doc_type in doc_types:
        print(f"\n{'#'*60}")
        print(f"ТЕСТИРОВАНИЕ ТИПА: {doc_type}")
        print(f"{'#'*60}")

        # Создаем базовую директорию для этого типа
        base_dir = Path(args.base_dir) / doc_type
        base_dir.mkdir(parents=True, exist_ok=True)

        results = []

        for n in n_values:
            # Генерируем документ
            output_dir = run_generate_document(
                n, args.images_dir, base_dir, doc_type, args.yes
            )

            if output_dir is None:
                print(f"Пропускаем N={n} для {doc_type} из-за ошибки генерации")
                continue

            # Запускаем компиляцию K раз
            time_values, benchmark_values = run_pdflatex_k_times(
                output_dir, args.runs, args.latex_cmd
            )

            # Вычисляем статистику
            time_stats = calculate_statistics(time_values)
            benchmark_stats = calculate_statistics(benchmark_values)

            # Сохраняем результаты
            result = {
                "N": n,
                "time_values": time_values,
                "benchmark_values": benchmark_values,
                "time_stats": time_stats,
                "benchmark_stats": benchmark_stats,
            }

            results.append(result)

            # Выводим сводку для этого N
            print(f"\nСводка для {doc_type}, N={n}:")
            if time_stats["mean"] is not None:
                print(
                    f"  time среднее: {time_stats['mean']:.2f} сек "
                    f"(min: {time_stats['min']:.2f}, max: {time_stats['max']:.2f}, "
                    f"успешных: {time_stats['count']}/{args.runs})"
                )
            else:
                print(f"  time: нет успешных измерений")

            if benchmark_stats["mean"] is not None:
                print(
                    f"  benchmark среднее: {benchmark_stats['mean']:.2f} сек "
                    f"(min: {benchmark_stats['min']:.2f}, max: {benchmark_stats['max']:.2f}, "
                    f"успешных: {benchmark_stats['count']}/{args.runs})"
                )
            else:
                print(f"  benchmark: нет успешных измерений")

            # Очищаем промежуточные файлы (кроме логов для отладки)
            for ext in [".aux", ".out", ".toc"]:
                for file in output_dir.glob(f"*{ext}"):
                    try:
                        file.unlink()
                    except:
                        pass

        # Сохраняем результаты для этого типа в CSV
        if results:
            if args.type == "all":
                csv_filename = f"{args.output_csv.replace('.csv', f'_{doc_type}.csv')}"
            else:
                csv_filename = args.output_csv

            save_results_to_csv(results, csv_filename, args.runs, doc_type)

            # Выводим финальную сводку для этого типа
            print(f"\n{'='*60}")
            print(f"ФИНАЛЬНАЯ СВОДКА ДЛЯ {doc_type}")
            print(f"{'='*60}")

            for result in results:
                n = result["N"]
                time_mean = result["time_stats"]["mean"]
                benchmark_mean = result["benchmark_stats"]["mean"]

                if time_mean is not None and benchmark_mean is not None:
                    print(
                        f"N={n:4d}: time={time_mean:6.2f}с, benchmark={benchmark_mean:6.2f}с"
                    )
                elif time_mean is not None:
                    print(f"N={n:4d}: time={time_mean:6.2f}с, benchmark=нет данных")
                elif benchmark_mean is not None:
                    print(
                        f"N={n:4d}: time=нет данных, benchmark={benchmark_mean:6.2f}с"
                    )
        else:
            print(f"Нет результатов для типа {doc_type}")


if __name__ == "__main__":
    main()

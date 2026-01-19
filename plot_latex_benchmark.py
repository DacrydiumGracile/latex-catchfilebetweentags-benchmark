# plot_latex_benchmark.py
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os
import sys
from pathlib import Path
from itertools import cycle

bright_colors = [
    "#FF0000",  # Красный
    "#006400",  # Зеленый
    "#0000FF",  # Синий
    "#FF9900",  # Оранжевый
    "#9900FF",  # Фиолетовый
    "#00FFFF",  # Голубой
    "#FF00FF",  # Розовый
    "#FFFF00",  # Желтый
    "#00FF99",  # Морской волны
    "#FF6600",  # Темно-оранжевый
    "#0066FF",  # Ярко-синий
    "#6600FF",  # Индиго
    "#FF0066",  # Ярко-розовый
    "#66FF00",  # Лаймовый
    "#FF33CC",  # Фуксия
]

markers = [
    "o",
    "s",
    "^",
    "D",
    "v",
    "<",
    ">",
    "p",
    "*",
    "h",
    "H",
    "+",
    "x",
    "d",
    "|",
]


def load_and_validate_data(input_csvs):
    """
    Загружает и валидирует данные из CSV файлов.

    Args:
        input_csvs: список путей к CSV файлам

    Returns:
        DataFrame: объединенные и валидированные данные
    """
    all_data = []

    for csv_file in input_csvs:
        try:
            df = pd.read_csv(csv_file)
            # Проверяем обязательные колонки
            required_cols = ["N", "doc_type", "time_mean", "benchmark_mean"]
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                print(
                    f" Ошибка: В файле {csv_file} отсутствуют колонки: {missing_cols}"
                )
                continue

            # Проверяем наличие статистических колонок, если нет - создаем
            if "time_min" not in df.columns and "time_max" not in df.columns:
                # Ищем колонки с отдельными запусками
                time_run_cols = [
                    col for col in df.columns if col.startswith("time_run_")
                ]
                if time_run_cols:
                    # Вычисляем min/max из отдельных запусков
                    df["time_min"] = df[time_run_cols].min(axis=1)
                    df["time_max"] = df[time_run_cols].max(axis=1)
                else:
                    # Если нет отдельных запусков, используем mean как min/max
                    df["time_min"] = df["time_mean"]
                    df["time_max"] = df["time_mean"]

            if "benchmark_min" not in df.columns and "benchmark_max" not in df.columns:
                benchmark_run_cols = [
                    col for col in df.columns if col.startswith("benchmark_run_")
                ]
                if benchmark_run_cols:
                    df["benchmark_min"] = df[benchmark_run_cols].min(axis=1)
                    df["benchmark_max"] = df[benchmark_run_cols].max(axis=1)
                else:
                    df["benchmark_min"] = df["benchmark_mean"]
                    df["benchmark_max"] = df["benchmark_mean"]

            df["source_file"] = csv_file
            all_data.append(df)
            print(f"Загружен {csv_file} ({len(df)} строк)")

        except Exception as e:
            print(f" Ошибка при загрузке {csv_file}: {e}")

    if not all_data:
        print(" Не удалось загрузить данные из CSV файлов")
        sys.exit(1)

    # Объединяем все данные
    combined_df = pd.concat(all_data, ignore_index=True)

    # Проверяем дубликаты (N, doc_type)
    duplicates = combined_df.duplicated(subset=["N", "doc_type"], keep=False)
    if duplicates.any():
        duplicate_rows = combined_df[duplicates].sort_values(["doc_type", "N"])
        print(f"\n Найдены дублирующиеся записи с одинаковыми N и doc_type:")
        for _, row in duplicate_rows.iterrows():
            print(
                f"   N={row['N']}, doc_type={row['doc_type']}, source={row.get('source_file', 'N/A')}"
            )
        print(
            "\nУдалите дублирующиеся записи или объедините их перед построением графиков."
        )
        sys.exit(1)

    return combined_df


def plot_time_vs_n_for_each_type(df, output_dir, dpi=150, max_n=None, english=False):
    """
    График 1: Для каждого типа - время компиляции (time и l3benchmark) в зависимости от N.

    Args:
        df: DataFrame с данными
        output_dir: директория для сохранения
        dpi: разрешение
        max_n: максимальное значение N для отображения
        english: использовать английские подписи
    """
    doc_types = df["doc_type"].unique()

    for doc_type in doc_types:
        df_type = df[df["doc_type"] == doc_type].sort_values("N")

        # Фильтруем по max_n если задано
        if max_n is not None:
            df_type = df_type[df_type["N"] <= max_n]

        if len(df_type) == 0:
            continue

        plt.figure(figsize=(10, 6))

        # Определяем язык подписей
        if english:
            file_prefix = "en_"
            xlabel = "Number of blocks (N)"
            ylabel = "Compilation time (seconds)"
            title = f"Compilation time vs N ({doc_type})"
            time_label = "time (mean)"
            time_minmax_label = "time (min-max)"
            benchmark_label = "l3benchmark (mean)"
            benchmark_minmax_label = "l3benchmark (min-max)"
        else:
            file_prefix = "ru_"
            xlabel = "Количество блоков (N)"
            ylabel = "Время компиляции (секунды)"
            title = f"Время компиляции в зависимости от N ({doc_type})"
            time_label = "time (среднее)"
            time_minmax_label = "time (min-max)"
            benchmark_label = "l3benchmark (среднее)"
            benchmark_minmax_label = "l3benchmark (min-max)"

        if max_n is not None:
            title += f" (N ≤ {max_n})"

        # TIME: среднее значение и область
        plt.plot(
            df_type["N"],
            df_type["time_mean"],
            "b-o",
            label=time_label,
            linewidth=2,
            markersize=6,
        )
        plt.fill_between(
            df_type["N"],
            df_type["time_min"],
            df_type["time_max"],
            alpha=0.2,
            color="blue",
            label=time_minmax_label,
        )

        # BENCHMARK: среднее значение и область
        plt.plot(
            df_type["N"],
            df_type["benchmark_mean"],
            "r-s",
            label=benchmark_label,
            linewidth=2,
            markersize=6,
        )
        plt.fill_between(
            df_type["N"],
            df_type["benchmark_min"],
            df_type["benchmark_max"],
            alpha=0.2,
            color="red",
            label=benchmark_minmax_label,
        )

        plt.xlabel(xlabel, fontsize=12)
        plt.ylabel(ylabel, fontsize=12)
        plt.title(title, fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=10)

        plt.tight_layout()
        filename = output_dir / f"{file_prefix}1_time_vs_n_{doc_type}.png"
        plt.savefig(filename, dpi=dpi, bbox_inches="tight")
        plt.close()

        print(f"✓ Сохранен график: {filename}")


def plot_mean_time_comparison(df, output_dir, dpi=150, max_n=None, english=False):
    """
    График 2: Линии со средним временем (time) для каждого типа.

    Args:
        df: DataFrame с данными
        output_dir: директория для сохранения
        dpi: разрешение
        max_n: максимальное значение N для отображения
        english: использовать английские подписи
    """
    plt.figure(figsize=(10, 6))

    doc_types = df["doc_type"].unique()

    # Используем циклы для цветов и маркеров
    color_cycle = cycle(bright_colors[: len(doc_types)])
    marker_cycle = cycle(markers)

    for doc_type in doc_types:
        df_type = df[df["doc_type"] == doc_type].sort_values("N")

        # Фильтруем по max_n если задано
        if max_n is not None:
            df_type = df_type[df_type["N"] <= max_n]

        if len(df_type) == 0:
            continue

        color = next(color_cycle)
        marker = next(marker_cycle)

        plt.plot(
            df_type["N"],
            df_type["time_mean"],
            marker=marker,
            linestyle="-",
            color=color,
            label=doc_type,
            linewidth=2,
            markersize=6,
            alpha=0.7,
        )

    # Определяем язык подписей
    if english:
        file_prefix = "en_"
        xlabel = "Number of blocks (N)"
        ylabel = "Mean compilation time (time, seconds)"
        title = "Comparison of mean compilation time (time) by document type"
    else:
        file_prefix = "ru_"
        xlabel = "Количество блоков (N)"
        ylabel = "Среднее время компиляции (time, секунды)"
        title = "Сравнение среднего времени компиляции (time) по типам документов"

    if max_n is not None:
        title += f" (N ≤ {max_n})"

    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.title(title, fontsize=14)
    plt.grid(True, alpha=0.3)

    # Настраиваем легенду в зависимости от количества типов
    if len(doc_types) > 4:
        plt.legend(fontsize=9, ncol=2, loc="upper left")
    else:
        plt.legend(fontsize=10)

    plt.tight_layout()
    filename = output_dir / f"{file_prefix}2_mean_time_comparison.png"
    plt.savefig(filename, dpi=dpi, bbox_inches="tight")
    plt.close()

    print(f"✓ Сохранен график: {filename}")


def plot_mean_benchmark_comparison(df, output_dir, dpi=150, max_n=None, english=False):
    """
    График 3: Линии со средним временем (l3benchmark) для каждого типа.

    Args:
        df: DataFrame с данными
        output_dir: директория для сохранения
        dpi: разрешение
        max_n: максимальное значение N для отображения
        english: использовать английские подписи
    """
    plt.figure(figsize=(10, 6))

    doc_types = df["doc_type"].unique()

    # Используем циклы для цветов и маркеров
    color_cycle = cycle(bright_colors[: len(doc_types)])
    marker_cycle = cycle(markers)

    for doc_type in doc_types:
        df_type = df[df["doc_type"] == doc_type].sort_values("N")

        # Фильтруем по max_n если задано
        if max_n is not None:
            df_type = df_type[df_type["N"] <= max_n]

        if len(df_type) == 0:
            continue

        color = next(color_cycle)
        marker = next(marker_cycle)

        plt.plot(
            df_type["N"],
            df_type["benchmark_mean"],
            marker=marker,
            linestyle="-",
            color=color,
            label=doc_type,
            linewidth=2,
            markersize=6,
            alpha=0.7,
        )

    # Определяем язык подписей
    if english:
        file_prefix = "en_"
        xlabel = "Number of blocks (N)"
        ylabel = "Mean compilation time (l3benchmark, seconds)"
        title = "Comparison of mean compilation time (l3benchmark) by document type"
    else:
        file_prefix = "ru_"
        xlabel = "Количество блоков (N)"
        ylabel = "Среднее время компиляции (l3benchmark, секунды)"
        title = (
            "Сравнение среднего времени компиляции (l3benchmark) по типам документов"
        )

    if max_n is not None:
        title += f" (N ≤ {max_n})"

    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.title(title, fontsize=14)
    plt.grid(True, alpha=0.3)

    # Настраиваем легенду в зависимости от количества типов
    if len(doc_types) > 4:
        plt.legend(fontsize=9, ncol=2, loc="upper left")
    else:
        plt.legend(fontsize=10)

    plt.tight_layout()
    filename = output_dir / f"{file_prefix}3_mean_benchmark_comparison.png"
    plt.savefig(filename, dpi=dpi, bbox_inches="tight")
    plt.close()

    print(f"✓ Сохранен график: {filename}")


def plot_difference_from_baseline(
    df, output_dir, baseline_type, dpi=150, max_n=None, english=False
):
    """
    График 4: Разность времени между типами документа и базовой линией (2x2).

    Верхний ряд: разность (слева - time, справа - benchmark)
    Нижний ряд: отношение времени (слева - time, справа - benchmark)

    Args:
        df: DataFrame с данными
        output_dir: директория для сохранения
        baseline_type: тип документа, используемый как базовая линия
        dpi: разрешение
        max_n: максимальное значение N для отображения
        english: использовать английские подписи
    """
    # Получаем данные для базовой линии
    df_baseline = df[df["doc_type"] == baseline_type].sort_values("N")

    # Фильтруем по max_n если задано
    if max_n is not None:
        df_baseline = df_baseline[df_baseline["N"] <= max_n]

    if len(df_baseline) == 0:
        print(f"⚠  Нет данных для {baseline_type}, пропускаем график разности")
        return

    # Создаем отдельный график для каждого небазового типа
    non_baseline_types = [t for t in df["doc_type"].unique() if t != baseline_type]

    for doc_type in non_baseline_types:
        df_type = df[df["doc_type"] == doc_type].sort_values("N")

        # Фильтруем по max_n если задано
        if max_n is not None:
            df_type = df_type[df_type["N"] <= max_n]

        if len(df_type) == 0:
            continue

        # Находим общие значения N
        common_n = sorted(set(df_baseline["N"]).intersection(set(df_type["N"])))

        if not common_n:
            print(
                f"⚠  Нет общих значений N для {baseline_type} и {doc_type}, пропускаем"
            )
            continue

        # Создаем DataFrame для разности (time)
        diff_time_data = []
        diff_benchmark_data = []

        for n in common_n:
            # TIME разность
            baseline_time = df_baseline[df_baseline["N"] == n]["time_mean"].values[0]
            type_time = df_type[df_type["N"] == n]["time_mean"].values[0]
            diff_absolute_time = type_time - baseline_time
            ratio_time = type_time / baseline_time if baseline_time > 0 else 1.0

            diff_time_data.append(
                {"N": n, "diff_absolute": diff_absolute_time, "ratio": ratio_time}
            )

            # BENCHMARK разность
            baseline_benchmark = df_baseline[df_baseline["N"] == n][
                "benchmark_mean"
            ].values[0]
            type_benchmark = df_type[df_type["N"] == n]["benchmark_mean"].values[0]
            diff_absolute_benchmark = type_benchmark - baseline_benchmark
            ratio_benchmark = (
                type_benchmark / baseline_benchmark if baseline_benchmark > 0 else 1.0
            )

            diff_benchmark_data.append(
                {
                    "N": n,
                    "diff_absolute": diff_absolute_benchmark,
                    "ratio": ratio_benchmark,
                }
            )

        diff_time_df = pd.DataFrame(diff_time_data)
        diff_benchmark_df = pd.DataFrame(diff_benchmark_data)

        # Определяем язык подписей
        if english:
            file_prefix = "en_"
            xlabel = "Number of blocks (N)"
            ylabel_diff = "Time difference (seconds)"
            ylabel_ratio = "Time ratio (times)"
            title_time_diff = f"Time difference (time): {doc_type} - {baseline_type}"
            title_benchmark_diff = (
                f"Time difference (l3benchmark): {doc_type} - {baseline_type}"
            )
            title_time_ratio = f"Time ratio (time): {doc_type} / {baseline_type}"
            title_benchmark_ratio = (
                f"Time ratio (l3benchmark): {doc_type} / {baseline_type}"
            )
        else:
            file_prefix = "ru_"
            xlabel = "Количество блоков (N)"
            ylabel_diff = "Разность времени (секунды)"
            ylabel_ratio = "Отношение времени (раз)"
            title_time_diff = f"Разность времени (time): {doc_type} - {baseline_type}"
            title_benchmark_diff = (
                f"Разность времени (l3benchmark): {doc_type} - {baseline_type}"
            )
            title_time_ratio = f"Отношение времени (time): {doc_type} / {baseline_type}"
            title_benchmark_ratio = (
                f"Отношение времени (l3benchmark): {doc_type} / {baseline_type}"
            )

        if max_n is not None:
            suffix = f" (N ≤ {max_n})"
            title_time_diff += suffix
            title_benchmark_diff += suffix
            title_time_ratio += suffix
            title_benchmark_ratio += suffix

        # Создаем фигуру с четырьмя подграфиками (2x2)
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

        # 1. Разность TIME (секунды)
        ax1.plot(
            diff_time_df["N"],
            diff_time_df["diff_absolute"],
            "b-o",
            linewidth=2,
            markersize=6,
        )
        ax1.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
        ax1.set_xlabel(xlabel, fontsize=11)
        ax1.set_ylabel(ylabel_diff, fontsize=11)
        ax1.set_title(title_time_diff, fontsize=12)
        ax1.grid(True, alpha=0.3)

        # 2. Разность BENCHMARK (секунды)
        ax2.plot(
            diff_benchmark_df["N"],
            diff_benchmark_df["diff_absolute"],
            "r-o",
            linewidth=2,
            markersize=6,
        )
        ax2.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
        ax2.set_xlabel(xlabel, fontsize=11)
        ax2.set_ylabel(ylabel_diff, fontsize=11)
        ax2.set_title(title_benchmark_diff, fontsize=12)
        ax2.grid(True, alpha=0.3)

        # 3. Отношение TIME (во сколько раз)
        ax3.plot(
            diff_time_df["N"], diff_time_df["ratio"], "b-o", linewidth=2, markersize=6
        )
        ax3.axhline(y=1.0, color="gray", linestyle="--", alpha=0.5)
        ax3.set_xlabel(xlabel, fontsize=11)
        ax3.set_ylabel(ylabel_ratio, fontsize=11)
        ax3.set_title(title_time_ratio, fontsize=12)
        ax3.grid(True, alpha=0.3)

        # Добавляем горизонтальные линии для ключевых коэффициентов
        for ratio_val, color, style in [
            (1.1, "green", "-"),
            (1.2, "orange", "-"),
            (1.5, "red", "-"),
        ]:
            ax3.axhline(
                y=ratio_val, color=color, linestyle=style, alpha=0.8, linewidth=0.8
            )

        # 4. Отношение BENCHMARK (во сколько раз)
        ax4.plot(
            diff_benchmark_df["N"],
            diff_benchmark_df["ratio"],
            "r-o",
            linewidth=2,
            markersize=6,
        )
        ax4.axhline(y=1.0, color="gray", linestyle="--", alpha=0.5)
        ax4.set_xlabel(xlabel, fontsize=11)
        ax4.set_ylabel(ylabel_ratio, fontsize=11)
        ax4.set_title(title_benchmark_ratio, fontsize=12)
        ax4.grid(True, alpha=0.3)

        # Добавляем горизонтальные линии для ключевых коэффициентов
        for ratio_val, color, style in [
            (1.1, "green", "-"),
            (1.2, "orange", "-"),
            (1.5, "red", "-"),
        ]:
            ax4.axhline(
                y=ratio_val, color=color, linestyle=style, alpha=0.8, linewidth=0.8
            )

        # Добавляем значения на все графики
        for i, (row_time, row_benchmark) in enumerate(
            zip(diff_time_df.iterrows(), diff_benchmark_df.iterrows())
        ):
            _, row_time = row_time
            _, row_benchmark = row_benchmark

            ratio_range_time = abs(
                diff_time_df["ratio"].max() - diff_time_df["ratio"].min()
            )

            if ratio_range_time < 0.1:
                y_offset_ratio_time = 0.005
            else:
                y_offset_ratio_time = max(ratio_range_time * 0.05, 0.005)
                y_offset_ratio_time = min(y_offset_ratio_time, 0.05)

            ratio_range_benchmark = abs(
                diff_benchmark_df["ratio"].max() - diff_benchmark_df["ratio"].min()
            )

            if ratio_range_benchmark < 0.1:
                y_offset_ratio_benchmark = 0.005
            else:
                y_offset_ratio_benchmark = max(ratio_range_benchmark * 0.05, 0.005)
                y_offset_ratio_benchmark = min(y_offset_ratio_benchmark, 0.05)

            # TIME: Разность
            if row_time["diff_absolute"] >= 0:
                va_abs_time = "bottom"
                offset_sign_time = 1
            else:
                va_abs_time = "top"
                offset_sign_time = -1

            ax1.text(
                row_time["N"],
                row_time["diff_absolute"],
                f'{row_time["diff_absolute"]:.3f}',
                ha="center",
                va=va_abs_time,
                fontsize=8,
                bbox=dict(
                    boxstyle="round,pad=0.2",
                    facecolor="white",
                    edgecolor="gray",
                    alpha=0.7,
                ),
            )

            # BENCHMARK: Разность
            if row_benchmark["diff_absolute"] >= 0:
                va_abs_benchmark = "bottom"
                offset_sign_benchmark = 1
            else:
                va_abs_benchmark = "top"
                offset_sign_benchmark = -1

            ax2.text(
                row_benchmark["N"],
                row_benchmark["diff_absolute"],
                f'{row_benchmark["diff_absolute"]:.3f}',
                ha="center",
                va=va_abs_benchmark,
                fontsize=8,
                bbox=dict(
                    boxstyle="round,pad=0.2",
                    facecolor="white",
                    edgecolor="gray",
                    alpha=0.7,
                ),
            )

            # TIME: Отношение времени
            ax3.text(
                row_time["N"],
                row_time["ratio"] + y_offset_ratio_time,
                f'{row_time["ratio"]:.3f}×',
                ha="center",
                va="bottom",
                fontsize=8,
                bbox=dict(
                    boxstyle="round,pad=0.2",
                    facecolor="white",
                    edgecolor="gray",
                    alpha=0.7,
                ),
            )

            # BENCHMARK: Отношение времени
            ax4.text(
                row_benchmark["N"],
                row_benchmark["ratio"] + y_offset_ratio_benchmark,
                f'{row_benchmark["ratio"]:.3f}×',
                ha="center",
                va="bottom",
                fontsize=8,
                bbox=dict(
                    boxstyle="round,pad=0.2",
                    facecolor="white",
                    edgecolor="gray",
                    alpha=0.7,
                ),
            )

        plt.tight_layout()
        filename = (
            output_dir / f"{file_prefix}4_difference_{doc_type}_vs_{baseline_type}.png"
        )
        plt.savefig(filename, dpi=dpi, bbox_inches="tight")
        plt.close()

        print(f"✓ Сохранен график: {filename}")


def create_summary_csv(df, output_dir):
    """
    Создает сводный CSV файл с ключевой статистикой.

    Args:
        df: DataFrame с данными
        output_dir: директория для сохранения
    """
    summary_data = []

    for doc_type in df["doc_type"].unique():
        df_type = df[df["doc_type"] == doc_type].sort_values("N")

        for _, row in df_type.iterrows():
            summary_data.append(
                {
                    "N": row["N"],
                    "doc_type": row["doc_type"],
                    "time_mean": row["time_mean"],
                    "time_min": row.get("time_min", row["time_mean"]),
                    "time_max": row.get("time_max", row["time_mean"]),
                    "benchmark_mean": row["benchmark_mean"],
                    "benchmark_min": row.get("benchmark_min", row["benchmark_mean"]),
                    "benchmark_max": row.get("benchmark_max", row["benchmark_mean"]),
                }
            )

    summary_df = pd.DataFrame(summary_data)
    summary_csv = output_dir / "summary_statistics.csv"
    summary_df.to_csv(summary_csv, index=False, encoding="utf-8")

    print(f"\n✓ Сводная статистика сохранена в: {summary_csv}")

    return summary_df


def main():
    parser = argparse.ArgumentParser(
        description="Построение графиков по результатам тестирования производительности LaTeX",
        epilog="""
Примеры использования:
  # Для одного CSV файла (результат --type all) с flat как базовой линией
  python plot_latex_benchmark.py --input-csv results_all.csv --output-dir plots
  
  # Для нескольких CSV файлов с указанием базовой линии
  python plot_latex_benchmark.py --input-csv results_flat.csv --input-csv results_modular.csv --input-csv results_modular_inner.csv --baseline flat --output-dir plots
  
  # Использование modular_inner как базовой линии
  python plot_latex_benchmark.py --input-csv results_all.csv --baseline modular_inner --output-dir plots
  
  # С ограничением по N (только до 100 блоков)
  python plot_latex_benchmark.py --input-csv results_all.csv --max-n 100 --output-dir plots_100
  
  # С высоким разрешением
  python plot_latex_benchmark.py --input-csv results_all.csv --output-dir high_res_plots --dpi 300
        """,
    )

    parser.add_argument(
        "--input-csv",
        type=str,
        required=True,
        action="append",
        help="путь к CSV файлу с результатами (можно указать несколько раз)",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="plots",
        help="директория для сохранения графиков (по умолчанию: plots)",
    )

    parser.add_argument(
        "--baseline",
        type=str,
        default="flat",
        help="тип документа, используемый как базовая линия для сравнения (по умолчанию: flat)",
    )

    parser.add_argument(
        "--max-n",
        type=int,
        default=None,
        help="максимальное значение N для построения графиков (по умолчанию: все данные)",
    )

    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="разрешение графиков в DPI (по умолчанию: 150)",
    )

    parser.add_argument(
        "-E",
        "--english",
        action="store_true",
        help="использовать английские подписи на графиках (по умолчанию: русские)",
    )

    args = parser.parse_args()

    # Создаем выходную директорию
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"{'='*60}")
    print(f"Построение графиков по результатам тестирования")
    print(f"{'='*60}")
    print(f"Входные файлы: {args.input_csv}")
    print(f"Выходная директория: {output_dir}")
    print(f"Базовая линия: {args.baseline}")
    print(f"Максимальное N: {args.max_n if args.max_n else 'все данные'}")
    print(f"Разрешение: {args.dpi} DPI")
    print(f"Язык подписей: {'английский' if args.english else 'русский'}")

    # Загружаем и валидируем данные
    df = load_and_validate_data(args.input_csv)

    # Фильтруем данные по max_n если задано
    if args.max_n is not None:
        df = df[df["N"] <= args.max_n]
        print(f"\nДанные отфильтрованы: N ≤ {args.max_n}")
        print(f"  Осталось строк: {len(df)}")

    print(f"\nЗагружено данных:")
    print(f"  Всего строк: {len(df)}")
    print(f"  Типы документов: {', '.join(df['doc_type'].unique())}")
    print(f"  Диапазон N: {df['N'].min()} - {df['N'].max()}")

    # Проверяем, что базовая линия существует в данных
    if args.baseline not in df["doc_type"].unique():
        print(
            f"\n Ошибка: Указанная базовая линия '{args.baseline}' не найдена в данных"
        )
        print(f"   Доступные типы: {', '.join(df['doc_type'].unique())}")
        sys.exit(1)

    # Создаем сводную статистику
    summary_df = create_summary_csv(df, output_dir)

    # Строим графики
    print(f"\n{'='*60}")
    print("Построение графиков...")
    print(f"{'='*60}")

    # 1. Графики для каждого типа (time и benchmark)
    plot_time_vs_n_for_each_type(df, output_dir, args.dpi, args.max_n, args.english)

    # 2. Сравнение среднего времени (time) для всех типов
    plot_mean_time_comparison(df, output_dir, args.dpi, args.max_n, args.english)

    # 3. Сравнение среднего времени (benchmark) для всех типов
    plot_mean_benchmark_comparison(df, output_dir, args.dpi, args.max_n, args.english)

    # 4. Графики разности для небазовых типов (2x2: time и benchmark)
    plot_difference_from_baseline(
        df, output_dir, args.baseline, args.dpi, args.max_n, args.english
    )

    # Дополнительно: сводная таблица с максимальными различиями
    if args.baseline in df["doc_type"].values and len(df["doc_type"].unique()) > 1:
        print(f"\n{'='*60}")
        if args.english:
            print(f"SUMMARY COMPARED TO BASELINE ({args.baseline.upper()}):")
        else:
            print(f"СВОДКА ПО ОТНОШЕНИЮ К БАЗОВОЙ ЛИНИИ ({args.baseline.upper()}):")
        print(f"{'='*60}")

        baseline_data = df[df["doc_type"] == args.baseline].set_index("N")

        for doc_type in df["doc_type"].unique():
            if doc_type == args.baseline:
                continue

            type_data = df[df["doc_type"] == doc_type].set_index("N")

            # Находим общие N
            common_n = baseline_data.index.intersection(type_data.index)

            if len(common_n) > 0:
                if args.english:
                    print(f"\n{doc_type.upper()}:")
                    print(f"  TIME:")
                else:
                    print(f"\n{doc_type.upper()}:")
                    print(f"  TIME:")
                for n in sorted(common_n):
                    baseline_time = baseline_data.loc[n, "time_mean"]
                    type_time = type_data.loc[n, "time_mean"]
                    diff = type_time - baseline_time
                    diff_pct = (diff / baseline_time * 100) if baseline_time > 0 else 0

                    if diff > 0:
                        if args.english:
                            print(
                                f"    N={n}: {args.baseline}={baseline_time:.2f}s, {doc_type}={type_time:.2f}s, "
                                f"slower={diff:.2f}s ({diff_pct:.1f}%)"
                            )
                        else:
                            print(
                                f"    N={n}: {args.baseline}={baseline_time:.2f}с, {doc_type}={type_time:.2f}с, "
                                f"замедление={diff:.2f}с ({diff_pct:.1f}%)"
                            )
                    elif diff < 0:
                        if args.english:
                            print(
                                f"    N={n}: {args.baseline}={baseline_time:.2f}s, {doc_type}={type_time:.2f}s, "
                                f"faster={abs(diff):.2f}s ({abs(diff_pct):.1f}%)"
                            )
                        else:
                            print(
                                f"    N={n}: {args.baseline}={baseline_time:.2f}с, {doc_type}={type_time:.2f}с, "
                                f"ускорение={abs(diff):.2f}с ({abs(diff_pct):.1f}%)"
                            )
                    else:
                        if args.english:
                            print(
                                f"    N={n}: {args.baseline}={baseline_time:.2f}s, {doc_type}={type_time:.2f}s, "
                                f"no change"
                            )
                        else:
                            print(
                                f"    N={n}: {args.baseline}={baseline_time:.2f}с, {doc_type}={type_time:.2f}с, "
                                f"без изменений"
                            )

                if args.english:
                    print(f"  L3BENCHMARK:")
                else:
                    print(f"  L3BENCHMARK:")
                for n in sorted(common_n):
                    baseline_benchmark = baseline_data.loc[n, "benchmark_mean"]
                    type_benchmark = type_data.loc[n, "benchmark_mean"]
                    diff = type_benchmark - baseline_benchmark
                    diff_pct = (
                        (diff / baseline_benchmark * 100)
                        if baseline_benchmark > 0
                        else 0
                    )

                    if diff > 0:
                        if args.english:
                            print(
                                f"    N={n}: {args.baseline}={baseline_benchmark:.2f}s, {doc_type}={type_benchmark:.2f}s, "
                                f"slower={diff:.2f}s ({diff_pct:.1f}%)"
                            )
                        else:
                            print(
                                f"    N={n}: {args.baseline}={baseline_benchmark:.2f}с, {doc_type}={type_benchmark:.2f}с, "
                                f"замедление={diff:.2f}с ({diff_pct:.1f}%)"
                            )
                    elif diff < 0:
                        if args.english:
                            print(
                                f"    N={n}: {args.baseline}={baseline_benchmark:.2f}s, {doc_type}={type_benchmark:.2f}s, "
                                f"faster={abs(diff):.2f}s ({abs(diff_pct):.1f}%)"
                            )
                        else:
                            print(
                                f"    N={n}: {args.baseline}={baseline_benchmark:.2f}с, {doc_type}={type_benchmark:.2f}с, "
                                f"ускорение={abs(diff):.2f}с ({abs(diff_pct):.1f}%)"
                            )
                    else:
                        if args.english:
                            print(
                                f"    N={n}: {args.baseline}={baseline_benchmark:.2f}s, {doc_type}={type_benchmark:.2f}s, "
                                f"no change"
                            )
                        else:
                            print(
                                f"    N={n}: {args.baseline}={baseline_benchmark:.2f}с, {doc_type}={type_benchmark:.2f}с, "
                                f"без изменений"
                            )

    print(f"\n{'='*60}")
    if args.english:
        print(f"ALL GRAPHS SUCCESSFULLY CREATED!")
        print(f"Results saved in: {output_dir}")
    else:
        print(f"ВСЕ ГРАФИКИ УСПЕШНО СОЗДАНЫ!")
        print(f"Результаты сохранены в: {output_dir}")
    print(f"Всего создано графиков: {len(list(output_dir.glob('*.png')))}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

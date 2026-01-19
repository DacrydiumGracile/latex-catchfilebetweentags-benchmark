# plot_flat_simple.py
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os
import sys
from pathlib import Path
from matplotlib.lines import Line2D


def load_data_with_min_max(flat_csv, flat_inner_csv):
    """Загружает данные с min/max значениями."""
    print("Загрузка данных...")

    # Загружаем данные
    df_flat = pd.read_csv(flat_csv)
    df_flat_inner = pd.read_csv(flat_inner_csv)

    # Проверяем обязательные колонки
    required_cols = [
        "N",
        "doc_type",
        "time_mean",
        "time_min",
        "time_max",
        "benchmark_mean",
        "benchmark_min",
        "benchmark_max",
    ]

    for df_name, df in [("flat", df_flat), ("flat_inner", df_flat_inner)]:
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"Ошибка: В файле {df_name} отсутствуют колонки: {missing_cols}")
            print(f"   Найдены колонки: {list(df.columns)}")
            sys.exit(1)

    # Проверяем, что N совпадают
    common_n = sorted(set(df_flat["N"]).intersection(set(df_flat_inner["N"])))
    if not common_n:
        print("Ошибка: Нет общих значений N между flat и flat_inner")
        sys.exit(1)

    print(f"Найдено общих значений N: {len(common_n)}")

    # Создаем объединенный DataFrame
    comparison_data = []

    for n in common_n:
        flat_row = df_flat[df_flat["N"] == n].iloc[0]
        flat_inner_row = df_flat_inner[df_flat_inner["N"] == n].iloc[0]

        # Данные для time
        flat_time_mean = flat_row["time_mean"]
        flat_time_min = flat_row["time_min"]
        flat_time_max = flat_row["time_max"]

        flat_inner_time_mean = flat_inner_row["time_mean"]
        flat_inner_time_min = flat_inner_row["time_min"]
        flat_inner_time_max = flat_inner_row["time_max"]

        # Данные для benchmark
        flat_bench_mean = flat_row["benchmark_mean"]
        flat_bench_min = flat_row["benchmark_min"]
        flat_bench_max = flat_row["benchmark_max"]

        flat_inner_bench_mean = flat_inner_row["benchmark_mean"]
        flat_inner_bench_min = flat_inner_row["benchmark_min"]
        flat_inner_bench_max = flat_inner_row["benchmark_max"]

        # Вычисляем разности
        time_diff = flat_inner_time_mean - flat_time_mean
        time_diff_pct = (time_diff / flat_time_mean * 100) if flat_time_mean > 0 else 0

        bench_diff = flat_inner_bench_mean - flat_bench_mean
        bench_diff_pct = (
            (bench_diff / flat_bench_mean * 100) if flat_bench_mean > 0 else 0
        )

        # Проверяем значимость: если среднее одного попадает в диапазон min/max другого
        time_overlap = (flat_time_min <= flat_inner_time_mean <= flat_time_max) or (
            flat_inner_time_min <= flat_time_mean <= flat_inner_time_max
        )

        bench_overlap = (flat_bench_min <= flat_inner_bench_mean <= flat_bench_max) or (
            flat_inner_bench_min <= flat_bench_mean <= flat_inner_bench_max
        )

        comparison_data.append(
            {
                "N": n,
                # Time данные
                "flat_time_mean": flat_time_mean,
                "flat_time_min": flat_time_min,
                "flat_time_max": flat_time_max,
                "flat_inner_time_mean": flat_inner_time_mean,
                "flat_inner_time_min": flat_inner_time_min,
                "flat_inner_time_max": flat_inner_time_max,
                "time_diff": time_diff,
                "time_diff_pct": time_diff_pct,
                # Если диапазоны НЕ перекрываются - значимо
                "time_significant": not time_overlap,
                # Benchmark данные
                "flat_bench_mean": flat_bench_mean,
                "flat_bench_min": flat_bench_min,
                "flat_bench_max": flat_bench_max,
                "flat_inner_bench_mean": flat_inner_bench_mean,
                "flat_inner_bench_min": flat_inner_bench_min,
                "flat_inner_bench_max": flat_inner_bench_max,
                "bench_diff": bench_diff,
                "bench_diff_pct": bench_diff_pct,
                # Если диапазоны НЕ перекрываются - значимо
                "bench_significant": not bench_overlap,
            }
        )

    df_comparison = pd.DataFrame(comparison_data).sort_values("N")
    print(f"Подготовлено данных: {len(df_comparison)} строк")

    return df_comparison


def plot_comparison(
    df_plot, measurement_type, max_n, output_dir, dpi=150, english=False
):
    """
    Создает график сравнения с min/max диапазонами.

    Args:
        df_plot: DataFrame с данными
        measurement_type: 'time' или 'benchmark'
        max_n: максимальное N для отображения
        output_dir: директория для сохранения
        dpi: разрешение
        english: использовать английские подписи
    """
    # Создаем кастомные элементы для легенды в зависимости от языка
    if english:
        file_prefix = "en_"
        legend_elements = [
            Line2D(
                [0],
                [0],
                color="blue",
                marker="o",
                linestyle="-",
                linewidth=2,
                markersize=6,
                label="flat (\\lipsum command)",
            ),
            Line2D(
                [0],
                [0],
                color="orange",
                marker="s",
                linestyle="-",
                linewidth=2,
                markersize=6,
                label="flat_inner (direct text)",
            ),
            Line2D(
                [0],
                [0],
                color="red",
                marker="*",
                linestyle="None",
                markersize=10,
                label="Significant differences (ranges do not overlap)",
            ),
        ]
    else:
        file_prefix = "ru_"
        legend_elements = [
            Line2D(
                [0],
                [0],
                color="blue",
                marker="o",
                linestyle="-",
                linewidth=2,
                markersize=6,
                label="flat (команда \\lipsum)",
            ),
            Line2D(
                [0],
                [0],
                color="orange",
                marker="s",
                linestyle="-",
                linewidth=2,
                markersize=6,
                label="flat_inner (непосредственный текст)",
            ),
            Line2D(
                [0],
                [0],
                color="red",
                marker="*",
                linestyle="None",
                markersize=10,
                label="Значимые различия (диапазоны не перекрываются)",
            ),
        ]

    # Определяем параметры в зависимости от типа измерения
    if measurement_type == "time":
        flat_mean = df_plot["flat_time_mean"]
        flat_min = df_plot["flat_time_min"]
        flat_max = df_plot["flat_time_max"]
        inner_mean = df_plot["flat_inner_time_mean"]
        inner_min = df_plot["flat_inner_time_min"]
        inner_max = df_plot["flat_inner_time_max"]
        diff = df_plot["time_diff"]
        diff_pct = df_plot["time_diff_pct"]
        significant = df_plot["time_significant"]

        if english:
            ylabel = "Compilation time (seconds)"
            title_measurement = "compilation time (time)"
            diff_label = "Difference of compilation time\nflat_inner - flat"
        else:
            ylabel = "Время компиляции (секунды)"
            title_measurement = "времени компиляции (time)"
            diff_label = "Разность времени компиляции\nflat_inner - flat"

        filename_prefix = "time"
    else:  # benchmark
        flat_mean = df_plot["flat_bench_mean"]
        flat_min = df_plot["flat_bench_min"]
        flat_max = df_plot["flat_bench_max"]
        inner_mean = df_plot["flat_inner_bench_mean"]
        inner_min = df_plot["flat_inner_bench_min"]
        inner_max = df_plot["flat_inner_bench_max"]
        diff = df_plot["bench_diff"]
        diff_pct = df_plot["bench_diff_pct"]
        significant = df_plot["bench_significant"]

        if english:
            ylabel = "l3benchmark time (seconds)"
            title_measurement = "l3benchmark time"
            diff_label = "Difference of l3benchmark time\nflat_inner - flat"
        else:
            ylabel = "Время l3benchmark (секунды)"
            title_measurement = "времени l3benchmark"
            diff_label = "Разность времени l3benchmark\nflat_inner - flat"

        filename_prefix = "benchmark"

    # Создаем график с двумя подграфиками
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), height_ratios=[2, 1])

    n_values = df_plot["N"]

    # Верхний график: сравнение с min/max диапазонами
    # Используем асимметричные ошибки (нижняя ошибка = mean - min, верхняя = max - mean)
    yerr_flat = [flat_mean - flat_min, flat_max - flat_mean]
    yerr_inner = [inner_mean - inner_min, inner_max - inner_mean]

    if english:
        flat_label = "flat (\\lipsum command)"
        inner_label = "flat_inner (direct text)"
    else:
        flat_label = "flat (команда \\lipsum)"
        inner_label = "flat_inner (непосредственный текст)"

    ax1.errorbar(
        n_values,
        flat_mean,
        yerr=yerr_flat,
        fmt="o-",
        color="blue",
        ecolor="blue",
        elinewidth=1.5,
        capsize=4,
        linewidth=2,
        markersize=6,
        label=flat_label,
        alpha=0.8,
    )

    ax1.errorbar(
        n_values,
        inner_mean,
        yerr=yerr_inner,
        fmt="s-",
        color="orange",
        ecolor="orange",
        elinewidth=1.5,
        capsize=4,
        linewidth=2,
        markersize=6,
        label=inner_label,
        alpha=0.8,
    )

    # Отмечаем статистически значимые различия
    for i, (n, sig) in enumerate(zip(n_values, significant)):
        if sig:
            y_max = max(flat_max.iloc[i], inner_max.iloc[i])
            ax1.text(
                n,
                y_max * 1.02,
                "*",
                ha="center",
                va="bottom",
                fontsize=12,
                color="red",
                fontweight="bold",
            )

    ax1.set_ylabel(ylabel, fontsize=12)
    if english:
        title_suffix = f" (N ≤ {max_n})" if max_n else ""
        ax1.set_title(
            f"Comparison of {title_measurement}: flat vs flat_inner{title_suffix}",
            fontsize=14,
        )
    else:
        title_suffix = f" (N ≤ {max_n})" if max_n else ""
        ax1.set_title(
            f"Сравнение {title_measurement}: flat vs flat_inner{title_suffix}",
            fontsize=14,
        )
    ax1.grid(True, alpha=0.3)
    ax1.legend(handles=legend_elements, fontsize=10)

    # Нижний график: разность
    # Зеленый - диапазоны перекрываются (незначимо), красный - не перекрываются (значимо)
    bar_colors = ["green" if not sig else "red" for sig in significant]
    bars = ax2.bar(
        n_values, diff, color=bar_colors, alpha=0.7, edgecolor="black", linewidth=0.5
    )

    ax2.axhline(y=0, color="black", linestyle="-", linewidth=0.5, alpha=0.5)
    ax2.set_xlabel(
        "Количество блоков (N)" if not english else "Number of blocks (N)", fontsize=12
    )
    ax2.set_ylabel(diff_label, fontsize=12)

    if english:
        ax2.set_title(f"Difference of {title_measurement}", fontsize=14)
    else:
        ax2.set_title(f"Разность {title_measurement}", fontsize=14)

    ax2.grid(True, alpha=0.3, axis="y")

    # Добавляем значения на столбцы
    max_abs_diff = diff.abs().max()
    for i, (n, d, pct, sig) in enumerate(zip(n_values, diff, diff_pct, significant)):
        offset = max_abs_diff * 0.05
        va_position = "bottom" if d >= 0 else "top"

        # Значение разности
        if english:
            diff_text = f"{d:.2f}s"
        else:
            diff_text = f"{d:.2f}с"

        ax2.text(
            n,
            d + (offset if d >= 0 else -offset),
            diff_text,
            ha="center",
            va=va_position,
            fontsize=8,
            fontweight="bold",
        )

        # Процент разности чуть ниже/выше
        ax2.text(
            n,
            d + (offset / 2 if d >= 0 else -offset / 2),
            f"({pct:.1f}%)",
            ha="center",
            va=va_position,
            fontsize=7,
        )

    plt.tight_layout()

    # Сохраняем
    filename_suffix = f"_N_{max_n}" if max_n else "_all"
    filename = (
        output_dir / f"{file_prefix}{filename_prefix}_comparison{filename_suffix}.png"
    )
    plt.savefig(filename, dpi=dpi, bbox_inches="tight")
    plt.close()

    print(f"✓ Сохранен график {measurement_type}: {filename}")

    # Краткая статистика для этого графика
    significant_count = sum(significant)
    total_count = len(df_plot)

    if english:
        print(
            f"  Significant differences: {significant_count}/{total_count} "
            f"({significant_count/total_count*100:.1f}%)"
        )
    else:
        print(
            f"  Значимых различий: {significant_count}/{total_count} "
            f"({significant_count/total_count*100:.1f}%)"
        )

    return fig


def print_summary_statistics(df_comparison, english=False):
    """Выводит краткую статистику в консоль."""
    if english:
        print("\n" + "=" * 60)
        print("SUMMARY STATISTICS")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("КРАТКАЯ СТАТИСТИКА")
        print("=" * 60)

    # Time статистика
    time_significant = df_comparison["time_significant"].sum()
    time_total = len(df_comparison)

    if english:
        print(f"TIME measurement:")
        print(
            f"  Significant differences: {time_significant}/{time_total} "
            f"({time_significant/time_total*100:.1f}%)"
        )
    else:
        print(f"ВРЕМЯ ОТ time:")
        print(
            f"  Значимых различий: {time_significant}/{time_total} "
            f"({time_significant/time_total*100:.1f}%)"
        )

    # Benchmark статистика
    bench_significant = df_comparison["bench_significant"].sum()
    bench_total = len(df_comparison)

    if english:
        print(f"\nL3BENCHMARK measurement:")
        print(
            f"  Significant differences: {bench_significant}/{bench_total} "
            f"({bench_significant/bench_total*100:.1f}%)"
        )
    else:
        print(f"\nВРЕМЯ l3benchmark:")
        print(
            f"  Значимых различий: {bench_significant}/{bench_total} "
            f"({bench_significant/bench_total*100:.1f}%)"
        )

    # Общий вывод
    if english:
        print("\n" + "=" * 60)
        print("CONCLUSION:")
        print("=" * 60)

        if time_significant == 0 and bench_significant == 0:
            print(
                "BOTH MEASUREMENTS show that flat and flat_inner are practically indistinguishable!"
            )
            print("   min/max ranges overlap for all N values.")
        elif time_significant > 0 or bench_significant > 0:
            print("Significant differences detected:")
            if time_significant > 0:
                print(
                    f"   - Time: {time_significant} values have non-overlapping ranges"
                )
            if bench_significant > 0:
                print(
                    f"   - Benchmark: {bench_significant} values have non-overlapping ranges"
                )

            # Показываем, для каких N есть значимые различия
            if time_significant > 0:
                significant_n = df_comparison[df_comparison["time_significant"]][
                    "N"
                ].tolist()
                print(f"     Time significant N: {significant_n}")

            if bench_significant > 0:
                significant_n = df_comparison[df_comparison["bench_significant"]][
                    "N"
                ].tolist()
                print(f"     Benchmark significant N: {significant_n}")
    else:
        print("\n" + "=" * 60)
        print("ВЫВОД:")
        print("=" * 60)

        if time_significant == 0 and bench_significant == 0:
            print(
                "ОБА ИЗМЕРЕНИЯ показывают, что flat и flat_inner практически неразличимы!"
            )
            print("   Диапазоны min/max перекрываются для всех значений N.")
        elif time_significant > 0 or bench_significant > 0:
            print("Обнаружены значимые различия:")
            if time_significant > 0:
                print(
                    f"   - Time: {time_significant} значений имеют неперекрывающиеся диапазоны"
                )
            if bench_significant > 0:
                print(
                    f"   - Benchmark: {bench_significant} значений имеют неперекрывающиеся диапазоны"
                )

            # Показываем, для каких N есть значимые различия
            if time_significant > 0:
                significant_n = df_comparison[df_comparison["time_significant"]][
                    "N"
                ].tolist()
                print(f"     Time значимые N: {significant_n}")

            if bench_significant > 0:
                significant_n = df_comparison[df_comparison["bench_significant"]][
                    "N"
                ].tolist()
                print(f"     Benchmark значимые N: {significant_n}")


def main():
    parser = argparse.ArgumentParser(
        description="Простое сравнение flat и flat_inner с min/max диапазонами",
        epilog="""
Примеры использования:
  # Базовое использование (все графики)
  python plot_flat_simple.py --flat-csv results_flat.csv --flat-inner-csv results_flat_inner.csv
  
  # Только детальные графики (N ≤ 300)
  python plot_flat_simple.py --flat-csv results_flat.csv --flat-inner-csv results_flat_inner.csv --detail-only
  
  # Только полные графики (все N)
  python plot_flat_simple.py --flat-csv results_flat.csv --flat-inner-csv results_flat_inner.csv --all-only
  
  # Высокое разрешение
  python plot_flat_simple.py --flat-csv results_flat.csv --flat-inner-csv results_flat_inner.csv --dpi 300
        """,
    )

    parser.add_argument(
        "--flat-csv",
        type=str,
        required=True,
        help="путь к CSV файлу с результатами flat версии",
    )

    parser.add_argument(
        "--flat-inner-csv",
        type=str,
        required=True,
        help="путь к CSV файлу с результатами flat_inner версии",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="flat_simple_comparison",
        help="директория для сохранения (по умолчанию: flat_simple_comparison)",
    )

    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="разрешение графиков в DPI (по умолчанию: 150)",
    )

    parser.add_argument(
        "--detail-max-n",
        type=int,
        default=200,
        help="максимальное N для детального графика (по умолчанию: 200)",
    )

    parser.add_argument(
        "--detail-only",
        action="store_true",
        help="строить только детальные графики (N ≤ detail-max-n)",
    )

    parser.add_argument(
        "--all-only", action="store_true", help="строить только полные графики (все N)"
    )

    parser.add_argument(
        "-E",
        "--english",
        action="store_true",
        help="использовать английские подписи на графиках (по умолчанию: русские)",
    )

    args = parser.parse_args()

    # Проверяем файлы
    for csv_file in [args.flat_csv, args.flat_inner_csv]:
        if not os.path.exists(csv_file):
            print(f"Ошибка: Файл не найден: {csv_file}")
            sys.exit(1)

    # Создаем выходную директорию
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.english:
        print("=" * 60)
        print("SIMPLE COMPARISON OF FLAT AND FLAT_INNER")
        print("=" * 60)
    else:
        print("=" * 60)
        print("ПРОСТОЕ СРАВНЕНИЕ FLAT И FLAT_INNER")
        print("=" * 60)

    print(f"Flat CSV: {args.flat_csv}")
    print(f"Flat_inner CSV: {args.flat_inner_csv}")
    print(f"Выходная директория: {output_dir}")
    print(f"Разрешение: {args.dpi} DPI")
    print(f"Язык подписей: {'английский' if args.english else 'русский'}")

    # Загружаем данные
    df_comparison = load_data_with_min_max(args.flat_csv, args.flat_inner_csv)

    if len(df_comparison) == 0:
        print("Ошибка: Не удалось загрузить данные для сравнения")
        sys.exit(1)

    # Строим графики
    if args.english:
        print("\n" + "=" * 60)
        print("CREATING GRAPHS")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("ПОСТРОЕНИЕ ГРАФИКОВ")
        print("=" * 60)

    # Определяем какие графики строить
    build_all = not args.detail_only
    build_detail = not args.all_only

    if build_all:
        # Графики для всех N
        if args.english:
            print("\nCreating graphs for all N:")
        else:
            print("\nСоздание графиков для всех N:")

        plot_comparison(df_comparison, "time", None, output_dir, args.dpi, args.english)
        plot_comparison(
            df_comparison, "benchmark", None, output_dir, args.dpi, args.english
        )

    if build_detail:
        # Графики для N ≤ detail-max-n
        if args.english:
            print(f"\nCreating detailed graphs (N ≤ {args.detail_max_n}):")
        else:
            print(f"\nСоздание детальных графиков (N ≤ {args.detail_max_n}):")

        df_detail = df_comparison[df_comparison["N"] <= args.detail_max_n]
        if len(df_detail) > 0:
            plot_comparison(
                df_detail, "time", args.detail_max_n, output_dir, args.dpi, args.english
            )
            plot_comparison(
                df_detail,
                "benchmark",
                args.detail_max_n,
                output_dir,
                args.dpi,
                args.english,
            )
        else:
            if args.english:
                print(f"No data for N ≤ {args.detail_max_n}")
            else:
                print(f"Нет данных для N ≤ {args.detail_max_n}")

    # Выводим статистику
    print_summary_statistics(df_comparison, args.english)

    # Сохраняем данные (опционально)
    data_csv = output_dir / "comparison_data.csv"
    df_comparison.to_csv(data_csv, index=False, encoding="utf-8")

    if args.english:
        print(f"\n✓ All data saved: {data_csv}")
    else:
        print(f"\n✓ Сохранены все данные: {data_csv}")

    # Финальный вывод
    if args.english:
        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETED!")
        print("=" * 60)
        print(f"Results saved in: {output_dir}")
    else:
        print("\n" + "=" * 60)
        print("АНАЛИЗ ЗАВЕРШЁН!")
        print("=" * 60)
        print(f"Результаты сохранены в: {output_dir}")

    if build_all and build_detail:
        print(
            f"Создано графиков: 4 (time и benchmark для всех N и N ≤ {args.detail_max_n})"
        )
    elif build_all:
        print(f"Создано графиков: 2 (time и benchmark для всех N)")
    else:
        print(f"Создано графиков: 2 (time и benchmark для N ≤ {args.detail_max_n})")

    if args.english:
        print("Used min/max ranges to assess significance")
    else:
        print("Использованы min/max диапазоны для оценки значимости")
    print("=" * 60)


if __name__ == "__main__":
    main()

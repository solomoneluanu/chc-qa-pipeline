import os
import matplotlib.pyplot as plt
import pandas as pd


# Global plotting style
plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
})


def _ensure_output_dir(output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)


def plot_concordance(results: dict, output_dir: str) -> None:
    """
    Plot concordance class distribution with clinical color coding.
    """
    _ensure_output_dir(output_dir)

    df = results["concordance_table"].copy()

    color_map = {
        "concordant": "green",
        "minor_discordant": "orange",
        "major_discordant": "red",
        "unmapped": "gray"
    }

    colors = [color_map.get(x, "gray") for x in df["Concordance_Class"]]

    plt.figure(figsize=(7, 4.5))
    bars = plt.bar(df["Concordance_Class"], df["Count"], color=colors)

    plt.title("Concordance Distribution")
    plt.ylabel("Number of Cases")
    plt.xlabel("Classification")

    for bar, count in zip(bars, df["Count"]):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.4,
            str(count),
            ha="center",
            va="bottom"
        )

    plt.tight_layout()
    plt.savefig(f"{output_dir}/concordance_bar.png", bbox_inches="tight")
    plt.close()


def plot_subtypes(results: dict, output_dir: str) -> None:
    """
    Plot discordance subtype distribution.
    """
    _ensure_output_dir(output_dir)

    df = results["subtype_table"].copy()
    df = df.sort_values("Count", ascending=True)

    subtype_color_map = {
        "exact_agreement": "green",
        "minor_variance": "orange",
        "minor_undercall": "orange",
        "minor_overcall": "orange",
        "major_undercall": "red",
        "major_overcall": "red",
        "unmapped": "gray"
    }

    colors = [subtype_color_map.get(x, "gray") for x in df["Discordance_Subtype"]]

    plt.figure(figsize=(8, 5))
    bars = plt.barh(df["Discordance_Subtype"], df["Count"], color=colors)

    plt.title("Discordance Subtype Distribution")
    plt.xlabel("Number of Cases")
    plt.ylabel("Subtype")

    for bar, count in zip(bars, df["Count"]):
        plt.text(
            bar.get_width() + 0.3,
            bar.get_y() + bar.get_height() / 2,
            str(count),
            va="center"
        )

    plt.tight_layout()
    plt.savefig(f"{output_dir}/subtype_bar.png", bbox_inches="tight")
    plt.close()


def plot_confusion_matrix(results: dict, output_dir: str) -> None:
    """
    Plot cytology vs histology confusion matrix as heatmap.
    """
    _ensure_output_dir(output_dir)

    cm = results["confusion_matrix"]

    plt.figure(figsize=(8, 5))
    im = plt.imshow(cm, aspect="auto")

    plt.title("Cytology vs Histology")
    plt.xlabel("Histology")
    plt.ylabel("Cytology")

    plt.xticks(range(len(cm.columns)), cm.columns, rotation=45, ha="right")
    plt.yticks(range(len(cm.index)), cm.index)

    for i in range(len(cm.index)):
        for j in range(len(cm.columns)):
            value = cm.iloc[i, j]
            if value != 0:
                plt.text(j, i, str(value), ha="center", va="center")

    plt.colorbar(im)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/confusion_matrix.png", bbox_inches="tight")
    plt.close()


def plot_discrepancy_buckets(results: dict, output_dir: str) -> None:
    """
    Plot CAP-style discrepancy buckets:
    MinVar, MajUnd, MinUnd, Agree, MinOver, MajOver
    """
    _ensure_output_dir(output_dir)

    df = results["bucket_table"].copy()

    bucket_color_map = {
        "Agree": "green",
        "MinVar": "orange",
        "MinUnd": "orange",
        "MinOver": "orange",
        "MajUnd": "red",
        "MajOver": "red"
    }

    colors = [bucket_color_map.get(x, "gray") for x in df["Bucket"]]

    plt.figure(figsize=(8, 4.8))
    bars = plt.bar(df["Bucket"], df["Count"], color=colors)

    plt.title("Cytology-Histology Correlations")
    plt.ylabel("Number of Cases")
    plt.xlabel("Discrepancy Bucket")

    for bar, count in zip(bars, df["Count"]):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.4,
            str(count),
            ha="center",
            va="bottom"
        )

    plt.tight_layout()
    plt.savefig(f"{output_dir}/discrepancy_buckets.png", bbox_inches="tight")
    plt.close()


def plot_hsil_metrics(results: dict, output_dir: str) -> None:
    """
    Plot CAP-style HSIL-focused QA metrics as percentages.
    """
    _ensure_output_dir(output_dir)

    labels = [
        "HSIL→HSIL",
        "HSIL Minor\nDiscrepancy",
        "HSIL Major FP"
    ]

    values = [
        results.get("hsil_to_hsil_pct", 0) or 0,
        results.get("hsil_minor_discrepancy_pct", 0) or 0,
        results.get("hsil_major_fp_pct", 0) or 0,
    ]

    colors = ["green", "orange", "red"]

    plt.figure(figsize=(7, 4.5))
    bars = plt.bar(labels, values, color=colors)

    plt.title("HSIL Correlation Metrics (%)")
    plt.ylabel("Percentage")
    plt.xlabel("Metric")

    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"{value:.1f}%",
            ha="center",
            va="bottom"
        )

    plt.tight_layout()
    plt.savefig(f"{output_dir}/hsil_metrics.png", bbox_inches="tight")
    plt.close()


def generate_all_figures(results: dict, classified_df: pd.DataFrame, output_dir: str) -> None:
    """
    Generate all QA figures in one call.
    """
    _ensure_output_dir(output_dir)

    plot_concordance(results, output_dir)
    plot_subtypes(results, output_dir)
    plot_confusion_matrix(results, output_dir)
    plot_discrepancy_buckets(results, output_dir)
    plot_hsil_metrics(results, output_dir)

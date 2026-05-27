import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch


# ?? Modern style configuration ????????????????????????????????????????????????
COLORS = {
    "concordant":      "#10B981",  # emerald green
    "minor_discordant":"#F59E0B",  # amber
    "major_discordant":"#EF4444",  # red
    "unmapped":        "#94A3B8",  # slate gray
    "blue":            "#1565C0",  # primary blue
    "blue_light":      "#E3F2FD",  # light blue
    "dark":            "#1E293B",  # near black
    "surface":         "#F8FAFC",  # off white
    "border":          "#E2E8F0",  # light border
}

BUCKET_COLORS = {
    "Agree":    "#10B981",
    "MinVar":   "#F59E0B",
    "MinUnd":   "#F59E0B",
    "MinOver":  "#F59E0B",
    "MajUnd":   "#EF4444",
    "MajOver":  "#DC2626",
}

plt.rcParams.update({
    "figure.dpi":         150,
    "savefig.dpi":        300,
    "font.family":        "DejaVu Sans",
    "font.size":          10,
    "axes.titlesize":     13,
    "axes.titleweight":   "bold",
    "axes.titlecolor":    "#1E293B",
    "axes.labelsize":     10,
    "axes.labelcolor":    "#475569",
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.spines.left":   False,
    "axes.spines.bottom": True,
    "axes.edgecolor":     "#E2E8F0",
    "axes.grid":          True,
    "axes.grid.axis":     "y",
    "grid.color":         "#F1F5F9",
    "grid.linewidth":     1.0,
    "xtick.color":        "#64748B",
    "ytick.color":        "#64748B",
    "xtick.bottom":       False,
    "ytick.left":         False,
    "figure.facecolor":   "white",
    "axes.facecolor":     "white",
    "savefig.facecolor":  "white",
    "savefig.bbox":       "tight",
    "savefig.pad_inches": 0.3,
})


def _ensure_output_dir(output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)


def _add_value_labels(ax, bars, fmt="{}", offset=0.5, fontsize=10, color="#1E293B"):
    """Add clean value labels above bars."""
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + offset,
                fmt.format(int(height)),
                ha="center",
                va="bottom",
                fontsize=fontsize,
                fontweight="bold",
                color=color
            )


def _add_subtitle(ax, text):
    """Add a subtle subtitle below the title."""
    ax.annotate(
        text,
        xy=(0.5, 1.02),
        xycoords="axes fraction",
        ha="center",
        fontsize=9,
        color="#94A3B8"
    )


def plot_concordance(results: dict, output_dir: str) -> None:
    """Modern concordance distribution chart."""
    _ensure_output_dir(output_dir)

    df = results["concordance_table"].copy()

    color_map = {
        "concordant":       COLORS["concordant"],
        "minor_discordant": COLORS["minor_discordant"],
        "major_discordant": COLORS["major_discordant"],
        "unmapped":         COLORS["unmapped"]
    }
    colors = [color_map.get(x, COLORS["unmapped"]) for x in df["Concordance_Class"]]

    fig, ax = plt.subplots(figsize=(8, 5))

    bars = ax.bar(
        df["Concordance_Class"],
        df["Count"],
        color=colors,
        width=0.55,
        zorder=3,
        edgecolor="white",
        linewidth=1.5,
        alpha=0.92
    )

    # Add gradient-like effect with edge highlight
    for bar, color in zip(bars, colors):
        bar.set_linewidth(0)
        # Add top highlight bar
        ax.bar(
            bar.get_x() + bar.get_width()/2,
            bar.get_height(),
            width=bar.get_width(),
            bottom=0,
            color=color,
            alpha=0.15,
            zorder=2
        )

    _add_value_labels(ax, bars, offset=0.8)

    # Add percentage labels
    total = df["Count"].sum()
    for bar, count in zip(bars, df["Count"]):
        pct = count / total * 100 if total > 0 else 0
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() / 2,
            f"{pct:.1f}%",
            ha="center",
            va="center",
            fontsize=9,
            color="white",
            fontweight="bold",
            alpha=0.9
        )

    ax.set_title("Concordance Distribution", pad=15)
    _add_subtitle(ax, "CAP-Aligned Classification of Cytology-Histology Pairs")
    ax.set_ylabel("Number of Cases")
    ax.set_xlabel("")

    # Custom x-tick labels
    labels = {
        "concordant":       "Concordant",
        "minor_discordant": "Minor\nDiscordant",
        "major_discordant": "Major\nDiscordant",
        "unmapped":         "Unmapped"
    }
    ax.set_xticklabels(
        [labels.get(x, x) for x in df["Concordance_Class"]],
        fontsize=9
    )

    # Legend
    legend_patches = [
        mpatches.Patch(color=COLORS["concordant"],       label="Concordant"),
        mpatches.Patch(color=COLORS["minor_discordant"], label="Minor Discordant"),
        mpatches.Patch(color=COLORS["major_discordant"], label="Major Discordant"),
    ]
    ax.legend(
        handles=legend_patches,
        loc="upper right",
        frameon=True,
        framealpha=0.9,
        edgecolor=COLORS["border"],
        fontsize=8
    )

    ax.set_ylim(0, df["Count"].max() * 1.25)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(f"{output_dir}/concordance_bar.png")
    plt.close()


def plot_discrepancy_buckets(results: dict, output_dir: str) -> None:
    """Modern CAP-style discrepancy bucket chart."""
    _ensure_output_dir(output_dir)

    df = results["bucket_table"].copy()

    # Reorder buckets clinically
    bucket_order = ["MajUnd", "MinUnd", "MinVar", "Agree", "MinOver", "MajOver"]
    df["Bucket"] = pd.Categorical(df["Bucket"], categories=bucket_order, ordered=True)
    df = df.sort_values("Bucket")

    colors = [BUCKET_COLORS.get(x, COLORS["unmapped"]) for x in df["Bucket"]]

    bucket_labels = {
        "MajUnd":  "Major\nUndercall",
        "MinUnd":  "Minor\nUndercall",
        "MinVar":  "Minor\nVariance",
        "Agree":   "Agree",
        "MinOver": "Minor\nOvercall",
        "MajOver": "Major\nOvercall",
    }

    fig, ax = plt.subplots(figsize=(10, 5.5))

    bars = ax.bar(
        range(len(df)),
        df["Count"],
        color=colors,
        width=0.6,
        zorder=3,
        edgecolor="white",
        linewidth=1.5,
        alpha=0.92
    )

    _add_value_labels(ax, bars, offset=0.5)

    # Add percentage inside bars
    total = df["Count"].sum()
    for bar, count in zip(bars, df["Count"]):
        pct = count / total * 100 if total > 0 else 0
        if bar.get_height() > 3:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() / 2,
                f"{pct:.1f}%",
                ha="center",
                va="center",
                fontsize=8,
                color="white",
                fontweight="bold"
            )

    ax.set_title("Cytology-Histology Correlation Buckets", pad=15)
    _add_subtitle(ax, "CAP QA Discrepancy Classification ? Birdsong ASC Guideline")
    ax.set_ylabel("Number of Cases")
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(
        [bucket_labels.get(x, x) for x in df["Bucket"]],
        fontsize=8.5
    )

    # Vertical separator between undercall and overcall
    ax.axvline(x=2.5, color=COLORS["border"], linewidth=1.5, linestyle="--", alpha=0.7)
    ax.axvline(x=3.5, color=COLORS["border"], linewidth=1.5, linestyle="--", alpha=0.7)

    # Zone labels
    ax.text(1.0, ax.get_ylim()[1] * 0.95, "Undercall Zone",
            ha="center", fontsize=8, color=COLORS["major_discordant"], alpha=0.7)
    ax.text(3.0, ax.get_ylim()[1] * 0.95, "Agree",
            ha="center", fontsize=8, color=COLORS["concordant"], alpha=0.7)
    ax.text(4.5, ax.get_ylim()[1] * 0.95, "Overcall Zone",
            ha="center", fontsize=8, color=COLORS["minor_discordant"], alpha=0.7)

    ax.set_ylim(0, df["Count"].max() * 1.3)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(f"{output_dir}/discrepancy_buckets.png")
    plt.close()


def plot_confusion_matrix(results: dict, output_dir: str) -> None:
    """Modern confusion matrix heatmap."""
    _ensure_output_dir(output_dir)

    cm = results["confusion_matrix"].copy()

    # Custom colormap: white ? blue ? dark blue
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "clinical",
        ["#F8FAFC", "#BFDBFE", "#1D4ED8", "#1E3A8A"],
        N=256
    )

    fig, ax = plt.subplots(figsize=(10, 6.5))

    im = ax.imshow(cm.values, cmap=cmap, aspect="auto", vmin=0)

    # Cell text
    for i in range(len(cm.index)):
        for j in range(len(cm.columns)):
            value = cm.iloc[i, j]
            if value > 0:
                text_color = "white" if value > cm.values.max() * 0.5 else COLORS["dark"]
                ax.text(
                    j, i, str(int(value)),
                    ha="center", va="center",
                    fontsize=10, fontweight="bold",
                    color=text_color
                )

    # Axis labels
    ax.set_xticks(range(len(cm.columns)))
    ax.set_yticks(range(len(cm.index)))

    short_histo = {
        "Benign / Inflammatory (Negative)": "Benign",
        "LSIL (CIN1)":                      "LSIL\n(CIN1)",
        "HSIL (CIN2)":                      "HSIL\n(CIN2)",
        "HSIL (CIN3)":                      "HSIL\n(CIN3)",
        "Squamous Cell Carcinoma":          "SCC",
        "Adenocarcinoma":                   "Adeno",
    }
    col_labels = [short_histo.get(c, c) for c in cm.columns]
    ax.set_xticklabels(col_labels, fontsize=8.5, rotation=0)
    ax.set_yticklabels(cm.index, fontsize=8.5)

    ax.set_title("Cytology vs Histology Correlation Matrix", pad=15)
    _add_subtitle(ax, "Cell values = number of cases. Diagonal = concordant pairs.")
    ax.set_xlabel("Histology Diagnosis", labelpad=10)
    ax.set_ylabel("Cytology Diagnosis", labelpad=10)

    # Diagonal highlight
    for i in range(min(len(cm.index), len(cm.columns))):
        ax.add_patch(plt.Rectangle(
            (i - 0.5, i - 0.5), 1, 1,
            fill=False,
            edgecolor=COLORS["concordant"],
            linewidth=2.5,
            zorder=5
        ))

    plt.colorbar(im, ax=ax, shrink=0.8, label="Case Count")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/confusion_matrix.png")
    plt.close()


def plot_hsil_metrics(results: dict, output_dir: str) -> None:
    """Modern HSIL QA metrics chart."""
    _ensure_output_dir(output_dir)

    values = [
        results.get("hsil_to_hsil_pct",          0) or 0,
        results.get("hsil_minor_discrepancy_pct", 0) or 0,
        results.get("hsil_major_fp_pct",          0) or 0,
    ]

    labels = [
        "HSIL Pap\nwith HSIL Biopsy",
        "HSIL Pap\nMinor Discrepancy",
        "HSIL Pap\nMajor False Positive",
    ]
    colors = [COLORS["concordant"], COLORS["minor_discordant"], COLORS["major_discordant"]]

    fig, ax = plt.subplots(figsize=(8, 5))

    bars = ax.bar(
        range(len(labels)),
        values,
        color=colors,
        width=0.5,
        zorder=3,
        edgecolor="white",
        linewidth=1.5,
        alpha=0.92
    )

    # Value labels
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.0,
            f"{value:.1f}%",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
            color=COLORS["dark"]
        )

    # CAP benchmark line for HSIL PV+
    ax.axhline(y=60, color="#6366F1", linewidth=1.5,
               linestyle="--", alpha=0.8, zorder=4, label="CAP Target (60%)")
    ax.text(2.35, 61, "CAP 60%", fontsize=8, color="#6366F1", va="bottom")

    ax.set_title("HSIL Correlation Metrics", pad=15)
    _add_subtitle(ax, "CAP Positive Predictive Value Analysis")
    ax.set_ylabel("Percentage (%)")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, max(values + [70]) * 1.2 if values else 100)
    ax.legend(fontsize=8, frameon=True, edgecolor=COLORS["border"])
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(f"{output_dir}/hsil_metrics.png")
    plt.close()


def plot_subtypes(results: dict, output_dir: str) -> None:
    """Modern horizontal subtype chart."""
    _ensure_output_dir(output_dir)

    df = results["subtype_table"].copy()
    df = df.sort_values("Count", ascending=True)

    subtype_colors = {
        "exact_agreement": COLORS["concordant"],
        "minor_variance":  "#A78BFA",
        "minor_undercall": COLORS["minor_discordant"],
        "minor_overcall":  "#FB923C",
        "major_undercall": COLORS["major_discordant"],
        "major_overcall":  "#DC2626",
        "unmapped":        COLORS["unmapped"]
    }
    colors = [subtype_colors.get(x, COLORS["unmapped"]) for x in df["Discordance_Subtype"]]

    fig, ax = plt.subplots(figsize=(9, 5.5))

    bars = ax.barh(
        df["Discordance_Subtype"],
        df["Count"],
        color=colors,
        height=0.55,
        zorder=3,
        edgecolor="white",
        linewidth=1.5,
        alpha=0.92
    )

    # Value labels
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.3,
            bar.get_y() + bar.get_height() / 2,
            str(int(width)),
            va="center",
            fontsize=10,
            fontweight="bold",
            color=COLORS["dark"]
        )

    ax.set_title("Discordance Subtype Breakdown", pad=15)
    _add_subtitle(ax, "Detailed classification of all non-concordant pairs")
    ax.set_xlabel("Number of Cases")
    ax.set_xlim(0, df["Count"].max() * 1.2)
    ax.xaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    # Remove y-axis spine
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(True)
    ax.spines["bottom"].set_color(COLORS["border"])

    plt.tight_layout()
    plt.savefig(f"{output_dir}/subtype_bar.png")
    plt.close()


def plot_summary_dashboard(results: dict, output_dir: str) -> None:
    """
    Modern summary dashboard with key metrics.
    Single figure with four panels.
    """
    _ensure_output_dir(output_dir)

    fig = plt.figure(figsize=(14, 8))
    fig.patch.set_facecolor("white")

    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

    # ?? Panel 1: Concordance donut ????????????????????????????????????????????
    ax1 = fig.add_subplot(gs[0, 0])
    concordance = results.get("concordance_counts", {})
    donut_vals  = [
        concordance.get("concordant",       0),
        concordance.get("minor_discordant", 0),
        concordance.get("major_discordant", 0),
    ]
    donut_colors  = [COLORS["concordant"], COLORS["minor_discordant"], COLORS["major_discordant"]]
    donut_labels  = ["Concordant", "Minor Disc", "Major Disc"]

    wedges, texts, autotexts = ax1.pie(
        donut_vals,
        colors=donut_colors,
        labels=None,
        autopct=lambda p: f"{p:.1f}%" if p > 3 else "",
        pctdistance=0.75,
        startangle=90,
        wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2)
    )
    for autotext in autotexts:
        autotext.set_fontsize(8)
        autotext.set_fontweight("bold")
        autotext.set_color("white")

    total = sum(donut_vals)
    ax1.text(0, 0, f"{total}\nCases", ha="center", va="center",
             fontsize=11, fontweight="bold", color=COLORS["dark"])
    ax1.set_title("Concordance\nBreakdown", fontsize=11, pad=8)
    ax1.legend(
        wedges, donut_labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=3,
        fontsize=7,
        frameon=False
    )

    # ?? Panel 2: Bucket bar ???????????????????????????????????????????????????
    ax2 = fig.add_subplot(gs[0, 1:])
    bucket_df = results["bucket_table"].copy()
    bucket_order = ["MajUnd", "MinUnd", "MinVar", "Agree", "MinOver", "MajOver"]
    bucket_df["Bucket"] = pd.Categorical(bucket_df["Bucket"], categories=bucket_order, ordered=True)
    bucket_df = bucket_df.sort_values("Bucket")

    bcolors = [BUCKET_COLORS.get(x, COLORS["unmapped"]) for x in bucket_df["Bucket"]]
    bars = ax2.bar(
        range(len(bucket_df)),
        bucket_df["Count"],
        color=bcolors,
        width=0.6,
        zorder=3,
        edgecolor="white",
        linewidth=1.5,
        alpha=0.92
    )

    bucket_short = {
        "MajUnd": "Maj\nUnd", "MinUnd": "Min\nUnd",
        "MinVar": "Min\nVar", "Agree":  "Agree",
        "MinOver": "Min\nOver", "MajOver": "Maj\nOver"
    }
    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax2.text(bar.get_x() + bar.get_width()/2, h + 0.4,
                     str(int(h)), ha="center", fontsize=8,
                     fontweight="bold", color=COLORS["dark"])

    ax2.set_xticks(range(len(bucket_df)))
    ax2.set_xticklabels([bucket_short.get(x, x) for x in bucket_df["Bucket"]], fontsize=8)
    ax2.set_title("Discrepancy Buckets", fontsize=11, pad=8)
    ax2.set_ylabel("Cases", fontsize=9)
    ax2.yaxis.grid(True, linestyle="--", alpha=0.4)
    ax2.set_axisbelow(True)
    ax2.spines["left"].set_visible(False)

    # ?? Panel 3: HSIL metrics ?????????????????????????????????????????????????
    ax3 = fig.add_subplot(gs[1, 0:2])
    hsil_vals = [
        results.get("hsil_to_hsil_pct",          0) or 0,
        results.get("hsil_minor_discrepancy_pct", 0) or 0,
        results.get("hsil_major_fp_pct",          0) or 0,
    ]
    hsil_labels = ["HSIL->HSIL\n(PV+)", "HSIL Minor\nDiscrep", "HSIL Major\nFP"]
    hsil_colors = [COLORS["concordant"], COLORS["minor_discordant"], COLORS["major_discordant"]]

    bars3 = ax3.bar(range(3), hsil_vals, color=hsil_colors,
                    width=0.45, zorder=3, edgecolor="white", alpha=0.92)
    ax3.axhline(y=60, color="#6366F1", linewidth=1.5, linestyle="--",
                alpha=0.8, label="CAP Target 60%")
    for bar, val in zip(bars3, hsil_vals):
        ax3.text(bar.get_x() + bar.get_width()/2, val + 1,
                 f"{val:.1f}%", ha="center", fontsize=9,
                 fontweight="bold", color=COLORS["dark"])
    ax3.set_xticks(range(3))
    ax3.set_xticklabels(hsil_labels, fontsize=8.5)
    ax3.set_title("HSIL Metrics", fontsize=11, pad=8)
    ax3.set_ylabel("Percentage (%)", fontsize=9)
    ax3.legend(fontsize=8, frameon=False)
    ax3.yaxis.grid(True, linestyle="--", alpha=0.4)
    ax3.set_axisbelow(True)
    ax3.spines["left"].set_visible(False)
    ax3.set_ylim(0, max(hsil_vals + [70]) * 1.3 if hsil_vals else 100)

    # ?? Panel 4: Key metrics scorecard ???????????????????????????????????????
    ax4 = fig.add_subplot(gs[1, 2])
    ax4.axis("off")

    total      = results.get("total_cases", 0)
    conc_pct   = results.get("concordance_percentages", {}).get("concordant", 0)
    major_pct  = results.get("concordance_percentages", {}).get("major_discordant", 0)
    minor_pct  = results.get("concordance_percentages", {}).get("minor_discordant", 0)
    hsil_pv    = results.get("hsil_pv_plus", 0) or 0
    major_fn   = results.get("major_fn_count", 0)

    metrics = [
        ("Total Cases",          str(total),           COLORS["blue"]),
        ("Concordant",           f"{conc_pct:.1f}%",   COLORS["concordant"]),
        ("Major Discordant",     f"{major_pct:.1f}%",  COLORS["major_discordant"]),
        ("Minor Discordant",     f"{minor_pct:.1f}%",  COLORS["minor_discordant"]),
        ("HSIL PV+",             f"{hsil_pv:.1f}%",    COLORS["blue"]),
        ("Major False Negatives",str(int(major_fn)),   COLORS["major_discordant"]),
    ]

    y = 0.95
    for label, value, color in metrics:
        ax4.text(0.05, y, label,    fontsize=8,  color="#64748B", va="top")
        ax4.text(0.95, y, value,    fontsize=11, color=color,
                 va="top", ha="right", fontweight="bold")
        ax4.axhline(y=y - 0.03, xmin=0, xmax=1,
                    color=COLORS["border"], linewidth=0.8, alpha=0.7)
        y -= 0.15

    ax4.set_title("Key Metrics", fontsize=11, pad=8)
    ax4.set_xlim(0, 1)
    ax4.set_ylim(0, 1)

    fig.suptitle(
        "CHC-QA Pipeline | Quality Assurance Report",
        fontsize=14,
        fontweight="bold",
        color=COLORS["dark"],
        y=1.01
    )

    plt.savefig(f"{output_dir}/summary_dashboard.png", bbox_inches="tight")
    plt.close()


def generate_all_figures(results: dict, classified_df: pd.DataFrame, output_dir: str) -> None:
    """Generate all QA figures."""
    _ensure_output_dir(output_dir)

    plot_concordance(results,          output_dir)
    plot_subtypes(results,             output_dir)
    plot_confusion_matrix(results,     output_dir)
    plot_discrepancy_buckets(results,  output_dir)
    plot_hsil_metrics(results,         output_dir)
    plot_summary_dashboard(results,    output_dir)

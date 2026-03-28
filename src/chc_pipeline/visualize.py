import os
import matplotlib.pyplot as plt
import pandas as pd


def plot_concordance(results, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    df = results["concordance_table"]

    plt.figure()
    plt.bar(df["Concordance_Class"], df["Count"])
    plt.title("Concordance Distribution")
    plt.xlabel("Class")
    plt.ylabel("Count")
    plt.xticks(rotation=30)
    plt.tight_layout()

    plt.savefig(f"{output_dir}/concordance_bar.png")
    plt.close()


def plot_subtypes(results, output_dir):
    df = results["subtype_table"]

    plt.figure()
    plt.bar(df["Discordance_Subtype"], df["Count"])
    plt.title("Discordance Subtype Distribution")
    plt.xlabel("Subtype")
    plt.ylabel("Count")
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(f"{output_dir}/subtype_bar.png")
    plt.close()


def plot_confusion_matrix(results, output_dir):
    cm = results["confusion_matrix"]

    plt.figure()
    plt.imshow(cm, aspect='auto')
    plt.title("Cytology vs Histology")
    plt.xlabel("Histology")
    plt.ylabel("Cytology")

    plt.xticks(range(len(cm.columns)), cm.columns, rotation=45)
    plt.yticks(range(len(cm.index)), cm.index)

    plt.colorbar()
    plt.tight_layout()

    plt.savefig(f"{output_dir}/confusion_matrix.png")
    plt.close()

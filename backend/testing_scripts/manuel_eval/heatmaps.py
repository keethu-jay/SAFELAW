"""
Generate stackable heatmap PNGs from v1–v4 manual evaluation CSVs.
Color-codes by analogous grade; blue outline for verbatim suggestions.
Outputs saved to same folder for stacking and comparison.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

# RGBA colors – alpha 0.6 for semi-transparent stacking
RGBA_MAP = {
    "Analogous": (0.3, 0.6, 0.0, 0.6),        # Dark Green
    "Mostly Analogous": (0.6, 0.8, 0.2, 0.6), # Light Green
    "Partly Analogous": (0.8, 0.6, 0.0, 0.6), # Mustard
    "Partially Analogous": (0.8, 0.6, 0.0, 0.6),  # Same as Partly
    "Kinda Analogous": (0.8, 0.6, 0.0, 0.6),  # Same as Partly
    "Not Analogous": (0.6, 0.0, 0.0, 0.6),    # Dark Red

}
VERBATIM_EDGE = "#3399FF"
DEFAULT_FACE = (1, 1, 1, 0)  # Transparent for unknown

# Semantic score ranges → same colors as manual grading
# 0.65–0.75 = light green; narrower bands so heatmap doesn't look overly positive
SCORE_RANGES = [
    (0.75, 1.0, RGBA_MAP["Analogous"]),       # Dark Green – verbatim-like
    (0.65, 0.75, RGBA_MAP["Mostly Analogous"]), # Light Green
    (0.55, 0.65, RGBA_MAP["Partly Analogous"]),  # Mustard
    (0.0, 0.55, RGBA_MAP["Not Analogous"]),   # Dark Red
]


def score_to_color(val) -> tuple:
    """Map numeric score to RGBA color."""
    try:
        s = float(val)
    except (ValueError, TypeError):
        return DEFAULT_FACE
    for lo, hi, color in SCORE_RANGES:
        if lo <= s < hi:
            return color
    if s >= 1.0:
        return SCORE_RANGES[0][2]
    return SCORE_RANGES[-1][2]


def normalize_grade(val: str) -> str:
    """Normalize grade strings to canonical form."""
    s = str(val).replace(" (Verbatim)", "").strip()
    if not s:
        return ""
    if "Partially" in s:
        return "Partially Analogous"
    if "Kinda" in s:
        return "Kinda Analogous"
    return s


def generate_stackable_layer(csv_path: Path, output_path: Path, title: str):
    """Generate one heatmap from a CSV. Color by grade, blue outline for verbatim."""
    df = pd.read_csv(csv_path, encoding="utf-8")
    df = df.set_index(df.columns[0])

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.axis("off")
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    # Title – two squares above the table
    ax.set_title(title, fontsize=14, fontweight="bold", pad=4)

    # Empty cell text for clean stacking; loc="upper center" so table sits close under title
    table = ax.table(
        cellText=[["" for _ in range(len(df.columns))] for _ in range(len(df))],
        rowLabels=df.index,
        colLabels=df.columns,
        cellLoc="center",
        loc="upper center",
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 2.5)

    for i in range(len(df)):
        for j in range(len(df.columns)):
            cell_val = df.iloc[i, j]
            cell = table[(i + 1, j)]
            is_verbatim = "(Verbatim)" in str(cell_val)
            clean_grade = normalize_grade(cell_val)
            face_color = RGBA_MAP.get(clean_grade, DEFAULT_FACE)
            cell.set_facecolor(face_color)
            if is_verbatim:
                cell.set_edgecolor(VERBATIM_EDGE)
                cell.set_linewidth(4)
            else:
                cell.set_edgecolor((0.8, 0.8, 0.8, 0.2))
                cell.set_linewidth(0.5)

    plt.savefig(output_path, transparent=True, bbox_inches="tight", pad_inches=0.15, dpi=300)
    plt.close()
    print(f"Saved: {output_path}")


def generate_scores_heatmap(
    scores_path: Path,
    eval_path: Path,
    output_path: Path,
    title: str,
):
    """Generate semantic score heatmap. Colors by score range; blue outline from eval CSV verbatim."""
    df = pd.read_csv(scores_path, encoding="utf-8")
    df = df.set_index(df.columns[0])

    # Load eval CSV for verbatim markers
    verbatim_mask = None
    if eval_path.exists() and eval_path.stat().st_size > 0:
        eval_df = pd.read_csv(eval_path, encoding="utf-8")
        eval_df = eval_df.set_index(eval_df.columns[0])
        if eval_df.shape == df.shape:
            verbatim_mask = eval_df.astype(str).apply(lambda c: c.str.contains("(Verbatim)", regex=False))

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.axis("off")
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    ax.set_title(title, fontsize=14, fontweight="bold", pad=4)

    table = ax.table(
        cellText=[["" for _ in range(len(df.columns))] for _ in range(len(df))],
        rowLabels=df.index,
        colLabels=df.columns,
        cellLoc="center",
        loc="upper center",
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 2.5)

    for i in range(len(df)):
        for j in range(len(df.columns)):
            cell_val = df.iloc[i, j]
            cell = table[(i + 1, j)]
            face_color = score_to_color(cell_val)
            cell.set_facecolor(face_color)
            is_verbatim = verbatim_mask is not None and verbatim_mask.iloc[i, j]
            if is_verbatim:
                cell.set_edgecolor(VERBATIM_EDGE)
                cell.set_linewidth(4)
            else:
                cell.set_edgecolor((0.8, 0.8, 0.8, 0.2))
                cell.set_linewidth(0.5)

    plt.savefig(output_path, transparent=True, bbox_inches="tight", pad_inches=0.15, dpi=300)
    plt.close()
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    configs = [
        ("v1_eval.csv", "v1_heatmap.png", "Manual Evaluation — v1: Label-filtered only"),
        ("v2_eval.csv", "v2_heatmap.png", "Manual Evaluation — v2: Context tag"),
        ("v3_eval.csv", "v3_heatmap.png", "Manual Evaluation — v3: Case summary"),
        ("v4_eval.csv", "v4_heatmap.png", "Manual Evaluation — v4: Label-filtered + context tag"),
    ]
    for csv_name, out_name, title in configs:
        csv_path = SCRIPT_DIR / csv_name
        if not csv_path.exists() or csv_path.stat().st_size == 0:
            print(f"Skip {csv_name} (not found or empty)")
            continue
        try:
            generate_stackable_layer(csv_path, SCRIPT_DIR / out_name, title)
        except Exception as e:
            print(f"Error processing {csv_name}: {e}")

    # Semantic score heatmaps
    score_configs = [
        ("v1_scores.csv", "v1_eval.csv", "v1_scores_heatmap.png", "Semantic Score — v1: Label-filtered only"),
        ("v2_scores.csv", "v2_eval.csv", "v2_scores_heatmap.png", "Semantic Score — v2: Context tag"),
        ("v3_scores.csv", "v3_eval.csv", "v3_scores_heatmap.png", "Semantic Score — v3: Case summary"),
        ("v4_scores.csv", "v4_eval.csv", "v4_scores_heatmap.png", "Semantic Score — v4: Label-filtered + context tag"),
    ]
    for scores_name, eval_name, out_name, title in score_configs:
        scores_path = SCRIPT_DIR / scores_name
        eval_path = SCRIPT_DIR / eval_name
        if not scores_path.exists() or scores_path.stat().st_size == 0:
            print(f"Skip {scores_name} (not found or empty)")
            continue
        try:
            generate_scores_heatmap(scores_path, eval_path, SCRIPT_DIR / out_name, title)
        except Exception as e:
            print(f"Error processing {scores_name}: {e}")

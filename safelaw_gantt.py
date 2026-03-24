import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

# ── Palette ──────────────────────────────────────────────────────────────────
BLUE = "#378ADD"
TEAL = "#1D9E75"
AMBER = "#BA7517"

PHASE_BG = "#F1EFE8"
HEADER_A = "#B5D4F4"
HEADER_B = "#9FE1CB"
HEADER_C = "#FAC775"
GRID_COLOR = "#CCCCCC"
TEXT_DARK = "#2C2C2A"
TEXT_MID = "#5F5E5A"

# ── Column definitions ────────────────────────────────────────────────────────
# Each col: (label, term)  term: 'A','B','C'
COLS = [
    ("21-22", "A"),
    ("25-29", "A"),
    ("1-5", "A"),
    ("8-12", "A"),
    ("15-19", "A"),
    ("22-26", "A"),
    ("29-3", "A"),
    ("6-10", "A"),
    ("13-17", "A"),
    ("20-24", "A"),
    ("27-31", "B"),
    ("3-7", "B"),
    ("10-14", "B"),
    ("17-21", "B"),
    ("24-28", "B"),
    ("1-5", "B"),
    ("8-12", "B"),
    ("15-19", "B"),
    ("22-26", "B"),
    ("Dec", "B"),
    ("—", "B"),
    ("14-16", "C"),
    ("19-23", "C"),
    ("26-30", "C"),
    ("2-6", "C"),
    ("9-13", "C"),
    ("16-20", "C"),
    ("23-27", "C"),
    ("2-6", "C"),
    ("9-13", "C"),
    ("Mar", "C"),
]
N_COLS = len(COLS)

# ── Row definitions ───────────────────────────────────────────────────────────
ROWS = [
    # (label, color_or_None, cells_list)
    # None color = phase header row
    ("Phase 1 — Research & Planning", None, []),
    (
        "Literature review on AI\nin judicial contexts",
        BLUE,
        [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ),
    (
        "Comparative analysis\n(UNESCO, EU, US, Colombia)",
        BLUE,
        [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ),
    (
        "CorpusStudio & GP-TSM\ncodebase deep-dive",
        BLUE,
        [0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ),
    (
        "Problem definition &\nresearch questions",
        BLUE,
        [0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ),
    ("Phase 2 — Design & Prototyping", None, []),
    (
        "HCI design review &\ninspiration gathering",
        TEAL,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ),
    (
        "Legal terminology\nfamiliarisation",
        TEAL,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ),
    (
        "Low-fidelity wireframes\n(interface for judges)",
        TEAL,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ),
    (
        "Feedback session with\nadvisors & mentors",
        TEAL,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ),
    (
        "High-fidelity prototype\n(Figma / Visily)",
        TEAL,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ),
    (
        "Style guide, colour palette\n& WCAG review",
        TEAL,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ),
    (
        "Frontend implementation\n(home, login, writing, reading)",
        TEAL,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    ),
    ("Phase 3 — Data Pipeline & Embeddings", None, []),
    (
        "US opinions eval &\nregex parser attempt",
        BLUE,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ),
    (
        "UK/US legal comparison\n& BAILII analysis",
        BLUE,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ),
    (
        "National Archives API\naccess request & approval",
        BLUE,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ),
    (
        "Voyage-law-2 eval →\npivot to Kanon-2 (MLEB)",
        BLUE,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ),
    (
        "Ingestion of ~4,000 UKSC\n& Upper Tribunal judgments",
        BLUE,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ),
    (
        "GPT-4 Mini opinion classifier\n(majority / concurring / dissenting)",
        BLUE,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ),
    (
        "Supabase backend schema\n& pgvector setup",
        BLUE,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ),
    ("Phase 4 — Retrieval Evaluation & Optimisation", None, []),
    (
        "Baseline retrieval testing\n& pgvector KNN bug fix",
        AMBER,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    ),
    (
        "Functional labeling\n(6 categories, sentence-level)",
        AMBER,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    ),
    (
        "Corpus extension: 14 HTML\n+ 6 PDF cases (Flanagan)",
        AMBER,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    ),
    (
        "V1–V4 metadata\nenrichment experiments",
        AMBER,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0],
    ),
    (
        "psycopg2 session pooler\n(bypass Supabase rate limits)",
        AMBER,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0],
    ),
    (
        "Manual eval with Prof. Flanagan\n& heatmap analysis",
        AMBER,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
    ),
    (
        "V4 confirmed as\nmost reliable version",
        AMBER,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    ),
]

N_ROWS = len(ROWS)

# ── Layout ────────────────────────────────────────────────────────────────────
LABEL_W = 2.6  # inches for task label column
COL_W = 0.32  # inches per week column
ROW_H = 0.42  # inches per task row
PHASE_H = 0.30  # inches for phase header rows
HEADER_H = 0.55  # inches for the term + week header area
MARGIN_L = 0.15
MARGIN_R = 0.15
MARGIN_T = 0.6
MARGIN_B = 0.5

total_w = MARGIN_L + LABEL_W + N_COLS * COL_W + MARGIN_R
# Compute total height
row_heights = []
for r in ROWS:
    row_heights.append(PHASE_H if r[1] is None else ROW_H)
total_h = MARGIN_T + HEADER_H + sum(row_heights) + MARGIN_B

fig, ax = plt.subplots(figsize=(total_w, total_h))
ax.set_xlim(0, total_w)
ax.set_ylim(0, total_h)
ax.axis("off")
fig.patch.set_facecolor("white")


# Helper: draw rect
def rect(x, y, w, h, color, alpha=1.0, zorder=2, radius=0.03):
    p = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=color,
        edgecolor="none",
        alpha=alpha,
        zorder=zorder,
    )
    ax.add_patch(p)


def line(x0, y0, x1, y1, color=GRID_COLOR, lw=0.4, zorder=1):
    ax.plot([x0, x1], [y0, y1], color=color, lw=lw, zorder=zorder)


# ── Draw term header band ─────────────────────────────────────────────────────
x0 = MARGIN_L + LABEL_W
y_top = total_h - MARGIN_T

# Term spans
term_spans = {}
for i, (lbl, term) in enumerate(COLS):
    if term not in term_spans:
        term_spans[term] = [i, i]
    else:
        term_spans[term][1] = i

term_colors = {"A": HEADER_A, "B": HEADER_B, "C": HEADER_C}
term_labels = {"A": "A Term (Aug – Oct)", "B": "B Term (Oct – Dec)", "C": "C Term (Jan – Mar)"}

TERM_H = 0.24
WEEK_H = 0.31

for term, (c_start, c_end) in term_spans.items():
    tx = x0 + c_start * COL_W
    tw = (c_end - c_start + 1) * COL_W
    ty = y_top - TERM_H
    rect(tx, ty, tw, TERM_H - 0.01, term_colors[term], radius=0.04)
    ax.text(
        tx + tw / 2,
        ty + TERM_H / 2,
        term_labels[term],
        ha="center",
        va="center",
        fontsize=7.5,
        fontweight="bold",
        color=TEXT_DARK,
        zorder=3,
    )

# Week header row
wy = y_top - TERM_H - WEEK_H
for i, (lbl, term) in enumerate(COLS):
    wx = x0 + i * COL_W
    rect(wx, wy, COL_W - 0.01, WEEK_H - 0.01, "#F8F7F4", radius=0.0)
    ax.text(
        wx + COL_W / 2,
        wy + WEEK_H / 2,
        lbl,
        ha="center",
        va="center",
        fontsize=5.2,
        color=TEXT_MID,
        zorder=3,
    )

# "Task" label in header area
ax.text(
    MARGIN_L + LABEL_W / 2,
    wy + WEEK_H / 2,
    "Task",
    ha="center",
    va="center",
    fontsize=7,
    fontweight="bold",
    color=TEXT_DARK,
    zorder=3,
)

# ── Draw rows ─────────────────────────────────────────────────────────────────
y_cursor = wy  # top of first row (going downward)

for row_idx, (label, color, cells) in enumerate(ROWS):
    rh = PHASE_H if color is None else ROW_H
    y_cursor -= rh

    # Label cell background
    if color is None:
        # Phase header
        rect(
            MARGIN_L,
            y_cursor,
            LABEL_W + N_COLS * COL_W,
            rh - 0.01,
            PHASE_BG,
            radius=0.0,
            zorder=2,
        )
        ax.text(
            MARGIN_L + 0.12,
            y_cursor + rh / 2,
            label,
            ha="left",
            va="center",
            fontsize=7.2,
            fontweight="bold",
            color=TEXT_MID,
            zorder=3,
        )
    else:
        # Task row — alternating subtle stripe
        bg = "#FAFAF8" if row_idx % 2 == 0 else "white"
        rect(MARGIN_L, y_cursor, LABEL_W, rh - 0.01, bg, radius=0.0, zorder=2)
        ax.text(
            MARGIN_L + 0.1,
            y_cursor + rh / 2,
            label,
            ha="left",
            va="center",
            fontsize=6.3,
            color=TEXT_DARK,
            zorder=3,
            linespacing=1.25,
        )

        # Week cells
        for ci, v in enumerate(cells):
            cx = x0 + ci * COL_W
            bg_cell = "#FAFAF8" if row_idx % 2 == 0 else "white"
            rect(cx, y_cursor, COL_W - 0.01, rh - 0.02, bg_cell, radius=0.0, zorder=2)
            if v:
                # Filled bar — slight inset
                pad = 0.03
                rect(
                    cx + pad,
                    y_cursor + pad,
                    COL_W - 0.01 - 2 * pad,
                    rh - 0.02 - 2 * pad,
                    color,
                    radius=0.04,
                    zorder=3,
                )

# ── Grid lines ────────────────────────────────────────────────────────────────
grid_top = y_top - TERM_H - WEEK_H
grid_bottom = y_cursor

# Vertical lines between columns
for i in range(N_COLS + 1):
    lx = x0 + i * COL_W
    line(lx, grid_top, lx, grid_bottom, color=GRID_COLOR, lw=0.3)

# Vertical line separating label column
line(
    MARGIN_L + LABEL_W,
    y_top - TERM_H,
    MARGIN_L + LABEL_W,
    grid_bottom,
    color=GRID_COLOR,
    lw=0.5,
)

# Horizontal lines
yc = wy
for row_idx, (label, color, cells) in enumerate(ROWS):
    rh = PHASE_H if color is None else ROW_H
    line(
        MARGIN_L,
        yc,
        MARGIN_L + LABEL_W + N_COLS * COL_W,
        yc,
        color=GRID_COLOR,
        lw=0.4 if color is None else 0.25,
    )
    yc -= rh
line(
    MARGIN_L,
    yc,
    MARGIN_L + LABEL_W + N_COLS * COL_W,
    yc,
    color=GRID_COLOR,
    lw=0.5,
)

# Outer border
bx = MARGIN_L
by = y_cursor
bw = LABEL_W + N_COLS * COL_W
bh = y_top - y_cursor
for x0b, y0b, x1b, y1b in [
    (bx, by, bx + bw, by),
    (bx, by + bh, bx + bw, by + bh),
    (bx, by, bx, by + bh),
    (bx + bw, by, bx + bw, by + bh),
]:
    line(x0b, y0b, x1b, y1b, color="#888780", lw=0.8)

# ── Title & Legend ────────────────────────────────────────────────────────────
ax.text(
    MARGIN_L,
    total_h - MARGIN_T / 2,
    "SAFELAW MQP — Project Timeline",
    ha="left",
    va="center",
    fontsize=10,
    fontweight="bold",
    color=TEXT_DARK,
)

legend_items = [
    mpatches.Patch(facecolor=BLUE, label="Research / Data Pipeline"),
    mpatches.Patch(facecolor=TEAL, label="Design / Frontend"),
    mpatches.Patch(facecolor=AMBER, label="Retrieval Evaluation"),
]
ax.legend(
    handles=legend_items,
    loc="lower right",
    bbox_to_anchor=(1 - MARGIN_R / total_w, 0),
    fontsize=6.5,
    frameon=True,
    framealpha=0.9,
    edgecolor=GRID_COLOR,
    handlelength=1.2,
    handleheight=0.9,
    borderpad=0.6,
    labelspacing=0.4,
)

plt.tight_layout(pad=0)
plt.savefig(
    "safelaw_gantt.png",
    dpi=180,
    bbox_inches="tight",
    facecolor="white",
    edgecolor="none",
)
print("Saved safelaw_gantt.png")

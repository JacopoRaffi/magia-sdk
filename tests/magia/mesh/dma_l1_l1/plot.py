#!/usr/bin/env python3
"""Plot latency (bars) and goodput (lines) vs. buffer size, per Manhattan distance.

Usage: python plot_latency.py data.csv [--dtype int16] [--skip 1] [-o plot]
                              [--zoom N | --logy] [--show]
Saves: <prefix>_latency.png and <prefix>_goodput.png
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import ConnectionPatch, Rectangle
import pandas as pd

DTYPE_BYTES = {
    "int8": 1, "uint8": 1,
    "int16": 2, "uint16": 2, "float16": 2, "bfloat16": 2,
    "int32": 4, "uint32": 4, "float32": 4,
    "int64": 8, "uint64": 8, "float64": 8,
}


def mean_latency(cell, skip):
    """Average of a ';'-separated list of samples, ignoring the first `skip`."""
    vals = [float(v) for v in str(cell).split(";") if v.strip()]
    return np.mean(vals[skip:] or vals)


def format_size(n):
    for unit, div in (("MiB", 1 << 20), ("KiB", 1 << 10)):
        if n >= div:
            return f"{n / div:g} {unit}"
    return f"{n:g} B"


def add_zoom_inset(ax, table, labels, n):
    """Inset showing only the first `n` buffer sizes, with a box + connectors
    on the main axes marking the zoomed region. Bars keep the main colors."""
    n = min(n, len(table))
    colors = [c.patches[0].get_facecolor() for c in ax.containers]

    # The inset sits over the empty upper-left area (legend is further left).
    # Its right edge lines up with the right edge of the zoom box on the main
    # axes (as far as sensible), so the connector there doesn't cross tick labels.
    n_total = len(table)
    left = 0.17
    right = min(max(n / n_total, 0.45), 0.95)
    inset = ax.inset_axes([left, 0.40, right - left, 0.52])
    table.iloc[:n].plot(kind="bar", ax=inset, width=0.8, legend=False, color=colors)

    x0, x1 = -0.5, n - 0.5
    y1 = table.iloc[:n].to_numpy().max() * 1.1
    inset.set_xlim(x0, x1)
    inset.set_ylim(0, y1)
    inset.set_xticks(range(n))
    inset.set_xticklabels(labels[:n], rotation=45, ha="right", fontsize=7)
    inset.set_xlabel("")
    inset.tick_params(axis="y", labelsize=7)
    inset.grid(axis="y", alpha=0.3)
    inset.set_title(f"First {n} sizes", fontsize=8)

    # Zoom box on the main axes + two connectors up to the inset's bottom corners.
    # Drawn by hand (not indicate_inset_zoom) so it looks the same in every
    # matplotlib version.
    style = dict(color="0.3", lw=0.8, alpha=0.8)
    ax.add_artist(Rectangle((x0, 0), x1 - x0, y1, fill=False, **style))
    for x_main, x_inset in ((x0, 0.0), (x1, 1.0)):
        ax.add_artist(ConnectionPatch(
            xyA=(x_main, y1), coordsA=ax.transData,
            xyB=(x_inset, 0.0), coordsB=inset.transAxes, **style))


def make_plot(df, column, ylabel, kind, path, logy=False, zoom=0):
    """x = buffer size, one bar/line per Manhattan distance."""
    table = df.pivot_table(index="bytes", columns="manhattan", values=column)
    labels = [format_size(s) for s in table.index]
    table = table.reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    style = {"marker": "o"} if kind == "line" else {"width": 0.8}
    table.plot(kind=kind, ax=ax, logy=logy, **style)

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_xlabel("Buffer size")
    ax.set_ylabel(ylabel)
    ax.legend(title="Distance", loc="upper left")
    ax.grid(axis="y", alpha=0.3)
    if zoom:
        add_zoom_inset(ax, table, labels, zoom)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    print(f"Saved {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--dtype", default="int16", choices=sorted(DTYPE_BYTES))
    ap.add_argument("--skip", type=int, default=1, help="warm-up samples to drop")
    ap.add_argument("-o", "--output", default="plot", help="output file prefix")
    ap.add_argument("--logy", action="store_true", help="log y-axis on the latency plot")
    ap.add_argument("--zoom", type=int, default=0, metavar="N",
                    help="add an inset to the latency plot zooming on the first N "
                         "buffer sizes (linear axis only)")
    ap.add_argument("--show", action="store_true", help="open the plot windows too")
    args = ap.parse_args()
    if args.zoom and args.logy:
        ap.error("--zoom and --logy are alternatives; use one of them")

    df = pd.read_csv(args.csv)
    df = df[df["errors"] == 0].copy()  # .copy() avoids SettingWithCopyWarning
    df["bytes"] = df["len_elems"] * DTYPE_BYTES[args.dtype]
    df["latency"] = df["samples"].apply(mean_latency, skip=args.skip)
    df["goodput"] = df["bytes"] / df["latency"]

    make_plot(df, "latency", "Latency (cycles)", "bar",
              f"{args.output}_latency.png", logy=args.logy, zoom=args.zoom)
    make_plot(df, "goodput", "Goodput (bytes/cycle)", "line",
              f"{args.output}_goodput.png")
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
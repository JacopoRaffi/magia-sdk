#!/usr/bin/env python3
# Copyright 2026 ETH Zurich, University of Bologna and Fondazione Chips-IT.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

"""Grouped bar charts for the dma_line sweep: latency (cycles) and goodput (B/cycle).

One figure, one row per (axis,line) of the sweep, two columns:
left  = latency (cycles) per buffer size, grouped by link (src->dst)
right = goodput (B/cycle) per buffer size, grouped by link (src->dst)

Requires: pandas, numpy, matplotlib (pip install pandas numpy matplotlib)

Usage (from magia-sdk root):
  ./tests/magia/mesh/dma_line/plot_results.py [results/dma_line.csv]
      [--stat median|mean] [--out results/dma_line_plots.png] [--annotate]
"""

import argparse
import os
import sys


def human(nbytes):
    if nbytes >= 1024 * 1024:
        return f"{nbytes // (1024 * 1024)} MiB"
    if nbytes >= 1024:
        return f"{nbytes // 1024} KiB"
    return f"{nbytes} B"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv", nargs="?", default="results/dma_line.csv")
    ap.add_argument("--stat", choices=["median", "mean"], default="median")
    ap.add_argument("--out", default="results/dma_line_plots.png")
    ap.add_argument("--annotate", action="store_true", help="print values above the bars")
    args = ap.parse_args()

    try:
        import numpy as np
        import pandas as pd
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as e:
        sys.exit(f"missing python package: {e.name} -- pip install pandas numpy matplotlib")

    if not os.path.exists(args.csv):
        sys.exit(f"error: input file '{args.csv}' not found.")

    df = pd.read_csv(args.csv)
    if df.columns[0] != "axis":  # old CSV without axis/line columns
        df.insert(0, "axis", 0)
        df.insert(1, "line", 0)

    agg = np.median if args.stat == "median" else np.mean
    rows = []
    for _, r in df.iterrows():
        vals = [int(v) for v in str(r["samples"]).strip(";").split(";") if v != ""]
        if not vals:
            continue
        cycles = float(agg(vals))
        n = int(r["len_elems"])
        bytes_val = n * 2
        rows.append({
            "axis": int(r["axis"]),
            "line": int(r["line"]),
            "link": f"{int(r['src'])} -> {int(r['dst'])}",
            "n": n,
            "cycles": cycles,
            "goodput": bytes_val / cycles if cycles > 0 else 0.0,
            "errors": int(r["errors"]),
        })
    d = pd.DataFrame(rows)

    if d.empty:
        sys.exit("error: no valid data rows found in CSV.")

    groups = list(d.groupby(["axis", "line"]))
    num_groups = len(groups)

    fig, axes = plt.subplots(
        num_groups, 2,
        figsize=(14, 4.5 * num_groups),
        squeeze=False,
        constrained_layout=True,
    )

    for g, ((axis, line), gdf) in enumerate(groups):
        # Pivot table sorted naturally by element size 'n'
        # Sort links numerically by source, then destination.
        link_order = sorted(
            gdf["link"].unique(),
            key=lambda link: tuple(map(int, link.split(" -> "))),
        )

        lat = gdf.pivot_table(
            index="n", columns="link", values="cycles", aggfunc=args.stat
        ).reindex(columns=link_order)

        bw = gdf.pivot_table(
            index="n", columns="link", values="goodput", aggfunc=args.stat
        ).reindex(columns=link_order)

        # Human readable buffer size labels on X-axis
        x_labels = [human(n * 2) for n in lat.index]

        # Left plot: Latency
        ax_lat = axes[g, 0]
        lat.plot(kind="bar", ax=ax_lat, width=0.8)
        ax_lat.set_title(f"Latency [{args.stat}] (cycles) - {'row' if axis == 0 else 'column'} {line}")
        ax_lat.set_xlabel("Buffer Size")
        ax_lat.set_ylabel("Cycles")
        ax_lat.set_xticklabels(x_labels, rotation=45, ha="right")
        ax_lat.grid(axis="y", linestyle="--", alpha=0.5)
        ax_lat.legend(title="Link", bbox_to_anchor=(1.02, 1), loc="upper left")

        if args.annotate:
            for p in ax_lat.patches:
                val = p.get_height()
                if np.isfinite(val) and val > 0:
                    lbl = f"{val/1000:.1f}k" if val >= 1000 else f"{val:.0f}"
                    ax_lat.annotate(
                        lbl,
                        (p.get_x() + p.get_width() / 2.0, val),
                        ha="center", va="bottom",
                        fontsize=6, rotation=90, xytext=(0, 2),
                        textcoords="offset points"
                    )

        # Right plot: Goodput
        ax_bw = axes[g, 1]
        bw.plot(kind="bar", ax=ax_bw, width=0.8)
        err = int((gdf["errors"] > 0).sum())
        ttl = f"Goodput (B/cycle) - {'row' if axis == 0 else 'column'} {line}"
        if err:
            ttl += f"  [{err} links with ERRORS]"
        ax_bw.set_title(ttl, color="red" if err else "black")
        ax_bw.set_xlabel("Buffer Size")
        ax_bw.set_ylabel("Bytes / Cycle")
        ax_bw.set_xticklabels(x_labels, rotation=45, ha="right")
        ax_bw.grid(axis="y", linestyle="--", alpha=0.5)
        ax_bw.legend(title="Link", bbox_to_anchor=(1.02, 1), loc="upper left")

        if args.annotate:
            for p in ax_bw.patches:
                val = p.get_height()
                if np.isfinite(val) and val > 0:
                    ax_bw.annotate(
                        f"{val:.2f}",
                        (p.get_x() + p.get_width() / 2.0, val),
                        ha="center", va="bottom",
                        fontsize=6, rotation=90, xytext=(0, 2),
                        textcoords="offset points"
                    )

    # Automatically create output directory if missing
    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    fig.savefig(args.out, dpi=150)
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
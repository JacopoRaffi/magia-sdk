import sys
import io
import re
import argparse
import pandas as pd
from itertools import product
from util import *


def extract_df_from_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    match = re.search(r'START_DF\n(.*?)\nEND_DF', content, re.DOTALL)
    if not match:
        raise ValueError(f"Could not find START_DF / END_DF markers in: {filepath}")
    raw_csv = match.group(1).strip()

    return pd.read_csv(io.StringIO(raw_csv))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse DataFrames from sweep output files")
    parser.add_argument("basename",            help="Base name of the executable (e.g. gemv)")
    parser.add_argument("--tiles", type=int,   nargs='+', required=True, help="Tile counts (e.g. --tiles 2 4 8)")
    parser.add_argument("--M",     type=int,   nargs='+', required=True, help="M values (e.g. --M 1)")
    parser.add_argument("--N",     type=int,   nargs='+', required=True, help="N values (e.g. --N 128 256 512)")
    parser.add_argument("--K",     type=int,   nargs='+', required=True, help="K values (e.g. --K 128 256 512)")
    parser.add_argument("--out",   type=str,   default=None,             help="Output CSV path (default: csv_output/<basename>.csv)")
    args = parser.parse_args()

    out_path = args.out or f"./csv_output/{args.basename}.csv"

    all_dfs = []
    missing = []
    # columns are: total_cycles,redmule_cycles,l2_l1_cycles,l1_l1_cycles,M_SIZE,K_SIZE,N_SIZE,repetition,hartid
    for tiles, M, N, K in product(args.tiles, args.M, args.N, args.K):
        filepath = f"raw_output/{args.basename}/{args.basename}_T{tiles}_M{M}_N{N}_K{K}.txt"
        try:
            df = extract_df_from_file(filepath)
            df["mesh_dim"] = tiles
            #use the metric FLOPs/cycles
            df["flops"] = df.apply(
                lambda row: compute_flops(row["M_SIZE"], row["K_SIZE"], row["N_SIZE"]), 
                axis=1
            )
            df["flops_per_cycle"] = df["flops"] / df["total_cycles"]
            df["idle_sync_cycles"] = df["total_cycles"] - df["redmule_cycles"] - df["l2_l1_cycles"] - df["l1_l1_cycles"]
            all_dfs.append(df)
        except Exception as e:
            print(f"Configuration T{tiles}_M{M}_N{N}_K{K} is missing or malformed: {e}")
            missing.append(filepath)

    if not all_dfs:
        print("No data found — check your arguments and raw_output directory.")
        sys.exit(1)

    final_df = pd.concat(all_dfs, ignore_index=True)
    print(final_df)

    import os
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    final_df.to_csv(out_path, index=False)
    print(f"\nSaved to {out_path}")
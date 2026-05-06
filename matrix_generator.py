#!/usr/bin/env python3
"""
Generate a test.h file for Z = Y + X*W matrix operation.

Arrays:
  X      : M x N  (input)
  W      : N x K  (weights)
  Y      : M x K  (bias, added to result)
  Z      : M x K  (output = Y + X*W, computed in float32, truncated to float16)
  y_out  : M x N  (zero-initialized output buffer)
  id_mat : N x K  (identity matrix, optional)

All values stored as uint16_t raw float16 bits.
"""

import argparse
import numpy as np


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def to_fp16_hex(arr: np.ndarray) -> list[str]:
    """Convert a float32 numpy array to a list of hex uint16 strings."""
    fp16 = arr.astype(np.float16)
    raw  = fp16.view(np.uint16)
    return [f"0x{v:04x}" for v in raw.flatten()]


def format_array(values: list[str], cols: int = 64) -> str:
    """Format a flat list of hex strings into rows of `cols` entries."""
    lines = []
    for i in range(0, len(values), cols):
        chunk = values[i:i + cols]
        sep   = ", \n" if i + cols < len(values) else " \n"
        lines.append(", ".join(chunk) + sep)
    return "".join(lines)


def make_identity_fp16(n: int, k: int) -> np.ndarray:
    """Return an N x K identity-like matrix (1.0 on diagonal, 0 elsewhere)."""
    mat = np.zeros((n, k), dtype=np.float32)
    for i in range(min(n, k)):
        mat[i, i] = 1.0
    return mat


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate(
    M: int,
    N: int,
    K: int,
    seed: int       = 1,
    include_id: bool = False,
    out_path: str   = "test.h",
) -> None:

    rng = np.random.default_rng(seed)

    # Random small positive values in [0, 1)
    X = rng.random((M, N), dtype=np.float64).astype(np.float32)
    W = rng.random((N, K), dtype=np.float64).astype(np.float32)
    Y = rng.random((M, K), dtype=np.float64).astype(np.float32)

    # Compute Z = Y + X*W in float32, then truncate to float16
    Z = (Y + X @ W).astype(np.float32)

    # y_out is always zero-initialized
    y_out = np.zeros((M, N), dtype=np.float32)

    guard = f"_MAT_VEC_GEN_{M}x{N}x{K}_"

    lines = []

    # Header comment
    lines.append(
        f"// Auto-generated data (uint16_t) for Z = Y + X*W, "
        f"with X {M}x{N}, W {N}x{K}, Y {M}x{K} and Z {M}x{K}\n"
    )
    lines.append(
        "// Python computes in full precision, values are truncated to 16 bits when emitted\n"
    )
    lines.append(f"// RNG seed: {seed}\n\n")

    lines.append(f"#ifndef {guard}\n")
    lines.append(f"#define {guard}\n\n")

    lines.append(f"#define M_SIZE ({M})\n")
    lines.append(f"#define N_SIZE ({N})\n")
    lines.append(f"#define K_SIZE ({K})\n\n")

    def emit_array(name: str, type_str: str, data: np.ndarray) -> str:
        vals = to_fp16_hex(data)
        body = format_array(vals, cols=64)
        return f"extern uint16_t {name} [{type_str}] = {{\n{body}}};\n\n"

    lines.append(emit_array("y_out",  "M_SIZE*N_SIZE", y_out))
    lines.append(emit_array("x_inp",   "M_SIZE*N_SIZE", X))
    lines.append(emit_array("w_inp",   "N_SIZE*K_SIZE", W))
    lines.append(emit_array("y_inp",   "M_SIZE*K_SIZE", Y))
    lines.append(emit_array("z_out",  "M_SIZE*K_SIZE", Z))

    if include_id:
        id_mat = make_identity_fp16(N, K)
        lines.append(emit_array("id_mat", "N_SIZE*K_SIZE", id_mat))

    lines.append(f"#endif /*{guard}*/\n")

    with open(out_path, "w") as f:
        f.writelines(lines)

    print(f"Generated '{out_path}'  (M={M}, N={N}, K={K}, seed={seed}, id_mat={include_id})")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a test.h with float16 matrix data for Z = Y + X*W."
    )
    parser.add_argument("-M", type=int, required=True,  help="Number of rows of X (and Z)")
    parser.add_argument("-N", type=int, required=True,  help="Inner dimension (cols of X, rows of W)")
    parser.add_argument("-K", type=int, required=True,  help="Number of cols of W (and Z)")
    parser.add_argument("--seed",       type=int, default=1,         help="RNG seed (default: 1)")
    parser.add_argument("--id",         action="store_false",          help="Include identity matrix id_mat")
    parser.add_argument("--out",        type=str, default="test.h",  help="Output file path (default: test.h)")

    args = parser.parse_args()

    generate(
        M          = args.M,
        N          = args.N,
        K          = args.K,
        seed       = args.seed,
        include_id = args.id,
        out_path   = args.out,
    )
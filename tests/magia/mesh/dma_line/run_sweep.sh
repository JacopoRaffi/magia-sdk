#!/bin/sh
# Copyright 2026 ETH Zurich, University of Bologna and Fondazione Chips-IT.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0
#
# Usage (from magia-sdk root): ./tests/magia/mesh/dma_line/run_sweep.sh [platform] [out.csv] [tiles]

set -e

mkdir -p results

PLATFORM=${1:-gvsoc}
OUT=${2:-results/dma_line.csv}
TILES=${3:-16}
TEST_H="tests/magia/mesh/dma_line/include/test.h"
BACKUP="${TEST_H}.sweep_bak"
RUN_LOG="tests/magia/mesh/dma_line/sweep_run.log"

cp "$TEST_H" "$BACKUP"

restore() {
    mv "$BACKUP" "$TEST_H"
}
trap restore EXIT INT TERM

set_len() {
    sed -i "s/#define DMA_LINE_N_ELEMS ([0-9]*)/#define DMA_LINE_N_ELEMS ($1)/" "$TEST_H"
}

LENS="1 2 4 8 16 32 64 128 256 512 1024 2048 4096 8192 16384 32768 65536"

echo "axis,line,src,dst,manhattan,len_elems,samples,errors" > "$OUT"

make gvsoc tiles=$TILES

for ln in $LENS; do
    echo ""
    echo "===== row 0, len $ln elems ====="
    set_len "$ln"
    make clean build test=test_dma_line tiles=$TILES
    make run test=test_dma_line platform="$PLATFORM" tiles=$TILES 2>&1 | tee "$RUN_LOG"
    grep -a "^DF " "$RUN_LOG" | sed 's/^DF /0,0,/' >> "$OUT"
done

echo ""
echo "Results in $OUT"

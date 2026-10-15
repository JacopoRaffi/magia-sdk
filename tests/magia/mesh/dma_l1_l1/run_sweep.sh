#!/bin/sh
# Copyright 2026 ETH Zurich, University of Bologna and Fondazione Chips-IT.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0
#
# Usage (from magia-sdk root): ./tests/magia/mesh/dma_l1_l1/run_sweep.sh [platform]

set -e

mkdir -p results

PLATFORM=${1:-gvsoc}
OUT=${2:-results/dma_l1_l1.csv}
TEST_H="tests/magia/mesh/dma_l1_l1/include/test.h"
BACKUP="${TEST_H}.sweep_bak"
TEST_DIR="tests/magia/mesh/dma_l1_l1"
RUN_LOG="${TEST_DIR}/sweep_run.log"
TILES=16

cp "$TEST_H" "$BACKUP"

restore() {
    mv "$BACKUP" "$TEST_H"
}
trap restore EXIT INT TERM

set_dst() {
    sed -i "s/#define PING_PONG_DST_X ([0-9]*)/#define PING_PONG_DST_X ($1)/" "$TEST_H"
    sed -i "s/#define PING_PONG_DST_Y ([0-9]*)/#define PING_PONG_DST_Y ($2)/" "$TEST_H"
}

set_len() {
    sed -i "s/#define PING_PONG_N_ELEMS ([0-9]*)/#define PING_PONG_N_ELEMS ($1)/" "$TEST_H"
}

DISTS="1:1:0 2:1:1 4:2:2 8:4:4 16:8:8"
LENS="1 2 4 8 16 32 64 128 256 512 1024 2048 4096 8192 16384 32768 65536"

echo "src,dst,manhattan,len_elems,samples,errors" > "$OUT"

make gvsoc tiles=$TILES

for entry in $DISTS; do
    dist=$(echo "$entry" | cut -d: -f1)
    dx=$(echo "$entry" | cut -d: -f2)
    dy=$(echo "$entry" | cut -d: -f3)
    mdist=$((dx + dy))
    for ln in $LENS; do
        echo ""
        echo "===== label $dist -> PE ($dx,$dy) Manhattan $mdist, len $ln elems ====="
        set_dst "$dx" "$dy"
        set_len "$ln"
        make clean build test=test_dma_l1_l1 tiles=$TILES
        make run test=test_dma_l1_l1 platform="$PLATFORM" tiles=$TILES 2>&1 | tee "$RUN_LOG"
        grep -a "^DF " "$RUN_LOG" | sed 's/^DF //' >> "$OUT"
    done
done

echo ""
echo "Results in $OUT"

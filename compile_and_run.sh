#!/bin/bash

NAME=$1
MATRIX_GEN=$2 # yes or no (if yes call the script to generate the matrices)

if [ -z "$NAME" ]; then
    echo "Usage: $0 <name_of_executable>"
    exit 1
fi

if [ -z "$MATRIX_GEN" ]; then
    echo "Usage: $0 <name_of_executable> <matrix_gen (yes/no)>"
    exit 1
fi

# -----------------------------------------------------------------------
# Sweep parameters — edit these to change the configs
# -----------------------------------------------------------------------
TILES_LIST=(4)
M_LIST=(1) # 1024 2048)
N_LIST=(1) # 1024 2048)
K_LIST=(1) # 1024 2048)
SEED=1
# -----------------------------------------------------------------------

RAW_OUTPUT_DIR="./raw_output/${NAME}"
LOG_DIR="./sweep_logs"
FAIL_LOG="${LOG_DIR}/failed_configs.txt"

mkdir -p "$RAW_OUTPUT_DIR"
mkdir -p "$LOG_DIR"
> "$FAIL_LOG"

export PATH=$HOME/v1.0.16-pulp-riscv-gcc-ubuntu-18/bin/:$PATH

TOTAL=0
PASSED=0
FAILED=0

for TILES in "${TILES_LIST[@]}"; do
    make gvsoc tiles=$TILES
    for M in "${M_LIST[@]}"; do
        for N in "${N_LIST[@]}"; do
            for K in "${K_LIST[@]}"; do

                if [ "$K" -ne "$N" ]; then # skip non-square configs for now...
                    continue
                fi

                TOTAL=$((TOTAL + 1))
                OUTPUT_NAME="${NAME}_T${TILES}_M${M}_N${N}_K${K}"
                CONFIG="tiles=${TILES} M=${M} N=${N} K=${K}"

                # Generate test.h
                if [ "$MATRIX_GEN" == "yes" ]; then
                    echo "Generating matrices for ${CONFIG}..."
                    python3 matrix_generator.py \
                    -M "$M" -N "$N" -K "$K" \
                    --seed "$SEED" \
                    --out "./tests/magia/mesh/${NAME}/include/test.h"

                if [ $? -ne 0 ]; then
                    echo "[FAIL] matrix_generator.py failed for ${CONFIG}"
                    echo "$OUTPUT_NAME  (generator failed)" >> "$FAIL_LOG"
                    FAILED=$((FAILED + 1))
                    exit 1
                fi
                else
                    echo "Skipping matrix generation for ${CONFIG} (MATRIX_GEN=no)"
                fi

cat > "./tests/magia/mesh/CMakeLists.txt" <<EOF
# Copyright 2025 University of Bologna.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0
#
# Alberto Dequino <alberto.dequino@unibo.it>
add_subdirectory(${NAME})
EOF

                make clean build target_platform=magia_v2 tiles=$TILES spatz=0

                if [ $? -ne 0 ]; then
                    echo "[FAIL] build failed for ${CONFIG}"
                    echo "$OUTPUT_NAME  (build failed)" >> "$FAIL_LOG"
                    FAILED=$((FAILED + 1))
                    exit 1
                fi

                echo "============================================="
                echo " Running: ${CONFIG}"
                echo "============================================="

                # Run
                make run_profiling test=test_brah tiles=4 platform=gvsoc profile_tile=0
                # make run test="test_${NAME}" platform=gvsoc tiles=$TILES > "${RAW_OUTPUT_DIR}/${OUTPUT_NAME}.txt"

                if [ $? -ne 0 ]; then
                    echo "[FAIL] run failed for ${CONFIG}: error code $?"
                    echo "$OUTPUT_NAME  (run failed)" >> "$FAIL_LOG"
                    FAILED=$((FAILED + 1))
                    continue
                fi

                echo "[OK] ${CONFIG}"
                PASSED=$((PASSED + 1))

            done
        done
    done
done

echo ""
echo "============================================="
echo " Sweep complete: ${PASSED}/${TOTAL} passed"
if [ "$FAILED" -gt 0 ]; then
    echo "${FAILED} failed — see ${FAIL_LOG}"
fi
echo "============================================="
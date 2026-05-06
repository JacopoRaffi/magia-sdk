#!/bin/bash

NAME=$1

if [ -z "$NAME" ]; then
    echo "Usage: $0 <name_of_executable>"
    exit 1
fi

# -----------------------------------------------------------------------
# Sweep parameters — edit these to change the configs
# -----------------------------------------------------------------------
TILES_LIST=(4)
M_LIST=(1) 
N_LIST=(128 256 512 1024)
K_LIST=(128 256 512 1024)
# TILES_LIST=(16)  # for mm_os just re-do from 16x16
# M_LIST=(128)
# N_LIST=(64 128)
# K_LIST=(64 128)
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

                if [ "$K" -ne "$N" ]; then # just for GEMV cases, skip non-square configs for now...
                    continue
                fi

                TOTAL=$((TOTAL + 1))
                OUTPUT_NAME="${NAME}_T${TILES}_M${M}_N${N}_K${K}"
                CONFIG="tiles=${TILES} M=${M} N=${N} K=${K}"

                # Generate test.h
                python3 matrix_generator.py \
                    -M "$M" -N "$N" -K "$K" \
                    --seed "$SEED" \
                    --out "./tests/magia/mesh/${NAME}/include/test.h"

                if [ $? -ne 0 ]; then
                    echo "[FAIL] matrix_generator.py failed for ${CONFIG}"
                    echo "$OUTPUT_NAME  (generator failed)" >> "$FAIL_LOG"
                    FAILED=$((FAILED + 1))
                    continue
                fi

                make clean build target_platform=magia_v2 tiles=$TILES

                if [ $? -ne 0 ]; then
                    echo "[FAIL] build failed for ${CONFIG}"
                    echo "$OUTPUT_NAME  (build failed)" >> "$FAIL_LOG"
                    FAILED=$((FAILED + 1))
                    continue
                fi

                echo "============================================="
                echo " Running: ${CONFIG}"
                echo "============================================="

                # Run
                make run test="test_${NAME}" platform=gvsoc tiles=$TILES > "${RAW_OUTPUT_DIR}/${OUTPUT_NAME}.txt"

                if [ $? -ne 0 ]; then
                    echo "[FAIL] run failed for ${CONFIG}"
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
    echo " ${FAILED} failed — see ${FAIL_LOG}"
fi
echo "============================================="
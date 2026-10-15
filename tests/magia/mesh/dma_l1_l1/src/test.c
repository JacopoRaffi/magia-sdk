// Copyright 2026 ETH Zurich, University of Bologna and Fondazione Chips-IT.
// Licensed under the Apache License, Version 2.0, see LICENSE for details.
// SPDX-License-Identifier: Apache-2.0

#include <stdint.h>
#include "test.h"

#include "tile.h"
#include "fsync.h"
#include "mg_idma.h"

#define WAIT_MODE WFE

#define PAY_LEN (PING_PONG_N_ELEMS * 2)
#define PATTERN (0xABCD)

int main(void)
{
    perf_init();
    uint32_t hartid = get_hartid();

    idma_init();
    fsync_init();
    eu_init();
    eu_clear_events(0xFFFFFFFF);
    eu_fsync_init(0);
    eu_idma_init(0);

    uint32_t src = GET_ID(PING_PONG_SRC_Y, PING_PONG_SRC_X);
    uint32_t dst = GET_ID(PING_PONG_DST_Y, PING_PONG_DST_X);

    int is_src = (hartid == src);
    int is_dst = (hartid == dst);

    uint32_t errors = 0;
    uint32_t base   = get_l1_base(hartid);

    volatile uint16_t *l1 = (volatile uint16_t *)base;

    if (is_dst)
        for (uint32_t i = 0; i < PING_PONG_N_ELEMS; i++)
            l1[i] = 0;

    fsync_sync_global();
    eu_fsync_wait(WAIT_MODE);

    uint32_t samples[PING_PONG_N_ITERS];

    if (is_src) {
        uint32_t peer_base = get_l1_base(dst);
        mg_event_t evt;

        for (uint32_t it = 0; it < PING_PONG_N_ITERS; it++) {
            for (uint32_t i = 0; i < PING_PONG_N_ELEMS; i++)
                l1[i] = (uint16_t)(PATTERN + it);

            uint32_t t0 = perf_get_cycles();

            mg_idma_memcpy_1d(WAIT_MODE, 1, peer_base, base, PAY_LEN, &evt, NULL);
            mg_idma_wait(1, WAIT_MODE, &evt);

            samples[it] = perf_get_cycles() - t0;
        }
    }

    fsync_sync_global();
    eu_fsync_wait(WAIT_MODE);

    if (is_dst) {
        for (uint32_t i = 0; i < PING_PONG_N_ELEMS; i++) {
            if (l1[i] != (uint16_t)(PATTERN + PING_PONG_N_ITERS - 1)) {
                errors++;
                break;
            }
        }
        if (errors)
            printf("ERR dst %d: payload check failed\n", dst);
    }

    if (is_src) {
        uint32_t dx    = PING_PONG_DST_X > PING_PONG_SRC_X ? PING_PONG_DST_X - PING_PONG_SRC_X
                                                           : PING_PONG_SRC_X - PING_PONG_DST_X;
        uint32_t dy    = PING_PONG_DST_Y > PING_PONG_SRC_Y ? PING_PONG_DST_Y - PING_PONG_SRC_Y
                                                           : PING_PONG_SRC_Y - PING_PONG_DST_Y;
        uint32_t mdist = dx + dy;
        printf("DF %d,%d,%d,%d,", src, dst, mdist, PING_PONG_N_ELEMS);
        for (uint32_t k = 0; k < PING_PONG_N_ITERS; k++)
            printf("%d;", samples[k]);
        printf(",%d\n", errors);
    }

    return (int)errors;
}

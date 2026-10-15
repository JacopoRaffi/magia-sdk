// Copyright 2026 ETH Zurich, University of Bologna and Fondazione Chips-IT.
// Licensed under the Apache License, Version 2.0, see LICENSE for details.
// SPDX-License-Identifier: Apache-2.0

#ifndef _TEST_PING_PONG_INCLUDE_GUARD_
#define _TEST_PING_PONG_INCLUDE_GUARD_

#include <stdint.h>

#define PING_PONG_SRC_X (0)
#define PING_PONG_SRC_Y (0)

#define PING_PONG_DST_X (1)
#define PING_PONG_DST_Y (0)

#define PING_PONG_N_ELEMS (8)

#if (PING_PONG_N_ELEMS & (PING_PONG_N_ELEMS - 1)) != 0
#error "PING_PONG_N_ELEMS must be a power of 2"
#endif

#define PING_PONG_N_ITERS (5)

#endif //_TEST_PING_PONG_INCLUDE_GUARD_

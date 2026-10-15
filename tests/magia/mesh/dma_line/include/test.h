// Copyright 2026 ETH Zurich, University of Bologna and Fondazione Chips-IT.
// Licensed under the Apache License, Version 2.0, see LICENSE for details.
// SPDX-License-Identifier: Apache-2.0

#ifndef _TEST_DMA_LINE_INCLUDE_GUARD_
#define _TEST_DMA_LINE_INCLUDE_GUARD_

#include <stdint.h>

#define DMA_LINE_N_ELEMS (64)

#if (DMA_LINE_N_ELEMS & (DMA_LINE_N_ELEMS - 1)) != 0
#error "DMA_LINE_N_ELEMS must be a power of 2"
#endif

#define DMA_LINE_N_ITERS (5)

#endif //_TEST_DMA_LINE_INCLUDE_GUARD_

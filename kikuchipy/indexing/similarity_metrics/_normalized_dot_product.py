# -*- coding: utf-8 -*-
# Copyright 2019-2021 The kikuchipy developers
#
# This file is part of kikuchipy.
#
# kikuchipy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kikuchipy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kikuchipy. If not, see <http://www.gnu.org/licenses/>.

import dask.array as da
import numba as nb
import numpy as np

from kikuchipy.indexing.similarity_metrics._similarity_metric import SimilarityMetric
from kikuchipy.indexing.similarity_metrics._normalized_cross_correlation import (
    _einsum_signature,
)


class NormalizedDotProductMetric(SimilarityMetric):
    @property
    def einsum_signature(self) -> str:
        return _einsum_signature(self.experimental_navigation_dimension)

    @property
    def prepare_chunk_simulated_func(self):
        if self.dtype == np.float32:
            return _prepare_simulated_patterns1d_float32
        else:
            return _prepare_simulated_patterns1d_float64

    def prepare_all_experimental(
        self, patterns: da.Array, n_per_iteration: int
    ) -> da.Array:
        patterns = patterns.astype(self.dtype)

        n_experimental = int(
            np.prod(patterns.shape[: self.experimental_navigation_dimension])
        )
        patterns = patterns.reshape((n_experimental, -1))

        if not isinstance(self.signal_mask, int):
            patterns = patterns[:, self.signal_mask]

        if self.can_rechunk:
            patterns = self.rechunk(patterns, n_per_iteration)

        patterns_norm = da.sqrt(da.sum(da.square(patterns), axis=1, keepdims=True))
        patterns = patterns / patterns_norm

        return patterns

    def prepare_chunk_simulated(self, patterns: np.ndarray) -> np.ndarray:
        if not isinstance(self.signal_mask, int):
            patterns = patterns[:, self.signal_mask]
        patterns = self.prepare_chunk_simulated_func(patterns)
        return patterns

    def compare(self, experimental: da.Array, simulated: np.ndarray) -> da.Array:
        return da.einsum(
            self.einsum_signature,
            experimental,
            simulated,
            optimize=True,
            dtype=self.dtype,
        )


@nb.jit("float32[:](float32[:])", cache=True, nogil=True, nopython=True)
def _normalize_pattern1d_float32(pattern: np.ndarray) -> np.ndarray:
    pattern_norm = np.sqrt(np.sum(np.square(pattern)))
    return pattern / pattern_norm


@nb.jit("float64[:](float64[:])", cache=True, nogil=True, nopython=True)
def _normalize_pattern1d_float64(pattern: np.ndarray) -> np.ndarray:
    pattern_norm = np.sqrt(np.sum(np.square(pattern)))
    return pattern / pattern_norm


@nb.jit("float32[:, :](float32[:, :])", cache=True, nogil=True, nopython=True)
def _prepare_simulated_patterns1d_float32(sim: np.ndarray) -> np.ndarray:
    simulated_prepared = np.zeros_like(sim)
    for i in nb.prange(sim.shape[0]):
        simulated_prepared[i] = _normalize_pattern1d_float32(sim[i])
    return simulated_prepared


@nb.jit("float64[:, :](float64[:, :])", cache=True, nogil=True, nopython=True)
def _prepare_simulated_patterns1d_float64(sim: np.ndarray) -> np.ndarray:
    simulated_prepared = np.zeros_like(sim)
    for i in nb.prange(sim.shape[0]):
        simulated_prepared[i] = _normalize_pattern1d_float64(sim[i])
    return simulated_prepared

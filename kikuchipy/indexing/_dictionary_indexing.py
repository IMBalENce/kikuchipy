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

"""Private tools for dictionary indexing of experimental patterns to a
dictionary of simulated patterns with known orientations.
"""

from typing import ClassVar, Tuple, Union

import dask.array as da
from dask.diagnostics import ProgressBar
import numpy as np
from orix.crystal_map import create_coordinate_arrays, CrystalMap
from tqdm import tqdm

from kikuchipy.indexing.similarity_metrics import SimilarityMetric


def _dictionary_indexing(
    experimental: Union[np.ndarray, da.Array],
    experimental_nav_shape: tuple,
    dictionary: Union[np.ndarray, da.Array],
    step_sizes: tuple,
    dictionary_xmap: CrystalMap,
    metric: SimilarityMetric,
    keep_n: int,
    n_per_iteration: int,
) -> CrystalMap:
    """Dictionary indexing of experimental to a dictionary of simulated
    patterns of known orientations.

    See :meth:`~kikuchipy.signals.EBSD.dictionary_indexing`.

    Parameters
    ----------
    experimental
    experimental_nav_shape
    dictionary
    step_sizes
    dictionary_xmap
    metric
    keep_n
    n_per_iteration

    Returns
    -------
    xmap
    """
    dictionary_size = dictionary.shape[0]
    n_experimental = int(np.prod(experimental_nav_shape))
    keep_n = min(keep_n, dictionary_size)
    n_iterations = dictionary_size // n_per_iteration

    experimental = metric.prepare_experimental(experimental)
    dictionary = dictionary.reshape((dictionary.shape[0], -1))

    phase_name = dictionary_xmap.phases.names[0]
    if phase_name is None:
        phase_name = ""
    print(
        _dictionary_indexing_info_message(
            metric=metric,
            n_experimental=n_experimental,
            dictionary_size=dictionary_size,
            n_iterations=n_iterations,
            phase_name=phase_name,
        )
    )

    if dictionary_size == n_per_iteration:
        simulation_indices, scores = _match_chunk(
            experimental,
            dictionary,
            keep_n=keep_n,
            metric=metric,
        )
        with ProgressBar():
            simulation_indices, scores = da.compute(simulation_indices, scores)
    else:
        simulation_indices = np.zeros((n_experimental, keep_n), dtype=np.int32)
        scores = np.full((n_experimental, keep_n), metric.sign, dtype=metric.dtype)

        lazy_dictionary = isinstance(dictionary, da.Array)

        negative_sign = -metric.sign

        chunk_starts = np.cumsum([0] + [n_per_iteration] * (n_iterations - 1))
        chunk_ends = np.cumsum([n_per_iteration] * n_iterations)
        chunk_ends[-1] = max(chunk_ends[-1], dictionary_size)
        for start, end in tqdm(zip(chunk_starts, chunk_ends), total=n_iterations):
            if lazy_dictionary:
                simulated = dictionary[start:end].compute()
            else:
                simulated = dictionary[start:end]

            simulation_indices_i, scores_i = _match_chunk(
                experimental,
                simulated,
                keep_n=min(keep_n, end - start),
                metric=metric,
            )

            simulation_indices_i, scores_i = da.compute(simulation_indices_i, scores_i)
            simulation_indices_i += start

            all_scores = np.hstack((scores, scores_i))
            all_simulation_indices = np.hstack(
                (simulation_indices, simulation_indices_i)
            )
            best_indices = np.argsort(negative_sign * all_scores, axis=1)[:, :keep_n]
            scores = np.take_along_axis(all_scores, best_indices, axis=1)
            simulation_indices = np.take_along_axis(
                all_simulation_indices, best_indices, axis=1
            )

    coordinate_arrays, _ = create_coordinate_arrays(
        shape=experimental_nav_shape, step_sizes=step_sizes
    )
    xmap = CrystalMap(
        rotations=dictionary_xmap.rotations[simulation_indices],
        phase_list=dictionary_xmap.phases_in_data,
        prop={"scores": scores, "simulation_indices": simulation_indices},
        **coordinate_arrays,
    )

    return xmap


def _match_chunk(
    experimental: Union[np.ndarray, da.Array],
    simulated: Union[np.ndarray, da.Array],
    keep_n: int,
    metric: SimilarityMetric,
) -> Tuple[da.Array, da.Array]:
    """Match all experimental patterns to part of or the entire
    dictionary of simulated patterns.

    Parameters
    ----------
    experimental
    simulated
    keep_n
    metric

    Returns
    -------
    simulation_indices
    scores
    """
    simulated = metric.prepare_dictionary(simulated)

    similarities = metric.match(experimental, simulated)

    simulation_indices = similarities.argtopk(keep_n, axis=-1)
    scores = similarities.topk(keep_n, axis=-1)
    out_shape = (-1, keep_n)
    simulation_indices = simulation_indices.reshape(out_shape)
    scores = scores.reshape(out_shape)

    return simulation_indices, scores


def _dictionary_indexing_info_message(
    metric: ClassVar,
    n_experimental: int,
    dictionary_size: int,
    n_iterations: int,
    phase_name: str,
) -> str:
    """Return a message with useful dictionary indexing information.

    Parameters
    ----------
    metric : SimilarityMetric
    n_experimental
    dictionary_size
    n_iterations
    phase_name
    Returns
    -------
    msg
        Message with useful dictionary indexing information.
    """
    return (
        "Dictionary indexing information:\n"
        f"\tPhase name: {phase_name}\n"
        f"\tMatching {n_experimental} experimental pattern(s) to {dictionary_size} "
        f"dictionary pattern(s) in {n_iterations} iteration(s)\n"
        f"\t{metric}"
    )

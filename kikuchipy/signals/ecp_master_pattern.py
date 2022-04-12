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

from hyperspy._signals.signal2d import Signal2D

from kikuchipy.signals._kikuchi_master_pattern import (
    KikuchiMasterPattern,
    LazyKikuchiMasterPattern,
)


class ECPMasterPattern(KikuchiMasterPattern, Signal2D):
    """Simulated Electron Channeling Pattern (ECP) master pattern.

    This class extends HyperSpy's Signal2D class for ECP master
    patterns. Methods inherited from HyperSpy can be found in the
    HyperSpy user guide. See the docstring of
    :class:`hyperspy.signal.BaseSignal` for a list of additional
    attributes.
    """

    _signal_type = "ECPMasterPattern"
    _alias_signal_types = ["ecp_master_pattern"]


class LazyECPMasterPattern(LazyKikuchiMasterPattern, ECPMasterPattern):
    """Lazy implementation of the :class:`ECPMasterPattern` class.

    This class extends HyperSpy's LazySignal2D class for ECP master
    patterns. Methods inherited from HyperSpy can be found in the
    HyperSpy user guide. See docstring of :class:`ECPMasterPattern`
    for attributes and methods.
    """

    pass
#!/usr/bin/python
#-*- coding: utf-8 -*-

# =========================================================================
#   Program:   iota2
#
#   Copyright (c) CESBIO. All rights reserved.
#
#   See LICENSE for details.
#
#   This software is distributed WITHOUT ANY WARRANTY; without even
#   the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the above copyright notices for more information.
#
# =========================================================================

import os
import logging
import fileUtils as fut

logger = logging.getLogger(__name__)


def GetAugmentationSamplesParameters(IOTA2_dir):
    """ read the /learningSample directory

    parse the directory /learningSamples and return a list of all sqlite files

    Parameter
    ---------

    IOTA2_dir : string
        absolute path to the IOTA2's directory

    Example
    -------

    ls /IOTA2/learningSamples
    Samples_region_2_seed0_learn.sqlite
    Samples_region_2_seed1_learn.sqlite
    Samples_region_1_seed0_learn.sqlite
    Samples_region_1_seed1_learn.sqlite

    >>> GetAugmentationSamplesParameters("/IOTA2")
        [Samples_region_1_seed0_learn.sqlite, Samples_region_2_seed0_learn.sqlite,
         Samples_region_1_seed1_learn.sqlite, Samples_region_2_seed1_learn.sqlite]

    Return
    ------
    list
        a list of sqlite files containing samples
    """
    IOTA2_dir_learningSamples = os.path.join(IOTA2_dir, "learningSamples")
    return fut.FileSearch_AND(IOTA2_dir_learningSamples, True, ".sqlite")


def AugmentationSamples(samples, workingDirectory=None):
    """
    """
    print samples
    pause = raw_input("pause")
    pass


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
    """
    """
    IOTA2_dir_learningSamples = os.path.join(IOTA2_dir, "learningSamples")
    return fut.FileSearch_AND(IOTA2_dir_learningSamples, True, ".sqlite")


def AugmentationSamples(samples, workingDirectory=None):
    """
    """
    print samples
    pause = raw_input("pause")
    pass


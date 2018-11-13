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
import shutil
from Common import ServiceConfigFile as SCF


def GenerateDirectories(cfg):
    """
    generate IOTA2 output directories
    """
    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    root = cfg.getParam('chain', 'outputPath')
    rm_PathTEST = cfg.getParam("chain", "remove_outputPath")
    start_step = cfg.getParam("chain", "firstStep")

    if os.path.exists(root) and root != "/" and rm_PathTEST and start_step == "init":
        shutil.rmtree(root,ignore_errors=False)
    os.mkdir(root)
    if os.path.exists(root+"/logs"):
        shutil.rmtree(root+"/logs")
    os.mkdir(root+"/logs")
    if os.path.exists(root+"/samplesSelection"):
        shutil.rmtree(root+"/samplesSelection")
    os.mkdir(root+"/samplesSelection")
    if os.path.exists(root+"/model"):
        shutil.rmtree(root+"/model")
    os.mkdir(root+"/model")
    if os.path.exists(root+"/formattingVectors"):
        shutil.rmtree(root+"/formattingVectors")
    os.mkdir(root+"/formattingVectors")
    if os.path.exists(root+"/config_model"):
        shutil.rmtree(root+"/config_model")
    os.mkdir(root+"/config_model")
    if os.path.exists(root+"/envelope"):
        shutil.rmtree(root+"/envelope")
    os.mkdir(root+"/envelope")
    if os.path.exists(root+"/classif"):
        shutil.rmtree(root+"/classif")
    os.mkdir(root+"/classif")
    if os.path.exists(root+"/shapeRegion"):
        shutil.rmtree(root+"/shapeRegion")
    os.mkdir(root+"/shapeRegion")
    if os.path.exists(root+"/final"):
        shutil.rmtree(root+"/final")
    os.mkdir(root+"/final")
    os.mkdir(root+"/final/simplification")
    os.mkdir(root+"/final/simplification/tiles")
    os.mkdir(root+"/final/simplification/vectors")    
    os.mkdir(root+"/final/simplification/tmp")
    if os.path.exists(root+"/features"):
        shutil.rmtree(root+"/features")
    os.mkdir(root+"/features")
    if os.path.exists(root+"/dataRegion"):
        shutil.rmtree(root+"/dataRegion")
    os.mkdir(root+"/dataRegion")
    if os.path.exists(root+"/learningSamples"):
        shutil.rmtree(root+"/learningSamples")
    os.mkdir(root+"/learningSamples")
    if os.path.exists(root+"/dataAppVal"):
        shutil.rmtree(root+"/dataAppVal")
    os.mkdir(root+"/dataAppVal")
    if os.path.exists(root+"/stats"):
        shutil.rmtree(root+"/stats")
    os.mkdir(root+"/stats")
    
    if os.path.exists(root+"/cmd"):
        shutil.rmtree(root+"/cmd")
    os.mkdir(root+"/cmd")
    os.mkdir(root+"/cmd/stats")
    os.mkdir(root+"/cmd/train")
    os.mkdir(root+"/cmd/cla")
    os.mkdir(root+"/cmd/confusion")
    os.mkdir(root+"/cmd/features")
    os.mkdir(root+"/cmd/fusion")
    os.mkdir(root+"/cmd/splitShape")

    merge_final_classifications = cfg.getParam('chain', 'merge_final_classifications')
    if merge_final_classifications:
        if os.path.exists(root+"/final/merge_final_classifications"):
            shutil.rmtree(root+"/final/merge_final_classifications")
        os.mkdir(root+"/final/merge_final_classifications")

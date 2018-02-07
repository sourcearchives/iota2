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

import argparse,os,shutil,sys

def GenerateDirectories(root):

    if os.path.exists(root):
        shutil.rmtree(root)
    os.mkdir(root)
    if os.path.exists(root+"/model"):
        shutil.rmtree(root+"/model")
    os.mkdir(root+"/model")
    if os.path.exists(root+"/formattingVectors"):
        shutil.rmtree(root+"/formattingVectors")
    os.mkdir(root+"/formattingVectors")
    if os.path.exists(root+"/metaData"):
        shutil.rmtree(root+"/metaData")
    os.mkdir(root+"/metaData")
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
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "This function creates directories for classifications")
    parser.add_argument("-root",dest = "root",help ="path where all directories will be create",required=True)
    args = parser.parse_args()

    GenerateDirectories(args.root)



















































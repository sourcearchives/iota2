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

import shutil
import sys
import os
import argparse
import numpy as np
import time
import otbAppli
import gdal


def clumpAndStackClassif(path, raster, outfilename, ram, out, float64 = False):

    begin_clump = time.time() 
    
    # Clump Classif with OTB segmentation algorithm
    clumpAppli = otbAppli.CreateClumpApplication(raster, 'distance<1', ram, 'uint32', os.path.join(path, 'clump.tif'))
    clumpAppli.Execute()

    # Add 300 to all clump ID    
    bandMathAppli = otbAppli.CreateBandMathApplication(clumpAppli, 'im1b1+300', ram, 'uint32', os.path.join(path, 'clump300.tif'))
    bandMathAppli.Execute()

    clumptime = time.time()
    print " ".join([" : ".join(["Clump : ", str(clumptime - begin_clump)]), "seconds"])
    
    # check exceed limit of float32 (23 bits mantissa)
    bandMathAppli.ExecuteAndWriteOutput()
    clump = gdal.Open(os.path.join(path, 'clump300.tif'), 0)
    clump_band = clump.GetRasterBand(1)
    clump_data = clump_band.ReadAsArray()
    
    maxId = np.amax(clump_data)
        
    if maxId > 2**23:
        print "Clump result exceed float32 mantissa limit (23 bits), risk of duplicate id in clump raster"
    
    if not float64:
        dataRamAppli = otbAppli.CreateBandMathApplication(raster, 'im1b1', ram, 'uint8')
        dataRamAppli.Execute()
        
        concatImages = otbAppli.CreateConcatenateImagesApplication([dataRamAppli, bandMathAppli], ram, 'uint32', os.path.join(path, outfilename))
        concatImages.ExecuteAndWriteOutput()
        
        concattime = time.time()
        print " ".join([" : ".join(["Regularized and Clumped rasters concatenation : ", str(concattime - clumptime)]), "seconds"])

        shutil.copyfile(os.path.join(path, outfilename), os.path.join(out, outfilename))
        
    else:
        command = '/work/OT/theia/oso/OTB/otb_superbuild/iotaDouble/'\
                  'iota2ConcatenateImages %s %s %s'%((raster, \
                                                      os.path.join(path, 'clump300.tif'), \
                                                      os.path.join(path, outfilename)))

        try:
            os.system(command)
            concattime = time.time()
            print " ".join([" : ".join(["Regularized and Clumped rasters concatenation : ", str(concattime - clumptime)]), "seconds"])
            shutil.copyfile(os.path.join(path, outfilename), os.path.join(out, outfilename))
        except:
            print "Application 'iota2ConcatenateImages' does not exist"
            sys.exit()

    
    
    

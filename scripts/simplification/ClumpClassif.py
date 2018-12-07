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

"""
Generete clumps raster from classification raster file
"""

import sys
import os
import argparse
import time
import shutil
import logging
logger = logging.getLogger(__name__)
import numpy as np
import gdal

try:
    from Common import Utils
    from Common import OtbAppBank
except ImportError:
    raise ImportError('Iota2 not well configured / installed')

def clumpAndStackClassif(path, raster, outpath, ram, float64 = False, exe64 = "", logger=logger):

    begin_clump = time.time()

    # split path and file name of outfilename
    out = os.path.dirname(outpath)
    outfilename = os.path.basename(outpath)

    # Clump Classif with OTB segmentation algorithm
    clumpAppli = OtbAppBank.CreateClumpApplication({"in" : raster,
                                                 "filter.cc.expr" : 'distance<1',
                                                 "ram" : str(0.2 * float(ram)),
                                                 "pixType" : 'uint32',
                                                 "mode" : "raster",
                                                 "filter" : "cc",
                                                 "mode.raster.out" : os.path.join(path, 'clump.tif')})
    
    if not float64:
        clumpAppli.Execute()

        clumptime = time.time()
        logger.info(" ".join([" : ".join(["Input raster well clumped : ", str(clumptime - begin_clump)]), "seconds"]))
        
        # Add 300 to all clump ID    
        bandMathAppli = OtbAppBank.CreateBandMathApplication({"il": clumpAppli,
                                                            "exp": 'im1b1+300', 
                                                            "ram": str(0.2 * float(ram)), 
                                                            "pixType": 'uint32', 
                                                            "out": os.path.join(path, 'clump300.tif')})
        bandMathAppli.Execute()

        dataRamAppli = OtbAppBank.CreateBandMathApplication({"il": raster,
                                                           "exp": 'im1b1',
                                                           "ram": str(0.2 * float(ram)),
                                                           "pixType": 'uint8'})
        dataRamAppli.Execute()
        
        concatImages = OtbAppBank.CreateConcatenateImagesApplication({"il" : [dataRamAppli, bandMathAppli],
                                                                    "ram" : str(0.2 * float(ram)),
                                                                    "pixType" : 'uint32',
                                                                    "out" : os.path.join(path, outfilename)})
        concatImages.ExecuteAndWriteOutput()
        
        concattime = time.time()
        logger.info(" ".join([" : ".join(["Regularized and Clumped rasters concatenation : ", str(concattime - clumptime)]), "seconds"]))

        shutil.copyfile(os.path.join(path, outfilename), os.path.join(out, outfilename))
        
    else:
        clumpAppli.ExecuteAndWriteOutput()
        
        command = '%s/iota2BandMath %s "%s" %s %s'%(exe64, \
                                                    os.path.join(path, 'clump.tif'), \
                                                    "im1b1+300", \
                                                    os.path.join(path, 'clump300.tif'), \
                                                    10)
        try:
            Utils.run(command)            
            clumptime = time.time()
            logger.info(" ".join([" : ".join(["Input raster well clumped : ", str(clumptime - begin_clump)]), "seconds"]))
        except:
            logger.error("Application 'iota2BandMath' for 64 bits does not exist, please change 64 bits binaries path")
            sys.exit()
            
        command = '%s/iota2ConcatenateImages %s %s %s %s'%((exe64,
                                                            raster, \
                                                            os.path.join(path, 'clump300.tif'), \
                                                            os.path.join(path, outfilename),
                                                            10))
        try:
            Utils.run(command)
            concattime = time.time()
            logger.info(" ".join([" : ".join(["Regularized and Clumped rasters concatenation : ", \
                                              str(concattime - clumptime)]), "seconds"]))
            shutil.copyfile(os.path.join(path, outfilename), os.path.join(out, outfilename))
            os.remove(os.path.join(path, 'clump.tif'))
            os.remove(os.path.join(path, 'clump300.tif'))
        except:
            logger.error("Application 'iota2ConcatenateImages' for 64 bits does not exist, please change 64 bits binaries path")
            sys.exit()

            
    command = "gdal_translate -q -b 2 -ot Uint32 %s %s"%(os.path.join(path, outfilename), os.path.join(path, "clump32bits.tif"))
    Utils.run(command)    
    shutil.copy(os.path.join(path, "clump32bits.tif"), out)
    os.remove(os.path.join(path, "clump32bits.tif"))
    if os.path.exists(os.path.join(path, outfilename)):
        os.remove(os.path.join(path, outfilename))            
    
    clumptime = time.time()
    logger.info(" ".join([" : ".join(["Clump : ", str(clumptime - begin_clump)]), "seconds"]))

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
 
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Generete clumps raster from classification raster file")
        
        parser.add_argument("-wd", dest="path", action="store", \
                            help="Working directory", required = True)
        
        parser.add_argument("-classif", dest="classif", action="store", \
                            help="Input classification raster file", required = True)
        
        parser.add_argument("-outpath", dest="outpath", action="store", \
                            help="Output file name and path", required = True)

        parser.add_argument("-ram", dest="ram", action="store", \
                            help="Ram for otb processes", required = True)
        
        parser.add_argument("-float64", dest="float64", action='store_true', default = False, \
                            help="Use specific float 64 Bandmath application "\
                            "for huge landscape (clumps number > 2²³ bits for mantisse)")

        parser.add_argument("-float64lib", dest="float64lib", action='store', required = False, \
                            help="float 64 exe path ")          
    
        args = parser.parse_args()
        
        clumpAndStackClassif(args.path, args.classif, args.outpath, args.ram, args.float64, args.float64lib)

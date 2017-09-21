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

import sys, os, argparse, time, shutil
import numpy as np
import gdal

try:
    import otbAppli
except ImportError:
    raise ImportError('Iota2 not well configured / installed')

def clumpAndStackClassif(path, raster, outpath, ram, float64 = False, exe64 = ""):

    begin_clump = time.time()

    # split path and file name of outfilename
    out = os.path.dirname(outpath)
    outfilename = os.path.basename(outpath)
    
    # Clump Classif with OTB segmentation algorithm
    clumpAppli = otbAppli.CreateClumpApplication({"in" : raster,
                                                 "filter.cc.expr" : 'distance<1',
                                                 "ram" : ram,
                                                 "pixType" : 'uint32',
                                                 "mode" : "raster",
                                                 "filter" : "cc",
                                                 "mode.raster.out" : os.path.join(path, 'clump.tif')})
    clumpAppli.Execute()

    # Add 300 to all clump ID    
    bandMathAppli = otbAppli.CreateBandMathApplication(clumpAppli, \
                                                       'im1b1+300', \
                                                       ram, \
                                                       'uint32', \
                                                       os.path.join(path, 'clump300.tif'))
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
        dataRamAppli = otbAppli.CreateBandMathApplication(raster, \
                                                          'im1b1', \
                                                          ram, \
                                                          'uint8')
        dataRamAppli.Execute()
        
        concatImages = otbAppli.CreateConcatenateImagesApplication([dataRamAppli, bandMathAppli], \
                                                                   ram, \
                                                                   'uint32', \
                                                                   os.path.join(path, outfilename))
        concatImages.ExecuteAndWriteOutput()
        
        concattime = time.time()
        print " ".join([" : ".join(["Regularized and Clumped rasters concatenation : ", str(concattime - clumptime)]), "seconds"])

        shutil.copyfile(os.path.join(path, outfilename), os.path.join(out, outfilename))
        
    else:
        command = '%s %s %s %s'%((exe64,
                                  raster, \
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
    
        args = parser.parse_args()
        
        clumpAndStackClassif(args.path, args.classif, args.outpath, args.ram, args.float64)

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
    
    if not float64:
        print "lalalalala"
        clumpAppli.Execute()

        clumptime = time.time()
        print " ".join([" : ".join(["Input raster well clumped : ", str(clumptime - begin_clump)]), "seconds"])    
        
        # Add 300 to all clump ID    
        bandMathAppli = otbAppli.CreateBandMathApplication({"il": clumpAppli,
                                                            "exp": 'im1b1+300', 
                                                            "ram": ram, 
                                                            "pixType": 'uint32', 
                                                            "out": os.path.join(path, 'clump300.tif')})
        bandMathAppli.Execute()

        dataRamAppli = otbAppli.CreateBandMathApplication({"il": raster,
                                                           "exp": 'im1b1',
                                                           "ram": ram,
                                                           "pixType": 'uint8'})
        dataRamAppli.Execute()
        
        concatImages = otbAppli.CreateConcatenateImagesApplication({"il" : [dataRamAppli, bandMathAppli],
                                                                    "ram" : ram,
                                                                    "pixType" : 'uint32',
                                                                    "out" : os.path.join(path, outfilename)})
        concatImages.ExecuteAndWriteOutput()
        
        concattime = time.time()
        print " ".join([" : ".join(["Regularized and Clumped rasters concatenation : ", str(concattime - clumptime)]), "seconds"])

        shutil.copyfile(os.path.join(path, outfilename), os.path.join(out, outfilename))
        
    else:
        clumpAppli.ExecuteAndWriteOutput()
        
        command = '/work/OT/theia/oso/OTB/otb_superbuild/iotaDouble_SVG/Exe/'\
                  'iota2BandMath %s "%s" %s %s'%(os.path.join(path, 'clump.tif'), \
                                                 "im1b1+300", \
                                                 os.path.join(path, 'clump300.tif'),\
                                                 10)
        os.system(command)

        clumptime = time.time()
        print " ".join([" : ".join(["Input raster well clumped : ", str(clumptime - begin_clump)]), "seconds"])    
        
        command = '%s %s %s %s %s'%((exe64,
                                     raster, \
                                     os.path.join(path, 'clump300.tif'), \
                                     os.path.join(path, outfilename),
                                     10))
        try:
            os.system(command)
            concattime = time.time()
            print " ".join([" : ".join(["Regularized and Clumped rasters concatenation : ", str(concattime - clumptime)]), "seconds"])
            shutil.copyfile(os.path.join(path, outfilename), os.path.join(out, outfilename))
        except:
            print "Application 'iota2ConcatenateImages' does not exist"
            sys.exit()

        
        
    clumptime = time.time()
    print " ".join([" : ".join(["Clump : ", str(clumptime - begin_clump)]), "seconds"])

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
                            help="float 64 bandmath exe path ")          
    
        args = parser.parse_args()
        
        clumpAndStackClassif(args.path, args.classif, args.outpath, args.ram, args.float64, args.float64lib)

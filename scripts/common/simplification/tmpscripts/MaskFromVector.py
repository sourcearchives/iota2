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

import sys
import os
import argparse
import shutil
import OSO_functions as osof

def prepareDataStats(path, vector, threads, pixFormat, classif, validity, confidence, outpath, maskTif):

    #driver = ogr.GetDriverByName('ESRI Shapefile')
    vector_open = osof.shape_open(vector,0)
    inLayer = vector_open.GetLayer()
    extent = inLayer.GetExtent()

    print extent
    outputTifName = os.path.splitext(os.path.basename(classif))[0]
    outputTifClassif = path + '/' + outputTifName + '_subset.tif'

    outputTifName = os.path.splitext(os.path.basename(validity))[0]
    outputTifValidity = path + '/' + outputTifName + '_subset.tif'

    outputTifName = os.path.splitext(os.path.basename(confidence))[0]
    outputTifConfidence = path + '/' + outputTifName + '_subset.tif'    

    cmd = "gdalwarp -multi -wo NUM_THREADS=" + threads + " -te " + str(extent[0]) + " " + str(extent[2]) + " " + \
          str(extent[1]) + " " + str(extent[3])
    cmd = cmd + " -ot " + pixFormat + " " + classif + " " + outputTifClassif

    os.system(cmd)

    print "Decoupage de la classification"
    
    cmd = "gdalwarp -multi -wo NUM_THREADS=" + threads + " -te " + str(extent[0]) + " " + str(extent[2]) + " " + \
          str(extent[1]) + " " + str(extent[3])
    cmd = cmd +" -ot " + pixFormat+" "+validity+" "+ outputTifValidity

    os.system(cmd)

    print "Decoupage de la confidence"
    
    cmd = "gdalwarp -multi -wo NUM_THREADS=" + threads + " -te " + str(extent[0]) + " " + str(extent[2]) + " " + \
          str(extent[1]) + " " + str(extent[3])
    cmd = cmd +" -ot " + pixFormat+" "+confidence+" "+ outputTifConfidence    
    os.system(cmd)

    cmd = "otbcli_Rasterization -in %s -out %s -im %s -mode binary -mode.binary.foreground 1"%(vector, maskTif, outputTifClassif)
    os.system(cmd)

    print "Rasterisation terminée"

    shutil.copy(outputTifClassif, outpath)
    shutil.copy(outputTifValidity, outpath)
    shutil.copy(outputTifConfidence, outpath)
    shutil.copy(maskTif, outpath)    

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
 
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Prepare subset data and mask for statistics")
        parser.add_argument("-wd", dest="path", action="store", \
                            help="Input path where classification is located", required = True)        
        parser.add_argument("-vector",dest = "vector",help ="path to the classif vector", default=None,required=True)
        parser.add_argument("-threads",dest = "threads",help ="number of threads",required=False,default='2')
        parser.add_argument("-pixFormat",dest = "pixFormat",help ="pixel format",required=False,default='uint8')
        parser.add_argument("-validity", dest="validity", action="store", \
                            help="validity raster", required = True)                            
        parser.add_argument("-classif", dest="classif", action="store", \
                            help="classification without regularization", required = True)        
        parser.add_argument("-confid", dest="confidence", action="store", \
                            help="confidence raster", required = True)
        parser.add_argument("-out", dest="out", action="store", \
                            help="out directory name", required = True)
        parser.add_argument("-mask", dest="mask", action="store", \
                            help="mask filename", required = True)        
        args = parser.parse_args()        
        prepareDataStats(args.path, \
                         args.vector, \
                         args.threads, \
                         args.pixFormat, \
                         args.classif, \
                         args.validity, \
                         args.confidence, \
                         args.out, \
                         args.mask)

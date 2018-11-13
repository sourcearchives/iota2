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

import os, sys, argparse
import ogr

def extractAndConcat(wd, shape_in, raster_in, raster_out, nbcore, outtype):

    inDriver = ogr.GetDriverByName("ESRI Shapefile")
    inDataSource = inDriver.Open(shape_in, 0)
    inLayer = inDataSource.GetLayer()
    extent = inLayer.GetExtent()

    extent = str(extent[0]), str(extent[2]), str(extent[1]), str(extent[3])

    rasttoconcat = []
    for rast in raster_in:
        tmprast = os.path.join(wd, os.path.basename(rast)[:-4] + 'clip.tif')
        os.system("gdalwarp  -tap -tr 10 10 -overwrite -multi -wo NUM_THREADS={} -te {} {} {}".format(nbcore, " ".join(extent), rast, tmprast))
        rasttoconcat.append(tmprast)
        
    os.system("otbcli_ConcatenateImages -il {} -out {} {}".format(" ".join(rasttoconcat), raster_out, outtype))
    
    for rasttodel in rasttoconcat:
        os.remove(rasttodel)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        PROG = os.path.basename(sys.argv[0])
        print '      '+sys.argv[0]+' [options]'
        print "     Help : ", PROG, " --help"
        print "        or : ", PROG, " -h"
        sys.exit(-1)
    else:
        USAGE = "usage: %prog [options] "
        PARSER = argparse.ArgumentParser(description="Clip raster files and concatenate them")
        PARSER.add_argument("-wd", dest="path", action="store",\
                            help="working dir",\
                            required=True)
        
        PARSER.add_argument("-ins", dest="ins", action="store", help="input shapefile to clip")
                            
        PARSER.add_argument("-inr", nargs ='+', dest="inr", action="store", help="input rasters", required=True)
                            
        PARSER.add_argument("-out", dest="out", action="store", help="output raster", required=True)        

        PARSER.add_argument("-pixtype", dest="pixtype", action="store", help="output raster", default="uint8")

        PARSER.add_argument("-nbcore", dest="nbcore", action="store", help="thread number for wrap operation", default="4")                            
                            
        args = PARSER.parse_args()

        extractAndConcat(args.path, args.ins, args.inr, args.out, args.nbcore, args.pixtype)
    
# extractAndConcat("/work/OT/theia/oso/vincent/vectorisation/loiret_oso2016.shp", ["/work/OT/theia/oso/production/2017/oso2017.tif", "/work/OT/theia/oso/production/2017/oso2017_validity.tif", "/work/OT/theia/oso/production/2017/oso2017_confidence.tif"], "/work/OT/theia/oso/vincent/test.tif", 24, "uint8")

# python devcourant/extractAndConcatRaster.py -ins /work/OT/theia/oso/vincent/vectorisation/loiret_oso2016.shp -inr /work/OT/theia/oso/production/2017/oso2017.tif /work/OT/theia/oso/production/2017/oso2017_confidence.tif /work/OT/theia/oso/production/2017/oso2017_validity.tif -out /work/OT/theia/oso/vincent/test.tif

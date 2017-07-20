#!/usr/bin/python
#-*- coding: utf-8 -*-

"""
Grid shapefile generation from an input raster
"""
import sys
import os
from osgeo import ogr,osr
from math import ceil
from osgeo.gdalconst import *
import OSO_functions as osof
import argparse
import numpy as np

def grid_generate(outname, raster, xysize):

    """
    Grid generation from raster.
    
    in :
        outname : out name of grid
        raster : raster name
        xysize : coefficient for tile size
    out : 
        shapefile
    
    """

    datas, xsize, ysize, projection, transform, raster_band = osof.raster_open(raster, 1)

    xmin = float(transform[0])
    xmax = float((transform[0] + transform[1] * xsize)) 
    ymin = float((transform[3] + transform[5] * ysize))
    ymax = float(transform[3])
    
    xSize = (xmax - xmin) / xysize - 1
    intervalX = np.arange(xmin, xmax, xSize)

    ySize = (ymax - ymin) / xysize - 1
    intervalY = np.arange(ymin, ymax, ySize)

    intervalX[0] = xmin
    intervalX[len(intervalX) - 1] = xmax
    intervalY[0] = ymin
    intervalY[len(intervalY) - 1] = ymax
    
    # create output file        
    osof.create_shape(outname, 2154)
    shape = osof.shape_open(outname, 1)
    outLayer = shape.GetLayer()
    featureDefn = outLayer.GetLayerDefn()

    # create grid cel
    countcols = 0
    while countcols < xysize:        
        countrows = 0
        while countrows < xysize:
            # create vertex
            ring = ogr.Geometry(ogr.wkbLinearRing)
            ring.AddPoint(intervalX[countcols], intervalY[countrows])
            ring.AddPoint(intervalX[countcols], intervalY[countrows + 1])
            ring.AddPoint(intervalX[countcols + 1], intervalY[countrows + 1])
            ring.AddPoint(intervalX[countcols + 1], intervalY[countrows])            
            ring.AddPoint(intervalX[countcols], intervalY[countrows])
            poly = ogr.Geometry(ogr.wkbPolygon)
            poly.AddGeometry(ring)

            # add new geom to layer
            outFeature = ogr.Feature(featureDefn)
            outFeature.SetGeometry(poly)
            outLayer.CreateFeature(outFeature)
            outFeature.Destroy

            ymin = intervalY[countrows]
            countrows += 1

        xmin = intervalX[countcols]
        countcols += 1
        
    # Close DataSources
    shape.Destroy()

    print "Grid has %s tiles"%(int(xysize * xysize))

    return int(xysize * xysize)
    
if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Grid shapefile generation from an input raster")
        parser.add_argument("-o", dest="outname", action="store", \
                            help="ouput grid shapefile path", required = True)
        parser.add_argument("-r", dest="raster", action="store", \
                            help="Input raster file", required = True)
        parser.add_argument("-c", dest="xysize", action="store", \
                            help="Number of vertical / horizontal tile", required = True)                            
        args = parser.parse_args()
        
        nbtiles = grid_generate(args.outname, args.raster, args.xysize)
    

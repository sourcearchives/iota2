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
Grid shapefile generation from an input raster
"""

import sys, os, argparse
from math import ceil
from osgeo import ogr, osr
from osgeo.gdalconst import *
import numpy as np

try:
    from Common import FileUtils as fut
except ImportError:
    raise ImportError('Iota2 not well configured / installed')

def createPolygonShape(name, epsg, driver):

    outDriver = ogr.GetDriverByName(driver)
    if os.path.exists(name):
        os.remove(name)
        
    out_coordsys = osr.SpatialReference()
    out_coordsys.ImportFromEPSG(epsg)
    outDataSource = outDriver.CreateDataSource(name)
    outLayer = outDataSource.CreateLayer(name, srs = out_coordsys, geom_type=ogr.wkbPolygon)
    
    outDataSource.Destroy()

def grid_generate(outname, xysize, epsg=2154, raster=None, coordinates=None):

    """
    Grid generation from raster.
    
    in :
        outname : out name of grid
        raster : raster name
        xysize : coefficient for tile size
    out : 
        shapefile
    
    """
    if raster is not None:
        xsize, ysize, projection, transform= fut.readRaster(raster, False, 1)

        xmin = float(transform[0])
        xmax = float((transform[0] + transform[1] * xsize)) 
        ymin = float((transform[3] + transform[5] * ysize))
        ymax = float(transform[3])
    else:
        xmin = float(coordinates[0])
        xmax = float(coordinates[1])
        ymin = float(coordinates[2])
        ymax = float(coordinates[3])

    xSize = (xmax - xmin) / xysize
    intervalX = np.arange(xmin, xmax + xSize, xSize)

    ySize = (ymax - ymin) / xysize
    intervalY = np.arange(ymin, ymax + ySize, ySize)
  
    # create output file        
    createPolygonShape(outname, epsg, 'ESRI Shapefile')
    driver = ogr.GetDriverByName("ESRI Shapefile")
    shape = driver.Open(outname, 1)
    outLayer = shape.GetLayer()
    featureDefn = outLayer.GetLayerDefn()

    # create grid cel
    countcols = 0
    while countcols < len(intervalX) - 1 :
        countrows = 0
        while countrows < len(intervalY) - 1:
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
        parser.add_argument("-epsg", dest="epsg", action="store", \
                            help="ouput grid shapefile projection (EPSG code)", type = int, required = True)        
        parser.add_argument("-r", dest="raster", action="store", \
                            help="Input raster file", default=None)
        parser.add_argument("-c", dest="xysize", action="store", type = int, \
                            help="Number of vertical / horizontal tile", required = True)
        parser.add_argument("-coords", dest="coords", nargs='*', action="store", \
                            help="xmin, xmax, ymin, ymax coordinates of the resulting bounding box")          
        args = parser.parse_args()

        if args.raster is not None:
            nbtiles = grid_generate(args.outname, args.xysize, args.epsg, args.raster)
        elif args.coords is not None:
            nbtiles = grid_generate(args.outname, args.xysize, args.epsg, None, args.coords)
        else:
            print "One of -r or coords option has to be filled"
            sys.exit()
    

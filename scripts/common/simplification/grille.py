#!/usr/bin/python
#-*- coding: utf-8 -*-

"""
Genere une grille selon un coefficent de taille par rapport a la taille des pixels.
Permet d'effectuer la serialisation de la simplification.
"""
import sys
import os
from osgeo import ogr,osr
import math
from math import ceil
from osgeo.gdalconst import *
import OSO_functions as osof
import argparse

def grid_generate(outname,raster,xysize):

    """
    Grid generation from raster.
    
    in :
        outname : out name of grid
        raster : raster name
        xysize : coefficient for tile size
    out : 
        shapefile
    
    """
    datas, xsize, ysize, projection, transform, raster_band = osof.raster_open(raster,1)

    xmin = transform[0]
    xmax = (transform[0] + transform[1] * xsize)
    ymin = (transform[3] + transform[5] * ysize)
    ymax = transform[3]  
    gridHeight = ysize * int(xysize)
    gridWidth = xsize * int(xysize)
    
    # convert sys.argv to float
    xmin = float(xmin)
    xmax = float(xmax)
    ymin = float(ymin)
    ymax = float(ymax)
    gridWidth = float(gridWidth)
    gridHeight = float(gridHeight)

    # get rows
    rows = ceil((ymax - ymin) / gridHeight)
    # get columns
    cols = ceil((xmax - xmin) / gridWidth)

    # start grid cell envelope
    ringXleftOrigin = xmin
    ringXrightOrigin = xmin + gridWidth
    ringYtopOrigin = ymax
    ringYbottomOrigin = ymax-gridHeight

    # create output file        
    osof.create_shape(outname, 2154)
    #outDriver = ogr.GetDriverByName('ESRI Shapefile')
    #out_coordsys = osr.SpatialReference()
    #out_coordsys.ImportFromEPSG(2154)
    #outDataSource = outDriver.CreateDataSource(outname)
    #outLayer = outDataSource.CreateLayer(outname,srs = out_coordsys,geom_type=ogr.wkbPolygon)
    shape = osof.shape_open(outname, 1)
    outLayer = shape.GetLayer()
    featureDefn = outLayer.GetLayerDefn()

    # create grid cells
    countcols = 0
    while countcols < cols:
        countcols += 1

        # reset envelope for rows
        ringYtop = ringYtopOrigin
        ringYbottom =ringYbottomOrigin
        countrows = 0

        while countrows < rows:
            countrows += 1
            ring = ogr.Geometry(ogr.wkbLinearRing)
            ring.AddPoint(ringXleftOrigin, ringYtop)
            ring.AddPoint(ringXrightOrigin, ringYtop)
            ring.AddPoint(ringXrightOrigin, ringYbottom)
            ring.AddPoint(ringXleftOrigin, ringYbottom)
            ring.AddPoint(ringXleftOrigin, ringYtop)
            poly = ogr.Geometry(ogr.wkbPolygon)
            poly.AddGeometry(ring)

            # add new geom to layer
            outFeature = ogr.Feature(featureDefn)
            outFeature.SetGeometry(poly)
            outLayer.CreateFeature(outFeature)
            outFeature.Destroy

            # new envelope for next poly
            ringYtop = ringYtop - gridHeight
            ringYbottom = ringYbottom - gridHeight

        # new envelope for next poly
        ringXleftOrigin = ringXleftOrigin + gridWidth
        ringXrightOrigin = ringXrightOrigin + gridWidth

    # Close DataSources
    outDataSource.Destroy()
    
    grid_open = osof.shape_open(outname,0)
    grid_layer = grid_open.GetLayer()
    nbtiles = grid_layer.GetFeatureCount()
    
    return nbtiles
    
    
if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Grid generation from an input raster")
        parser.add_argument("-o", dest="outname", action="store", \
                            help="ouput grid shapefile path", required = True)
        parser.add_argument("-r", dest="raster", action="store", \
                            help="Input raster file", required = True)
        parser.add_argument("-c", dest="xysize", action="store", \
                            help="coefficient for tile size", required = True)                            
        args = parser.parse_args()
        
        nbtiles = grid_generate(args.outname, args.raster, args.xysize)
        print "La grille contient {} tuiles".format(nbtiles)
    

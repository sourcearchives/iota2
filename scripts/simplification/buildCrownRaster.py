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
Create a raster of entities and neighbors entities according to an area (from tile).
"""

import sys, os, shutil
from osgeo import gdal, osr
from osgeo.gdalconst import *
import numpy as np
import pickle
import logging
logger = logging.getLogger(__name__)

try:
    from Common import OtbAppBank
    from Common import FileUtils as fu
    from Common import Utils
except ImportError:
    raise ImportError('Iota2 not well configured / installed')

def arraytoRaster(array, output, model, driver='GTiff'):

    driver = gdal.GetDriverByName(driver)
    cols = model.RasterXSize
    rows = model.RasterYSize
    outRaster = driver.Create(output, cols, rows, 1, gdal.GDT_Byte)
    outRaster.SetGeoTransform((model.GetGeoTransform()[0], \
                               model.GetGeoTransform()[1], 0, \
                               model.GetGeoTransform()[3], 0, \
                               model.GetGeoTransform()[5]))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(array)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromWkt(model.GetProjectionRef())
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()

def pixToGeo(raster,col,row):
	ds = gdal.Open(raster)
	c, a, b, f, d, e = ds.GetGeoTransform()
	xp = a * col + b * row + c
	yp = d * col + e * row + f
	return(xp, yp)
    
def manageBlocks(pathCrowns, tilenumber, blocksize, inpath, outpath, ram, logger=logger):

    tabBlocks = []
    tomerge = []
    for paths, dirs, files in os.walk(pathCrowns):
        for crown in files:
            if "_" + str(tilenumber) + ".tif" in crown and "aux.xml" not in crown:
                shutil.copy(os.path.join(paths, crown), inpath)
                crownSource = gdal.Open(os.path.join(inpath, crown), GA_ReadOnly)
                row, col = int(crownSource.RasterYSize), int(crownSource.RasterXSize)
                crownSource = None
                intervalX = np.arange(0, col, blocksize)
                intervalY = np.arange(0, row, blocksize)
                nbcolsblock = len(intervalX)
                nbrowsblock = len(intervalY)
                
                with open(os.path.join(pathCrowns, "listid_%s"%(tilenumber)), 'r') as f:
                    listid = pickle.load(f)
                    
                nbblock = 0
                for y in intervalY:
                    for x in intervalX:
                        outputTif = os.path.join(inpath, "tile%sblock%s.tif"%(tilenumber, nbblock))
                        xmin,ymin = pixToGeo(os.path.join(inpath, crown), x, y)
                        xmax,ymax = pixToGeo(os.path.join(inpath, crown), x + blocksize, y + blocksize)
                        
                        cmd = "gdalwarp -overwrite -multi -te "+str(xmin)+" "+str(ymax)+" "+str(xmax)+" "+str(ymin)
                        cmd = cmd+" -ot UInt32 "+os.path.join(inpath, crown)+" "+outputTif

                        Utils.run(cmd)
                        ds = gdal.Open(outputTif)
                        idx = ds.ReadAsArray()[1]
                        labels = ds.ReadAsArray()[0]
                        masknd = np.isin(idx, listid[0])
                        x = labels * masknd
                        outRasterPath = os.path.join(inpath, "tile%sblock%s_masked.tif"%(tilenumber, nbblock))
                        tomerge.append(outRasterPath)
                        arraytoRaster(x, outRasterPath, ds)
                        
                        nbblock += 1

                # Mosaic
                out = os.path.join(inpath, "tile_%s.tif"%(tilenumber))
                fu.assembleTile_Merge(tomerge, int(round(ds.GetGeoTransform()[1], 0)), out, ot="Byte")

                shutil.copy(out, outpath)

                # remove tmp files
                os.remove(os.path.join(inpath, crown))
                for fileblock in tomerge:
                    os.remove(fileblock)
            else:
                logger.info('Tile %s does not exist'%(tilenumber))

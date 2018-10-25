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
Create a raster of entities and neighbors entities according to an area (from tile) to serialize simplification step.
"""

import os
from osgeo import gdal, osr
from osgeo.gdalconst import *
import numpy as np
import pickle


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

def prepareBlocksMPI(pathCrowns, blocksize, outpath):

    for paths, dirs, files in os.walk(pathCrowns):
        for crown in files :
            print crown, dirs, paths
            if ".tif" in crown and "56" in crown and "blocks" not in paths:
                tilenumber = os.path.splitext(crown)[0].split("_")[len(os.path.splitext(crown)[0].split("_")) - 1]
                crownSource = gdal.Open(os.path.join(paths, crown), GA_ReadOnly)
                row, col = int(crownSource.RasterYSize), int(crownSource.RasterXSize)
                
                intervalX = np.arange(0, col, blocksize)
                intervalY = np.arange(0, row, blocksize)
                nbcolsblock = len(intervalX)
                nbrowsblock = len(intervalY)

                tabBlocks = []
                nbblock = 0
                for y in intervalY:
                    for x in intervalX:
                        tabBlocks.append((tilenumber, crown, nbblock, x, y, blocksize))
                        nbblock += 1

    for line in tabBlocks:
        outputTif = os.path.join(outpath, "block%s_tile%s.tif"%(line[2], line[0]))
        cmd = "otbcli_ExtractROI -startx "+str(line[3])+" -starty "+str(line[4])+" -sizex "+str(line[5])+\
              " -sizey "+str(line[5])+" -in "+ os.path.join(pathCrowns, line[1]) +" -out "+outputTif+ " -ram 10000"
        os.system(cmd)
        
        with open(os.path.join(pathCrowns, "listid_%s"%(line[0])), 'r') as f:
            listid = pickle.load(f)

        ds = gdal.Open(outputTif)
        idx = ds.ReadAsArray()[1]
        labels = ds.ReadAsArray()[0]
        masknd = np.isin(idx, listid)
        x = labels * masknd
        outRasterPath = os.path.join(outpath, "block%s_tile%s_masked.tif"%(line[2], line[0]))
        arraytoRaster(x, outRasterPath, ds)


prepareBlocksMPI("/work/OT/theia/oso/vincent/crowns/", 2000, "/work/OT/theia/oso/vincent/crowns/blocks")



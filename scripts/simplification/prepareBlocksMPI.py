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

import sys, os, shutil
from osgeo import gdal, osr
from osgeo.gdalconst import *
import numpy as np
import pickle

try:
    from Common import OtbAppBank
    from Common import FileUtils as fu
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

def parametersBlocks(pathCrowns, blocksize, outpath):

    tabBlocks = []
    ntile = 0
    for paths, dirs, files in os.walk(pathCrowns):
        for crown in files :
            if ".tif" in crown:
                tilenumber = os.path.splitext(crown)[0].split("_")[len(os.path.splitext(crown)[0].split("_")) - 1]
                crownSource = gdal.Open(os.path.join(paths, crown), GA_ReadOnly)
                row, col = int(crownSource.RasterYSize), int(crownSource.RasterXSize)
                
                intervalX = np.arange(0, col, blocksize)
                intervalY = np.arange(0, row, blocksize)
                nbcolsblock = len(intervalX)
                nbrowsblock = len(intervalY)

                tabBlocks.append([os.path.join(paths, crown), os.path.join(paths, "listid_%s"(tilenumber)), tilenumber])
                nbblock = 0
                for y in intervalY:
                    for x in intervalX:
                        tabBlocks[ntile].append([nbblock, x, y, blocksize])
                        nbblock += 1
                        
                ntile += 1
                        
    return tabBlocks


def managementBlocks(inpath, tileBlocks, outpath, nbline=None):

    shutil.copy(tileBlocks[0][0], inpath)
    
    tomerge = []
    for idx, line in enumerate(tileBlocks[1]):
        if nbline is not None and idx == nbline:
            outputTif = os.path.join(outpath, "block%s_tile%s.tif"%(tileBlocks[0][2], line[0]))
            roiapp = OtbAppBank.CreateExtractROIApplication({"in": tileBlocks[0][0],
                                                             "ram": ram,
                                                             "startx": line[1],
                                                             "starty": line[2],
                                                             "sizex": line[3],
                                                             "sizey": line[3]                                                                                                                        
                                                             "out": outputTif})
            bmapp.ExecuteAndWriteOutput()
        
            with open(tileBlocks[0][1], 'r') as f:
                listid = pickle.load(f)

            ds = gdal.Open(outputTif)
            idx = ds.ReadAsArray()[1]
            labels = ds.ReadAsArray()[0]
            masknd = np.isin(idx, listid)
            x = labels * masknd
            outRasterPath = os.path.join(inpath, "block%s_tile%s_masked.tif"%(line[0], tileBlocks[0][2]))
            tomerge.append(outRasterPath)
            arraytoRaster(x, outRasterPath, ds)
            

    # Mosaic
    out = os.path.join(inpath, "tile%s_masked.tif"%(tileBlocks[0][2]))
    fu.assembleTile_Merge(tomerge, int(ds.RasterYSize), out, ot="Byte"):

    shutil.copy(out, outpath)
    
    # remove tmp files
    os.remove(os.path.join(inpath, os.path.basename(tileBlocks[0][0])))
    for fileblock in tomerge:
        os.remove(fileblock)


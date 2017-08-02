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
Script to run all generalization steps (regularization, clump, vectorization, simplification and statistics computing)
"""

import os
import Regularization
import ClumpClassif
import GridGenerator
import TileEntitiesAndCrown
import VectAndSimp
import MergeTileShapes
import RastersToSqlitePoint
import ZonalStats

class Generalization:
    
    def __init__(self, wd, out, ram, nbcore, grasslib, classif = "", validity = "", confidence = ""):
        self.wd = wd
        self.out = out
        self.ram = ram
        self.nbcore = nbcore
        self.grasslib = grasslib
        if classif != "":
            self.classif = classif
        if validity != "":
            self.validity = validity
        if confidence != "":
            self.confidence = confidence            

    def Regularization(self, classif, umc1, outFile, inland, resampleSize, umc2):
        Regularization.OSORegularization(classif, umc1, self.cpu, self.wd, os.path.join(self.out, outFile), \
                                         self.ram, inland, resampleSize, umc2)

    def Clump(self, inFile, outFile):        
        ClumpClassif.clumpAndStackClassif(self.wd, inFile, outFile, self.ram)

    def GenGrid(self, inFile, outFile, nbVertTile):        
        GridGenerator.grid_generate(outFile, inFile, nbVertTile)

    def Serialize(self, inFile, outGrid, nbVertTile, ngrid = None, split = False, mode = 'cmd', float64 = False):
        GridGenerator.grid_generate(outGrid, inFile, nbVertTile)
        TileEntitiesAndCrown.serialisation_tif(self.wd, inFile, self.ram, outGrid, self.out, self.nbcore, ngrid, split, mode, float64)
    
    def Vectorize(self, inFile, outFile, douglas = 10, hermite = 10, angle45 = True):
        VectAndSimp.simplification(self.wd, inFile, self.grasslib, outFile, douglas, hermite, angle45)

    def MergeTileShapes(self, inFiles, outFile, MMU, fieldClass, zone = "", fieldZone = "", \
                        fieldValue = "", tileId = "", prefix = "", tilesFolder = ""):
        
        MergeTileShapes.mergeTileShapes(self.wd, inFiles, outFile, self.grasslib, MMU, fieldClass, \
                            zone, fieldZone, fieldValue, tileId, prefix, tilesFolder)
        
    def ComputeStats(self, inFile, outStats, outShape, fieldClass, rtype, maskMer = "", split = "", *rasters):
                
        RastersToSqlitePoint.RastersToSqlitePoint(self.wd, inFile, fieldClass, outStats, \
                                                  self.ram, rtype, maskMer, split, rasters)
        
        ZonalStats.computeAndJoinStats(self.wd, inFile, outFile, outShape)

    def Generalize(self, umc1, inland, resampleSize, umc2, nbVertTile, douglas, hermite, angle45, \
                   MMU, outShape, fieldClass, rtype, split, zone="", fieldZone="", fieldValue="", \
                   tileId="", prefix="", tilesFolder=""):

        outReg = os.path.join(self.wd, "regul.tif")
        self.Regularization(self.classif, umc1, outReg, inland, resampleSize, umc2)

        outClump = os.path.join(self.wd, "clump.tif")
        self.Clump(outReg, outClump)

        outGrid = os.path.join(self.wd, "grid.shp")
        self.Serialize(outClump, outGrid, nbVertTile, None, split, 'cmd', False)

        for tile in range(nbVertTile):
            inRaster = os.path.join(self.wd, 'outfiles', 'tile_' + str(tile) + '.tif')
            outVect = os.path.join(self.wd, 'outfiles', 'tile_' + str(tile) + '.tif')
            self.Vectorize(inRaster, outVect, douglas, hermite, angle45)

        outGeomFile =  os.path.join(self.wd, 'classif.shp')
        self.MergeTileShapes(outGrid, outGeomFile, MMU, fieldClass, zone, fieldZone, fieldValue, tileId, prefix, tilesFolder)

        outStats = os.path.join(self.wd, 'extract_stats.sqlite')
        
        rasters = []
        rasters.append(self.classif)
        if self.validity != "":
            rasters.append(self.validity)
        if self.confidence != "":
            rasters.append(self.confidence)
            
        self.ComputeStats(outGeomFile, outStats, outShape, fieldClass, rtype, inland, split, rasters)

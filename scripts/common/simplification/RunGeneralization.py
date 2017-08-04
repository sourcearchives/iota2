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

import os, shutil, time
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
        self.cpu = nbcore
        self.grasslib = grasslib
        if classif != "":
            self.classif = classif
        if validity != "":
            self.validity = validity
        if confidence != "":
            self.confidence = confidence            

    def init(self):
        if os.path.exists(self.wd):
            shutil.rmtree(self.wd, ignore_errors=True)
            os.mkdir(self.wd)
        else:
            os.mkdir(self.wd)

        if os.path.exists(self.out):
            shutil.rmtree(self.out, ignore_errors=True)
            os.mkdir(self.out)
        else:
            os.mkdir(self.out)

    def clean(self):
        if os.path.exists(self.wd):
            shutil.rmtree(self.wd, ignore_errors=True)
            os.mkdir(self.wd)
        else:
            os.mkdir(self.wd)
            
    def Regularization(self, classif, umc1, outFile, inland, resampleSize, umc2):
        Regularization.OSORegularization(classif, umc1, self.cpu, self.wd, os.path.join(self.out, outFile), \
                                         self.ram, inland, resampleSize, umc2)

    def Clump(self, inFile, outFile):        
        ClumpClassif.clumpAndStackClassif(self.wd, inFile, outFile, self.ram)

    def GenGrid(self, inFile, outFile, nbVertTile):        
        GridGenerator.grid_generate(outFile, inFile, nbVertTile)

    def Serialize(self, inFile, outGrid, nbVertTile, ngrid = None, split = False, mode = 'cmd', float64 = False):
        GridGenerator.grid_generate(outGrid, inFile, nbVertTile)
        TileEntitiesAndCrown.serialisation_tif(self.wd, inFile, self.ram, outGrid, self.out, self.cpu, ngrid, split, mode, float64)
    
    def Vectorize(self, inFile, outFile, douglas = 10, hermite = 10, angle45 = True):
        VectAndSimp.simplification(self.wd, inFile, self.grasslib, outFile, douglas, hermite, angle45)

    def MergeTileShapes(self, inFiles, outFile, MMU, fieldClass, zone = "", fieldZone = "", \
                        fieldValue = "", tileId = "", prefix = "", tilesFolder = ""):
        
        MergeTileShapes.mergeTileShapes(self.wd, inFiles, outFile, self.grasslib, MMU, fieldClass, \
                            zone, fieldZone, fieldValue, tileId, prefix, tilesFolder)
        
    def ComputeStats(self, inFile, outStats, outShape, fieldClass, rtype, rasters, maskMer = "", split = ""):
                
        RastersToSqlitePoint.RastersToSqlitePoint(self.wd, inFile, fieldClass, outStats, \
                                                  self.ram, rtype, rasters, maskMer, split)
        
        ZonalStats.computeAndJoinStats(self.wd, inFile, outStats, outShape)

    def Generalize(self, umc1, inland, resampleSize, umc2, nbVertTile, douglas, hermite, angle45, \
                   MMU, outShape, fieldClass, rtype, split = "", zone="", fieldZone="", fieldValue="", \
                   tileId=""):

        timeinit = time.time()
        self.init()

        print "############################## Regularization ###############################\n"
        
        outReg = os.path.join(self.out, "regul.tif")
        self.Regularization(self.classif, umc1, outReg, inland, resampleSize, umc2)
        
        timeregu = time.time()     
        print " ".join([" : ".join(["Regularization", str(timeregu - timeinit)]), "seconds"])

        print "\n################################### Clump ###################################\n"
        
        outClump = os.path.join(self.out, "clump.tif")
        self.Clump(outReg, outClump)

        timeclump = time.time()     
        print " ".join([" : ".join(["Clump", str(timeclump - timeregu)]), "seconds"])

        print "\n############################## Serialization ################################\n"
        
        outGrid = os.path.join(self.out, "grid.shp")
        self.Serialize(outClump, outGrid, nbVertTile, None, split, 'cmd', False)

        timeneigh = time.time()     
        print " ".join([" : ".join(["Serialization", str(timeneigh - timeclump)]), "seconds"])

        print "\n##################### Vectorization & Simplification ########################\n"
        
        listTiles = []
        for tile in range(nbVertTile * nbVertTile):
            inRaster = os.path.join(self.out, 'tile_' + str(tile) + '.tif')
            outVect = os.path.join(self.wd, 'tile_' + str(tile) + '.shp')
            if os.path.exists(os.path.join(self.out, 'tile_' + str(tile) + '.tif')):
                print "\n############################# Tile %s ################################\n"%(tile)
                self.Vectorize(inRaster, outVect, douglas, hermite, angle45)
                listTiles.append(outVect)

        timevect = time.time()     
        print " ".join([" : ".join(["Vectorization & Simplification", str(timevect - timeneigh)]), "seconds"])

        print "\n############################# Merge vectors ################################\n"
        
        outGeomFile =  os.path.join(self.wd, 'classif.shp')
        self.MergeTileShapes(listTiles, outGeomFile, MMU, 'cat', zone, fieldZone, fieldValue, tileId, 'tile_', self.wd)

        timemerge = time.time()     
        print " ".join([" : ".join(["Merge Vectors", str(timemerge - timevect)]), "seconds"])

        print "\n######################### Statistics computing #############################\n"
        
        outStats = os.path.join(self.wd, 'extract_stats.sqlite')

        rasters = []
        rasters.append(self.classif)
        if self.validity != "":
            rasters.append(self.validity)
        if self.confidence != "":
            rasters.append(self.confidence)
            
        self.ComputeStats(outGeomFile, outStats, outShape, fieldClass, rtype, rasters, inland, split)
        
        timestats = time.time()     
        print " ".join([" : ".join(["Statistics computing", str(timestats - timemerge)]), "seconds\n"])

        print "Generalization process sucessfully finished : %s created"%(outShape)
        
        self.clean()

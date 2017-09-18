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

import unittest
import os, sys, shutil
import multiprocessing
import gdal, ogr
import numpy as np
import pandas as pad
import sqlite3 as lite

try:
    from dbfread import DBF
except ImportError:
    raise Exception("Please install dbfread library")

import Regularization
import ClumpClassif
import GridGenerator
import TileEntitiesAndCrown as tec
import VectAndSimp as vas
import MergeTileShapes as mts
import RastersToSqlitePoint as rtsp
import ZonalStats as zs
import fileUtils as fu

#export PYTHONPATH=$PYTHONPATH:/home/thierionv/cluster/chaineIOTA/iota2-share/iota2/scripts/common
#export PYTHONPATH=$PYTHONPATH:/home/thierionv/sources/OTB-6.0.0-Linux64/lib/python
#export POS2TDIR=/home/vthierion/Documents/OSO/Dev/iota2/data/simplification/
#source /home/thierionv/sources/OTB-6.0.0-Linux64/otbenv.profile
#export GRASSDIR=/usr/lib/grass70/

pos2t_dir = os.environ.get('POS2TDIR')
try:
    pos2t_dataTest = pos2t_dir
except:
    raise Exception("Variable POS2TDIR not set, please provide the path of post-treatment scripts")

def rasterToArray(InRaster):
    
    arrayOut = None
    ds = gdal.Open(InRaster)
    arrayOut = ds.ReadAsArray()
    
    return arrayOut

def dbftoDataframe(vect):

    dbf = list(DBF(os.path.splitext(vect)[0] + '.dbf', load=True))
    df = pad.DataFrame.from_records([x.values() for x in dbf], columns=dbf[0].keys())
    
    return df
    
def compareVectorFile(vect_1, vect_2, mode='table', typegeom = 'point', drivername = "SQLite"):

        '''
        compare SQLite, table mode is faster but does not work with 
        connected OTB applications.

        return true if vectors are the same
        '''

        def getFieldValue(feat,fields):
                return dict([(currentField,feat.GetField(currentField)) for currentField in fields])
        def priority(item):
                return (item[0],item[1])
        def getValuesSortedByCoordinates(vector):
                values = []
                driver = ogr.GetDriverByName(drivername)
                ds = driver.Open(vector,0)
                lyr = ds.GetLayer()
                fields = fu.getAllFieldsInShape(vector, drivername)
                for feature in lyr:
                    if typegeom == "point":
                        x,y= feature.GetGeometryRef().GetX(),feature.GetGeometryRef().GetY()
                    elif typegeom == "polygon":
                        x,y= feature.GetGeometryRef().Centroid().GetX(),feature.GetGeometryRef().Centroid().GetY()
                    fields_val = getFieldValue(feature,fields)
                    values.append((x,y,fields_val))

                values = sorted(values,key=priority)
                return values

        fields_1 = fu.getAllFieldsInShape(vect_1, drivername) 
        fields_2 = fu.getAllFieldsInShape(vect_2, drivername)

        if len(fields_1) != len(fields_2): return False
        elif cmp(fields_1,fields_2) != 0 : return False
        
        if mode == 'table':
                connection_1 = lite.connect(vect_1)
                df_1 = pad.read_sql_query("SELECT * FROM output", connection_1)

                connection_2 = lite.connect(vect_2)
                df_2 = pad.read_sql_query("SELECT * FROM output", connection_2)

                try: 
                        table = (df_1 != df_2).any(1)
                        if True in table.tolist():return False
                        else:return True
                except ValueError:
                        return False

        elif mode == 'coordinates':
                values_1 = getValuesSortedByCoordinates(vect_1)
                values_2 = getValuesSortedByCoordinates(vect_2)
                sameFeat = [cmp(val_1,val_2) == 0 for val_1,val_2 in zip(values_1,values_2)]
                if False in sameFeat:return False
                return True
        else:
                raise Exception("mode parameter must be 'table' or 'coordinates'")    
    
class postt_regularization(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.raster10m = os.path.join(pos2t_dataTest, "OSO_10m.tif")
        self.rasterreg20m = os.path.join(pos2t_dataTest, "classif_regul_20m.tif")
        self.wd = os.path.join(pos2t_dataTest, "wd")
        self.out = os.path.join(pos2t_dataTest, "out")
        self.outfile = os.path.join(pos2t_dataTest, self.out, "classif_regul_20m.tif")
        self.inland = os.path.join(pos2t_dataTest, "masque_mer.shp")
        
    def test_regularization(self):
        """
        Check regularization process
        """
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

        # regularization process
        Regularization.OSORegularization(self.raster10m, 10, multiprocessing.cpu_count(), self.wd, self.outfile, "10000", self.inland, 20, 3)

        # test
        outtest = rasterToArray(self.outfile)
        outref = rasterToArray(self.rasterreg20m)        
        self.assertTrue(np.array_equal(outtest, outref))

        # remove temporary folders
        if os.path.exists(self.wd):shutil.rmtree(self.wd, ignore_errors=True)
        if os.path.exists(self.out):shutil.rmtree(self.out, ignore_errors=True)

class postt_clump(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.wd = os.path.join(pos2t_dataTest, "wd")
        self.out = os.path.join(pos2t_dataTest, "out")
        self.rasterreg20m = os.path.join(pos2t_dataTest, "classif_regul_20m.tif")
        self.outfilename = os.path.join(self.out, "classif_clump_regularisee.tif")
        self.rasterclump = os.path.join(pos2t_dataTest, self.outfilename)
        self.outfile = os.path.join(pos2t_dataTest, self.out, self.outfilename)

    def test_clump(self):
        """
        Check clump process
        """
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

        # clump process
        ClumpClassif.clumpAndStackClassif(self.wd, self.rasterreg20m, self.outfilename, "10000", False)

        # test
        outtest = rasterToArray(self.outfile)
        outref = rasterToArray(self.rasterclump)        
        self.assertTrue(np.array_equal(outtest, outref))

        # remove temporary folders
        if os.path.exists(self.wd):shutil.rmtree(self.wd, ignore_errors=True)
        if os.path.exists(self.out):shutil.rmtree(self.out, ignore_errors=True)

class postt_grid(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.rasterclump = os.path.join(pos2t_dataTest, "classif_clump_regularisee.tif")
        self.outfilename = "grid.shp"
        self.grid = os.path.join(pos2t_dataTest, self.outfilename)        
        self.wd = os.path.join(pos2t_dataTest, "wd")
        self.out = os.path.join(pos2t_dataTest, "out")
        self.outfile = os.path.join(pos2t_dataTest, self.out, self.outfilename)
        
    def test_grid(self):
        """
        Check grid generation process
        """

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

        # Grid generation process
        GridGenerator.grid_generate(self.outfile, self.rasterclump, 3)
        
        # test
        self.assertTrue(compareVectorFile(self.grid, self.outfile, 'coordinates', 'polygon', "ESRI Shapefile"), \
                        "Generated grid does not fit with grid reference file")

        # remove temporary folders
        if os.path.exists(self.wd):shutil.rmtree(self.wd, ignore_errors=True)
        if os.path.exists(self.out):shutil.rmtree(self.out, ignore_errors=True)

class postt_tec(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.rasterclump = os.path.join(pos2t_dataTest, "classif_clump_regularisee.tif")
        self.grid = os.path.join(pos2t_dataTest, "grid.shp")
        self.wd = os.path.join(pos2t_dataTest, "wd")
        self.out = os.path.join(pos2t_dataTest, "out")
        self.tile = 0
        self.outfilename = "tile_0.tif"
        #self.outfile = os.path.join(self.out, str(self.tile), self.outfilename)
        self.outfile = os.path.join(self.out, self.outfilename)        
        self.rasterneigh = os.path.join(pos2t_dataTest, 'rasters', self.outfilename)
        
    def test_tec(self):
        """
        Check tileEntitiesAndCrown process
        """

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

        # tileEntitiesAndCrown process
        tec.serialisation_tif(self.wd, self.rasterclump, "10000", self.grid, self.out, 4, self.tile)

        # test
        outtest = rasterToArray(self.outfile)
        outref = rasterToArray(self.rasterneigh)        
        self.assertTrue(np.array_equal(outtest, outref), \
                        "Generated raster doesnot fit with raster reference file")

        # remove temporary folders
        if os.path.exists(self.wd):shutil.rmtree(self.wd, ignore_errors=True)
        if os.path.exists(self.out):shutil.rmtree(self.out, ignore_errors=True)        

class postt_simplif(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.classif = os.path.join(pos2t_dataTest, "rasters", "tile_2.tif")
        self.wd = os.path.join(pos2t_dataTest, "wd")
        self.out = os.path.join(pos2t_dataTest, "out")
        self.outfilename = "tile_2.shp"
        self.vecteur =  os.path.join(pos2t_dataTest, 'vectors', self.outfilename)        
        self.outfile = os.path.join(pos2t_dataTest, self.out, self.outfilename)
        self.grasslib = os.environ.get('GRASSDIR')
        
    def test_simplif(self):
        """
        Check tileEntitiesAndCrown process
        """
        
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

        # Vectorization and simplification process          
        if not os.path.exists(os.path.join(self.grasslib, 'bin')):
            raise Exception("GRASSDIR '%s' not well initialized"%(self.grasslib))
        
        vas.simplification(self.wd, self.classif, self.grasslib, self.outfile, 10, 10, True)
        
        # test        
        self.assertTrue(compareVectorFile(self.vecteur, self.outfile, 'coordinates', 'polygon', "ESRI Shapefile"), \
                        "Generated shapefile vector does not fit with shapefile reference file")

        # remove temporary folders
        if os.path.exists(self.wd):shutil.rmtree(self.wd, ignore_errors=True)
        if os.path.exists(self.out):shutil.rmtree(self.out, ignore_errors=True)

class postt_merge(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.wd = os.path.join(pos2t_dataTest, "wd")
        self.out = os.path.join(pos2t_dataTest, "out")
        self.shapefiles = [os.path.join(pos2t_dataTest, "vectors", "tile_0.shp"), \
                           os.path.join(pos2t_dataTest, "vectors", "tile_1.shp"), \
                           os.path.join(pos2t_dataTest, "vectors", "tile_2.shp")]
        self.outfilename = "classif.shp"
        self.outfile = os.path.join(pos2t_dataTest, self.out, self.outfilename)
        self.mmu = 1000
        self.zone = os.path.join(pos2t_dataTest, "zone.shp")
        self.field = "id"
        self.value = 1
        self.fieldclass = 'cat'
        self.grasslib = os.environ.get('GRASSDIR')
        self.vecteur =  os.path.join(pos2t_dataTest, 'vectors', self.outfilename)        

    def test_merge(self):
        """
        Check mergeTileShapes process
        """
        
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

        mts.mergeTileShapes(self.wd, self.shapefiles, self.outfile, self.grasslib, \
                            self.mmu, self.fieldclass, self.zone, self.field, self.value)
        
        # test
        self.assertTrue(compareVectorFile(self.vecteur, self.outfile, 'coordinates', 'polygon', "ESRI Shapefile"), \
                        "Generated shapefile vector does not fit with shapefile reference file")

        # remove temporary folders
        if os.path.exists(self.wd):shutil.rmtree(self.wd, ignore_errors=True)
        if os.path.exists(self.out):shutil.rmtree(self.out, ignore_errors=True)

class postt_mergeTileSearch(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.wd = os.path.join(pos2t_dataTest, "wd")
        self.out = os.path.join(pos2t_dataTest, "out")
        self.tile = os.path.join(pos2t_dataTest, "grid.shp")
        self.outfilename = "classif_tile.shp"
        self.outfile = os.path.join(pos2t_dataTest, self.out, self.outfilename)
        self.mmu = 1000
        self.zone = os.path.join(pos2t_dataTest, "subzone.shp")
        self.field = "zone"
        self.value = 1
        self.fieldclass = 'cat'
        self.grasslib = os.environ.get('GRASSDIR')
        self.vecteur =  os.path.join(pos2t_dataTest, 'vectors', self.outfilename)
        self.tileId = 'FID'
        self.prefix = 'tile_'
        self.tilesfolder = os.path.join(pos2t_dataTest, 'vectors')

    def test_mergeTileSearch(self):
        """
        Check mergeTileShapes process
        """
        
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

        mts.mergeTileShapes(self.wd, self.tile, self.outfile, self.grasslib, \
                            self.mmu, self.fieldclass, self.zone, self.field, \
                            self.value, self.tileId, self.prefix, self.tilesfolder)
        
        # test
        self.assertTrue(compareVectorFile(self.vecteur, self.outfile, 'coordinates', 'polygon', "ESRI Shapefile"), \
                        "Generated shapefile vector does not fit with shapefile reference file")

        # remove temporary folders
        if os.path.exists(self.wd):shutil.rmtree(self.wd, ignore_errors=True)
        if os.path.exists(self.out):shutil.rmtree(self.out, ignore_errors=True)        

class postt_extractPixelValue(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.wd = os.path.join(pos2t_dataTest, "wd")
        self.out = os.path.join(pos2t_dataTest, "out")
        self.outfilename = os.path.join(pos2t_dataTest, self.out, "sample_extraction.sqlite")
        self.zone = os.path.join(pos2t_dataTest, 'vectors', "classif.shp")
        self.field = 'class'
        self.rasters = [os.path.join(pos2t_dataTest, "OSO_10m.tif"), \
                        os.path.join(pos2t_dataTest, "validity_10m.tif"), \
                        os.path.join(pos2t_dataTest, "confidence_10m.tif")]

        self.rtype = 'uint8'
        self.sqlite = os.path.join(pos2t_dataTest, "vectors", "sample_extraction.sqlite")

    def test_extractPixelValue(self):
        """
        Check RastersToSqlitePoint process
        """
        
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

        rtsp.RastersToSqlitePoint(self.wd, self.zone, self.field, self.outfilename, "10000", self.rtype, self.rasters, "", "")

        # test        
        self.assertTrue(compareVectorFile(self.sqlite, self.outfilename, 'coordinates'), \
                        "Generated sqlite samples does not fit with sqlite reference file")

        # remove temporary folders
        #if os.path.exists(self.wd):shutil.rmtree(self.wd, ignore_errors=True)
        #if os.path.exists(self.out):shutil.rmtree(self.out, ignore_errors=True)

class postt_joinSqlite(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.wd = os.path.join(pos2t_dataTest, "wd")
        self.out = os.path.join(pos2t_dataTest, "out")
        self.outfilename = "classification.shp"
        self.outshape = os.path.join(self.out, self.outfilename)
        self.statsdb = os.path.join(pos2t_dataTest, "vectors", "sample_extraction.sqlite")
        self.shapefile = os.path.join(pos2t_dataTest, "vectors", "classif.shp")
        self.vecteur = os.path.join(pos2t_dataTest, "vectors", "classification.shp")
        
    def test_joinSqlite(self):
        """
        Check computeAndJoinStats process
        """
        
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

        zs.computeAndJoinStats(self.wd, self.shapefile, self.statsdb, self.outshape)

        # test
        self.assertTrue(compareVectorFile(self.vecteur, self.outshape, 'coordinates', 'polygon', "ESRI Shapefile"),
                        "Generated shapefile vector does not fit with shapefile reference file")

        # remove temporary folders
        if os.path.exists(self.wd):shutil.rmtree(self.wd, ignore_errors=True)
        if os.path.exists(self.out):shutil.rmtree(self.out, ignore_errors=True)
        
if __name__ == "__main__":
    unittest.main()

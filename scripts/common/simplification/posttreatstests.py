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
import os, sys
import multiprocessing
import shutil
import gdal
import numpy as np
import pandas as pad
import manageDBF
import regularization
import clumpClassif
import gridGenerator
import TileEntitiesAndCrown as tec
import VectAndSimp as vas

#export PYTHONPATH=$PYTHONPATH:/home/thierionv/cluster/chaineIOTA/iota2-share/iota2/scripts/common
#export PYTHONPATH=$PYTHONPATH:/home/thierionv/sources/OTB-6.0.0-Linux64/lib/python
#export POS2TDIR=/home/thierionv/cluster/chaineIOTA/iota2-share/iota2/scripts/common/simplification
#source /home/thierionv/sources/OTB-6.0.0-Linux64/otbenv.profile
#export GRASSDIR=/usr/lib/grass70/

pos2t_dir = os.environ.get('POS2TDIR')
try:
    pos2t_dataTest = pos2t_dir
except:
    print "Variable POS2TDIR not set, please provide the path of post-treatment scripts"
    sys.exit()

def rasterToArray(InRaster):
    arrayOut = None
    ds = gdal.Open(InRaster)
    arrayOut = ds.ReadAsArray()
    return arrayOut

def dbftoDataframe(vect):
    f = open(vect[:-4] + '.dbf')
    dbf = list(manageDBF.dbfreader(f))
    df = pad.DataFrame.from_records(dbf[2:], columns = dbf[0])

    return df
    
def compareShapefile(vect1, vect2):

    dbf1 = dbftoDataframe(vect1)
    dbf2 = dbftoDataframe(vect2)    

    try: 
        table = (dbf1 != dbf2).any(1)
        if True in table.tolist():return False
        else:return True
    except ValueError:
        return False
    
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
        regularization.OSORegularization(self.raster10m, 10, multiprocessing.cpu_count(), self.wd, self.outfile, "10000", self.inland, 20, 3)

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
        self.rasterreg20m = os.path.join(pos2t_dataTest, "classif_regul_20m.tif")
        self.outfilename = "classif_clump_regularisee.tif"
        self.rasterclump = os.path.join(pos2t_dataTest, self.outfilename)
        self.wd = os.path.join(pos2t_dataTest, "wd")
        self.out = os.path.join(pos2t_dataTest, "out")
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
        clumpClassif.clumpAndStackClassif(self.wd, self.rasterreg20m, self.outfilename, "10000", self.out, False)

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
        gridGenerator.grid_generate(self.outfile, self.rasterclump, 3)
        
        # test
        self.assertTrue(compareShapefile(self.grid, self.outfile), "Generated grid does not fit with grid reference file")

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
        self.outfile = os.path.join(self.out, str(self.tile), self.outfilename)        
        self.rasterneigh = os.path.join(pos2t_dataTest, self.outfilename)
        
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
        tec.serialisation_tif(self.wd, self.rasterclump, "10000", self.grid, "outfiles", self.out, 4, self.tile)

        # test
        outtest = rasterToArray(self.outfile)
        outref = rasterToArray(self.rasterneigh)        
        self.assertTrue(np.array_equal(outtest, outref))

        # remove temporary folders
        if os.path.exists(self.wd):shutil.rmtree(self.wd, ignore_errors=True)
        if os.path.exists(self.out):shutil.rmtree(self.out, ignore_errors=True)        

class postt_simplif(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.classif = os.path.join(pos2t_dataTest, "tile_0.tif")
        self.wd = os.path.join('/home/thierionv', "wd")
        self.out = os.path.join(pos2t_dataTest, "out")
        self.outfilename = "tile_0.shp"
        self.vecteur =  os.path.join(pos2t_dataTest, self.outfilename)        
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
        
        '''
        # test
        self.assertTrue(compareShapefile(self.vecteur, self.outfile), "Generated shapefile vector does not fit with shapefile reference file")

        # remove temporary folders
        if os.path.exists(self.wd):shutil.rmtree(self.wd, ignore_errors=True)
        if os.path.exists(self.out):shutil.rmtree(self.out, ignore_errors=True)
        '''
        
if __name__ == "__main__":
    unittest.main()

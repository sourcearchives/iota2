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

import sys, os, argparse, time, shutil, string
from osgeo import gdal, ogr, osr
from osgeo.gdalconst import *
import numpy as np
from itertools import chain
from subprocess import check_output

try:
    from skimage.measure import regionprops
    from skimage.future import graph

except ImportError:
    raise ImportError('Please install skimage library')

try:
    from Common import FileUtils as fu
except ImportError:
    raise ImportError('Iota2 not well configured / installed')

def manageEnvi(inpath, outpath, ngrid):

    # working directory
    if not os.path.exists(os.path.join(inpath, str(ngrid))):
        os.mkdir(os.path.join(inpath, str(ngrid)))

    if not os.path.exists(os.path.join(outpath, str(ngrid))):
        os.mkdir(os.path.join(outpath, str(ngrid)))        

    # outputs folder of working directory
    if not os.path.exists(os.path.join(inpath, str(ngrid), "outfiles")):
        os.mkdir(os.path.join(inpath, str(ngrid), "outfiles"))

    if not os.path.exists(os.path.join(outpath, str(ngrid), "outfiles")):
        os.mkdir(os.path.join(outpath, str(ngrid), "outfiles"))        

def cellCoords(feature, transform):
    """
    Generate pixel coordinates of square feature corresponding to raster transform.

    in :
        feature : feature from grid (osgeo format)
        transform : coordinates from raster
            transform[0] = Xmin;             // Upper Left X
            transform[1] = CellSize;         // W-E pixel size
            transform[2] = 0;                // Rotation, 0 if 'North Up'
            transform[3] = Ymax;             // Upper Left Y
            transform[4] = 0;                // Rotation, 0 if 'North Up'
            transform[5] = -CellSize;        // N-S pixel size
    out :
        cols_xmin : cols_xmin of cell
        cols_xmax : cols_xmax of cell
        cols_ymin : cols_ymin of cell
        cols_ymax : cols_ymax of cell
    """

    geom = feature.GetGeometryRef()
    ring = geom.GetGeometryRef(0)
    pointsX = []
    pointsY = []

    # get coordinates of cell corners
    for point in range(ring.GetPointCount()):
        X = ring.GetPoint(point)[0]
        Y = ring.GetPoint(point)[1]
        pointsX.append(X)
        pointsY.append(Y)

    # Convert geo coordinates in col / row of raster reference
    cols_xmin = int((min(pointsX)-transform[0])/transform[1])
    cols_xmax = int((max(pointsX)-transform[0])/transform[1])
    cols_ymin = int((max(pointsY)-transform[3])/transform[5])
    cols_ymax = int((min(pointsY)-transform[3])/transform[5])

    return cols_xmin, cols_xmax, cols_ymin, cols_ymax

def listTileEntities(raster, outpath, feature):
    """
        entities ID list of tile

        in :
            raster : bi-band raster (classification - clump)
            outpath : out directory
            feature : feature of tile from shapefile

        out :
            tile_id : list with ID

    """

    # Classification and Clump opening
    datas_classif, xsize_classif, ysize_classif, projection_classif, transform_classif = fu.readRaster(raster, True, 1)
    datas_clump, xsize_clump, ysize_clump, projection_clump, transform_clump = fu.readRaster(raster, True, 2)

    # Generate pixel coordinates of square feature corresponding to raster transform
    cols_xmin_decoup, cols_xmax_decoup, cols_ymin_decoup, cols_ymax_decoup = cellCoords(feature, transform_classif)

    # subset raster data array based on feature coordinates
    tile_classif = datas_classif[cols_ymin_decoup:cols_ymax_decoup, cols_xmin_decoup:cols_xmax_decoup]
    tile_id_all = datas_clump[cols_ymin_decoup:cols_ymax_decoup, cols_xmin_decoup:cols_xmax_decoup]

    del datas_classif, datas_clump

    # entities ID list of tile (except nodata and sea)
    tile_id = np.unique(np.where(((tile_classif > 1) & (tile_classif < 250)), tile_id_all, 0)).tolist()

    # delete 0 value
    tile_id = [int(x) for x in tile_id if x != 0]

    return tile_id

def ExtentEntitiesTile(tileId, Params, xsize, ysize, neighbors=False):

    """
        Compute geographical extent of tile entities

        in :
            tileId : entities ID list
            Params : Skimage regioprops output (entities individual extent)
            xsize : Cols number
            ysize : Rows number
            neighbors : neighbors entities computing (boolean)

        out :
            geographical extent of tile entities
    """

    subParams = {x:Params[x] for x in tileId}
    valsExtents = list(subParams.values())

    minCol = min([y for x, y, z, w in valsExtents])
    minRow = min([x for x, y, z, w in valsExtents])
    maxCol = max([w for x, y, z, w in valsExtents])
    maxRow = max([z for x, y, z, w in valsExtents])

    if not neighbors :
        if minRow > 0:
            minRow -= 1
        if minCol > 0:
            minCol -= 1
        if maxRow < ysize:
            maxRow += 1
        if maxCol < xsize:
            maxCol += 1

    return [minRow, minCol, maxRow, maxCol]

def pixToGeo(raster,col,row):
	ds = gdal.Open(raster)
	c, a, b, f, d, e = ds.GetGeoTransform()
	xp = a * col + b * row + c
	yp = d * col + e * row + f
	return(xp, yp)

#------------------------------------------------------------------------------
def serialisation_tif(inpath, raster, ram, grid, outpath, nbcore = 4, ngrid = -1, split = False, float64 = False, hpc = True):
    """

        in :
            inpath : working directory with datas
            raster : name of raster
            ram : ram for otb application
            grid : grid name for serialisation
            out : output path
            ngrid : tile number

        out :
            raster with normelized name (tile_ngrid.tif)
    """

    begintime = time.time()

    if os.path.exists(os.path.join(outpath, "tile_%s.tif"%(ngrid))):
        print "Output file '%s' already exists"%(os.path.join(outpath, "tile_%s.tif"%(ngrid)))
        sys.exit()
                
    # cast clump file from float to uint32
    if not 'UInt32' in check_output(["gdalinfo", raster]):
        clump = os.path.join(inpath, "clump.tif")
        command = "gdal_translate -q -b 2 -ot Uint32 %s %s"%(raster, clump)
        os.system(command)
        rasterfile = gdal.Open(clump, 0)
        clumpBand = rasterfile.GetRasterBand(1)
        os.remove(clump)
    else:
        rasterfile = gdal.Open(raster, 0)
        clumpBand = rasterfile.GetRasterBand(2)

    xsize = rasterfile.RasterXSize
    ysize = rasterfile.RasterYSize
    clumpArray = clumpBand.ReadAsArray()
    clumpProps = regionprops(clumpArray)
    rasterfile = clumpBand = clumpArray = None

    # Get extent of all image clumps
    params = {x.label:x.bbox for x in clumpProps}

    timeextents = time.time()
    print " ".join([" : ".join(["Get extents of all entities", str(timeextents - begintime)]), "seconds"])

    # Open Grid file
    driver = ogr.GetDriverByName("ESRI Shapefile")
    shape = driver.Open(grid, 0)
    grid_layer = shape.GetLayer()

    # for each tile
    for feature in grid_layer :

        # get feature FID
        idtile = int(feature.GetField("FID"))

        # feature ID vs. requested tile (ngrid)
        if ngrid is None or idtile == int(ngrid):
            print "-------------------------------------------------------\n\nTile : ", idtile

            print "########## Phase 1 - Tile entities ##########\n"

            # manage environment
            manageEnvi(inpath, outpath, idtile)

            # entities ID list of tile
            listTileId = listTileEntities(raster, outpath, feature)

            # if no entities in tile
            if len(listTileId) != 0 :

                timentities = time.time()
                print " ".join([" : ".join(["Entities ID list of tile", str(timentities - timeextents)]), "seconds"])
                print " : ".join(["Entities number", str(len(listTileId))])

                # tile entities bounding box
                listExtent = ExtentEntitiesTile(listTileId, params, xsize, ysize, False)
                timeextent = time.time()
                print " ".join([" : ".join(["Compute geographical extent of entities", str(timeextent - timentities)]), "seconds"])

                # Extract classification raster on tile entities extent
                tifRasterExtract = os.path.join(inpath, str(ngrid), "raster_tile_entities.tif")
                if os.path.exists(tifRasterExtract):os.remove(tifRasterExtract)

                xmin, ymax = pixToGeo(raster, listExtent[1], listExtent[0])
                xmax, ymin = pixToGeo(raster, listExtent[3], listExtent[2])

                command = "gdalwarp -q -multi -wo NUM_THREADS={} -te {} {} {} {} -ot UInt32 {} {}".format(nbcore,\
                                                                                                          xmin, \
                                                                                                          ymin, \
                                                                                                          xmax, \
                                                                                                          ymax, \
                                                                                                          raster, \
                                                                                                          tifRasterExtract)
                os.system(command)
                timeextract = time.time()
                print " ".join([" : ".join(["Extract classification raster on tile entities extent", \
                                            str(timeextract - timeextent)]), "seconds"])

                # Crown entities research
                ds = gdal.Open(tifRasterExtract)
                idx = ds.ReadAsArray()[1]
                g = graph.RAG(idx.astype(int), connectivity = 2)

                # Create connection duplicates
                listelt = []
                for elt in g.edges():
                    listelt.append(elt)
                    listelt.append((elt[1], elt[0]))
                
                # group by tile entities id
                topo = dict(fu.sortByFirstElem(listelt))
                
                # Flat list and remove tile entities
                flatneighbors = set(chain(*dict((key,value) for key, value in topo.iteritems() if key in listTileId).values()))

                timecrownentities = time.time()
                print " ".join([" : ".join(["List crown entities", \
                                            str(timecrownentities - timeextract)]), "seconds"])

                # Crown raster extraction
                listExtentneighbors = ExtentEntitiesTile(flatneighbors, params, xsize, ysize, False)
                xmin, ymax = pixToGeo(raster, listExtentneighbors[1], listExtentneighbors[0])
                xmax, ymin = pixToGeo(raster, listExtentneighbors[3], listExtentneighbors[2])

                rastEntitiesNeighbors = os.path.join(inpath, str(ngrid), "raster_crown_entities.tif")
                command = "gdalwarp -q -multi -wo NUM_THREADS={} -te {} {} {} {} -ot UInt32 {} {}".format(nbcore,\
                                                                                                          xmin, \
                                                                                                          ymin, \
                                                                                                          xmax, \
                                                                                                          ymax, \
                                                                                                          raster, \
                                                                                                          rastEntitiesNeighbors)
                
                os.system(command)

                timeextractcrown = time.time()
                print " ".join([" : ".join(["Extract classification raster on crown entities extent", \
                                            str(timeextractcrown - timecrownentities)]), "seconds"])

                ds = gdal.Open(rastEntitiesNeighbors)
                idx = ds.ReadAsArray()[1]
                labels = ds.ReadAsArray()[0]
                
                # Mask no crown and tile entities
                masknd = np.isin(idx, [listTileId + list(flatneighbors)])
                x = labels * masknd

                timemask = time.time()
                print " ".join([" : ".join(["Mask non crown and tile pixels", \
                                            str(timemask - timeextractcrown)]), "seconds"])
                
                # write numpy array
                driver = gdal.GetDriverByName('GTiff')
                rows = labels.shape[0]
                cols = labels.shape[1]
                outRaster = os.path.join(inpath, str(ngrid), "tile_%s.tif"%(ngrid))
                outRaster = driver.Create(outRaster, cols, rows, 1, gdal.GDT_Byte)
                outRaster.SetGeoTransform((ds.GetGeoTransform()[0], \
                                           ds.GetGeoTransform()[1], 0, \
                                           ds.GetGeoTransform()[3], 0, \
                                           ds.GetGeoTransform()[5]))
                outband = outRaster.GetRasterBand(1)
                outband.WriteArray(x)
                outRasterSRS = osr.SpatialReference()
                outRasterSRS.ImportFromWkt(ds.GetProjectionRef())
                outRaster.SetProjection(outRasterSRS.ExportToWkt())
                outband.FlushCache()     

                finalextract = time.time()
                print " ".join([" : ".join(["Save tile and crown entities raster", \
                                            str(finalextract - timemask)]), "seconds"])

                finTraitement = time.time() - begintime
                print "\nTemps de traitement : %s"%(round(finTraitement,2))


#------------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]'
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)

    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Manage tile clumps (in the ngrid th of the grid shapefile) and neighbors clumps " \
                                         ".i.e clumps in the crown. Result raster (tile_ngrid.tif) gets all clumps (tile and crown ones). " \
                                         "To differenciate them tile clumps have OSO classification codes while crown clumps have ID clumps ")

        parser.add_argument("-wd", dest="path", action="store", \
                            help="Working directory", required = True)

        parser.add_argument("-in", dest="classif", action="store", \
                            help="Name of raster bi-bands : classification (regularized) + clump (patches of pixels)", required = True)

        parser.add_argument("-nbcore", dest="core", action="store", \
                            help="Number of cores to use for OTB applications", required = True)

        parser.add_argument("-ram", dest="ram", action="store", \
                            help="Ram for otb processes", required = True)

        parser.add_argument("-grid", dest="grid", action="store", \
                            help="Grid file name", required = True)

        parser.add_argument("-ngrid", dest="ngrid", action="store", \
                            help="Tile number", required = False, default = None)

        parser.add_argument("-out", dest="out", action="store", \
                            help="outname directory", required = True)

        parser.add_argument("-split", dest="split", action='store_true', default = False, \
                            help="split mode for entities identification (landscape and crown entities)")

        parser.add_argument("-float64", dest="float64", action='store_true', default = False, \
                            help="Use specific float 64 Bandmath application for huge landscape (clumps number > 2²³ bits for mantisse)")
        
        parser.add_argument("-hpc", dest="hpc", action='store_true', default = False, \
                            help="Cluster use ?")        

    args = parser.parse_args()
    os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"]= str(args.core)

    serialisation_tif(args.path, args.classif, args.ram, args.grid, \
                      args.out, args.core, args.ngrid, args.split, args.float64, args.hpc)

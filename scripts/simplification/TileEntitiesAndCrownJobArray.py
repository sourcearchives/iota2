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
from osgeo import gdal,ogr,osr
from osgeo.gdalconst import *
import numpy as np
from subprocess import check_output

try:
    from skimage.measure import regionprops
except ImportError:
    raise ImportError('Please install skimage library')

try:
    from Common import FileUtils as fu
    from Common import OtbAppBank
except ImportError:
    raise ImportError('Iota2 not well configured / installed')

import BandMathSplit as bms
import ExtractAndSplit as eas

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
    tile_id = [x for x in tile_id if x != 0]

    return tile_id

def listTileNeighbors(clumpIdBoundaries, tifRasterExtract, listTileId):
    """
        entities ID list of crow

        in :
            clumpIdBoundaries : binary raster (1=neighbors)
            tifRasterExtract : subset bi-band raster (classification - clump)
            listTileId : entities ID list of tile

        out :
            listeIdCrown : entities ID list of crow
            waterSeaNeighbors : boolean
            neighbors : boolean
    """

    # Open rasters
    boundaries, xsize_bound, ysize_bound, proj_bound, transf_bound = fu.readRaster(clumpIdBoundaries, True, 1)

    datas_classif_neighbors, xsize_neighbors, ysize_neighbors, proj_neighbors, transf_neighbors = fu.readRaster(tifRasterExtract, True, 1)

    datas_clump_neighbors, xsize_cneighbors, ysize_cneighbors, proj_cneighbors, transf_cneighbors = fu.readRaster(tifRasterExtract, True, 2)

    # get ids of crown clumps
    listeIdCrown = np.unique(np.where(((datas_classif_neighbors > 1) & \
                                       (datas_classif_neighbors < 250) & \
                                       (boundaries == 1)), datas_clump_neighbors, 0)).tolist()

    # delete 0 value
    listeIdCrown = [x for x in listeIdCrown if x != 0]

    # check if presence of sea water (255)
    if len(listeIdCrown) != 0 :
        neighbors = True
        if np.any((boundaries == 1) & ((datas_classif_neighbors == 255) | (datas_classif_neighbors == 0))):
            listeIdCrown = listeIdCrown + listTileId
            waterSeaNeighbors = True
        else :
            waterSeaNeighbors = False
    else :
        waterSeaNeighbors = True
        neighbors = False

    return listeIdCrown, waterSeaNeighbors, neighbors

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

def setConditionsExpression(list_id, band, listfile=None):
    """
    Generate a list with conditions for id in array.

    in :
        list_id : list of id
    out :
        list_conds : list with conditions from list id
    """
    list_conds = []
    list_id.append(-1000)
    pos = 0

    while pos < len(list_id)-1:
        npos = pos+1
        if list_id[pos]+1 != list_id[pos+1] :
            list_conds.append("(im1b%s=="%(band)+str(list_id[pos])+")")
            pos += 1
        else :
            tmppos = pos
            while (tmppos < len(list_id)-1) and \
                  (list_id[tmppos]+1 == list_id[tmppos+1]):
                tmppos += 1
            list_conds.append("((im1b%s>="%(band)+str(list_id[pos])+") && (im1b%s<="%(band)+str(list_id[tmppos])+"))")
            pos = tmppos+1

    list_id.remove(-1000)

    if listfile is not None:
            condFile = open(listfile,"w")
            condFile.write(string.join(list_conds, "||") + "?1:0")

    return string.join(list_conds, "||") + "?1:0"

def removeFolderContent(folder):

    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)

def encodingChange(inpath, ngrid, tifClumpIdBinTemp, pixType):

    # encoding change
    tifClumpIdBin = os.path.splitext(tifClumpIdBinTemp)[0] + '_%s'%(pixType) + os.path.splitext(tifClumpIdBinTemp)[1]
    if os.path.exists(tifClumpIdBin):os.remove(tifClumpIdBin)
    command = "gdal_translate -q -ot {} {} {}".format(pixType, tifClumpIdBinTemp, tifClumpIdBin)
    os.system(command)
    os.remove(tifClumpIdBinTemp)

    return tifClumpIdBin


def entitiesToRaster(listTileId, raster, xsize, ysize, inpath, outpath, ngrid, feature, params, neighbors, split, float64, nbcore, ram, timeinit, hpc):

    # tile entities bounding box
    listExtent = ExtentEntitiesTile(listTileId, params, xsize, ysize, neighbors)
    timeextent = time.time()
    print " ".join([" : ".join(["Compute geographical extent of entities", str(timeextent - timeinit)]), "seconds"])

    tifRasterExtract = os.path.join(inpath, str(ngrid), "raster_extract.tif")
    if os.path.exists(tifRasterExtract):os.remove(tifRasterExtract)
    
    # Extract classification raster on tile entities extent [minRow, minCol, maxRow, maxCol]

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
    shutil.copy(tifRasterExtract, os.path.join(outpath))
    timeextract = time.time()
    print " ".join([" : ".join(["Extract classification raster on extent", str(timeextract - timeextent)]), "seconds"])

    #shutil.copy(tifRasterExtract, os.path.join(outpath, str(ngrid), "raster_extract.tif"))

    # Generate OTB expression (list of tile entities ID)
    conditionIdTileFile = os.path.join(inpath, str(ngrid), 'cond' + str(ngrid))
    condition = setConditionsExpression(listTileId, 2, conditionIdTileFile)
    tifClumpIdBinTemp = os.path.join(inpath, str(ngrid), "ClumpIdBinTemp.tif")
    tifClumpIdBin = os.path.join(inpath, str(ngrid), "ClumpIdBin.tif")
    
    # Split Raster to apply parallel Bandmath otb applications
    if split:
        shutil.copy(conditionIdTileFile, os.path.join(outpath, str(ngrid)))
        conditionIdTileFile =  os.path.join(outpath, str(ngrid), os.path.basename(conditionIdTileFile))

        sharedir = os.path.join(outpath, str(ngrid), 'subtiles')
        try:
            os.mkdir(sharedir)
        except:
            print 'Share directory already exists, existing files will be overwrited'
            shutil.rmtree(sharedir)
            os.mkdir(sharedir)

        if hpc:
            if float64:
                '''
                subRasterName = "bandMathSplit"
                splits = eas.extractAndSplit(tifRasterExtract, None, None, None, sharedir, subRasterName, 5, 5, None, "entire", 'gdal', 'UInt32', 10)
                splitsname = " ".join(splits)
                os.system("time mpirun -np %s -x ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=%s python BandMathSplitMPI.py "\
                          "-in %s -out %s -expression.file %s -wd %s "\
                          "-bandMathExe %s -share.Directory %s -splits %s -nbStreamDiv %s"%(6, 6, \
                                                                                            tifRasterExtract, \
                                                                                            tifClumpIdBinTemp, \
                                                                                            conditionIdTileFile, \
                                                                                            inpath, \
                                                                                            '/work/OT/theia/oso/OTB/otb_superbuild/iotaDouble_SVG/Exe/iota2BandMathFile',\
                                                                                            sharedir, \
                                                                                            splitsname, \
                                                                                            4))
                '''
                bms.bandMathSplit(tifRasterExtract,\
                                  tifClumpIdBinTemp,\
                                  conditionIdTileFile,\
                                  inpath,\
                                  'uint8', \
                                  'hpc',\
                                  10,\
                                  10,\
                                  '/work/OT/theia/oso/OTB/otb_superbuild/iotaDouble_SVG/Exe/iota2BandMathFile',\
                                  sharedir,\
                                  nbcore)

                
                tifClumpIdBin = encodingChange(inpath, ngrid, tifClumpIdBinTemp, 'Byte')

                return tifClumpIdBin, tifRasterExtract, tifClumpIdBin
            else:
                bms.bandMathSplit(tifRasterExtract,\
                                  tifClumpIdBin,\
                                  conditionIdTileFile,\
                                  inpath,\
                                  'uint8', \
                                  'hpc',\
                                  10,\
                                  10,\
                                  'otbcli_BandMath',\
                                  sharedir,\
                                  nbcore)
        else:
            bms.bandMathSplit(tifRasterExtract,\
                              tifClumpIdBin,\
                              conditionIdTileFile,\
                              inpath,\
                              'uint8', \
                              'cmd',\
                              10,\
                              10,\
                              'otbcli_BandMath',\
                              sharedir,\
                              nbcore)

        BMAtifRasterExtract = tifClumpIdBin
    else:
        if float64:
            commandBM = '/work/OT/theia/oso/OTB/otb_superbuild/iotaDouble/Exe/'\
                        'iota2BandMathFile %s %s %s'%(tifRasterExtract, \
                                                      conditionIdTileFile, \
                                                      tifClumpIdBinTemp)
            os.system(commandBM)

            tifClumpIdBin = encodingChange(inpath, ngrid, tifClumpIdBinTemp, 'Byte')

            return tifClumpIdBin, tifRasterExtract, tifClumpIdBin
        
        else:
            exp = open(conditionIdTileFile, 'r').read()
            BMAtifRasterExtract = OtbAppBank.CreateBandMathApplication({"il": tifRasterExtract,
                                                                      "exp": exp,
                                                                      "ram": ram,
                                                                      "pixType": 'uint8',
                                                                      "out": tifClumpIdBin})
            BMAtifRasterExtract.ExecuteAndWriteOutput()

            return tifClumpIdBin, tifRasterExtract

    #shutil.copy(tifClumpIdBin, os.path.join(outpath, str(ngrid), "ClumpIdBin.tif"))

    timeentities = time.time()
    print " ".join([" : ".join(["Raster generation of Entities", str(timeentities - timeextract)]), "seconds"])

    return tifClumpIdBin, tifRasterExtract, BMAtifRasterExtract

def getEntitiesBoundaries(clumpIdBoundaries, tifClumpIdBin, BMAtifRasterExtract, ram):

    BMAtifClumpIdBin = OtbAppBank.CreateBandMathApplication({"il": tifClumpIdBin,
                                                           "exp": "im1b1",
                                                           "ram": ram,
                                                           "pixType": 'uint8'})
    BMAtifClumpIdBin.Execute()

    # 1 pixel dilatation of tile entities raster
    dilateAppli = OtbAppBank.CreateBinaryMorphologicalOperation({"in" : BMAtifRasterExtract,
                                                               "ram" : ram,
                                                               "pixType" : 'uint8',
                                                               "filter" : 'dilate',
                                                               "structype.ball.xradius" : 1,
                                                               "structype.ball.yradius" : 1})

    dilateAppli.Execute()

    # Create tile entities boundary
    BMABoundary = OtbAppBank.CreateBandMathApplication({"il": [BMAtifClumpIdBin, dilateAppli],
                                                      "exp": '(im1b1==0 && im2b1==1)?1:0',
                                                      "ram": ram,
                                                      "pixType": 'uint8',
                                                      "out": clumpIdBoundaries})
    BMABoundary.ExecuteAndWriteOutput()


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

                # Generate raster of tile entities
                tifClumpIdBin, tifRasterExtract, BMAtifRasterExtract = entitiesToRaster(listTileId, \
                                                                                        raster, \
                                                                                        xsize, \
                                                                                        ysize, \
                                                                                        inpath, \
                                                                                        outpath, \
                                                                                        idtile, \
                                                                                        feature, \
                                                                                        params, \
                                                                                        False, \
                                                                                        split, \
                                                                                        float64, \
                                                                                        nbcore, \
                                                                                        ram, \
                                                                                        timentities, \
                                                                                        hpc)


                # Keep output raster of tile entities management
                shutil.copyfile(tifRasterExtract, os.path.join(inpath, str(idtile), "raster_extract_tile.tif"))
                tifRasterExtract = os.path.join(inpath, str(idtile), "raster_extract_tile.tif")

                shutil.copyfile(tifClumpIdBin, os.path.join(inpath, str(idtile), "ClumpIdBin_tile.tif"))
                tifClumpIdBin =  os.path.join(inpath, str(idtile), "ClumpIdBin_tile.tif")

                print "\n"
                print "############# Phase 2 - Crown entities #############\n"

                timephase1 = time.time()

                # Raster generation of tile entities boundary
                clumpIdBoundaries = os.path.join(inpath, str(idtile), "clump_id_boundaries.tif")
                getEntitiesBoundaries(clumpIdBoundaries, tifClumpIdBin, BMAtifRasterExtract, ram)

                #shutil.copy(clumpIdBoundaries, \
                #            os.path.join(outpath, str(idtile), "clumpIdBoundaries.tif"))

                timeboundary = time.time()
                print " ".join([" : ".join(["Raster generation of tile entities boundary", str(timeboundary - timephase1)]), "seconds"])

                # Crown entities ID list of tile (check sea water and neighbors)
                listTileIdCouronne, seaWater, neighbors = listTileNeighbors(clumpIdBoundaries, \
                                                                            tifRasterExtract, \
                                                                            listTileId)

                timecrownentitieslist = time.time()
                print " ".join([" : ".join(["Crown entities ID list", str(timecrownentitieslist - timeboundary)]), "seconds"])
                print " : ".join(["Crown entities number", str(len(listTileIdCouronne))])

                # neighbors management
                if neighbors :
                    tifClumpIdBinNeighbors, tifRasterExtractNeighbors, BMAtifRasterExtractNeighbors = entitiesToRaster(listTileIdCouronne, \
                                                                                                                       raster, \
                                                                                                                       xsize, \
                                                                                                                       ysize, \
                                                                                                                       inpath, \
                                                                                                                       outpath, \
                                                                                                                       idtile, \
                                                                                                                       feature, \
                                                                                                                       params, \
                                                                                                                       True, \
                                                                                                                       split, \
                                                                                                                       float64, \
                                                                                                                       nbcore, \
                                                                                                                       ram, \
                                                                                                                       timecrownentitieslist, \
                                                                                                                       hpc)


                    timephase2 = time.time()

                    print "\n"
                    print "############# Phase 3 - Merge tile and crown Entities #############\n"

                    # Align tile entities raster and crown raster
                    tifClumpIdBinResample = os.path.join(inpath, str(idtile), "ClumpIdBinResample.tif")
                    siAppli = OtbAppBank.CreateSuperimposeApplication({"inr": tifRasterExtractNeighbors,
                                                                     "inm": tifClumpIdBin,
                                                                     "ram": ram,
                                                                     "interpolator" : "nn",
                                                                     "pixType": 'uint8',
                                                                     "lms": '1000000',
                                                                     "out": tifClumpIdBinResample})

                    siAppli[0].ExecuteAndWriteOutput()

                    timealignraster = time.time()
                    print " ".join([" : ".join(["Align tile entities raster and crown raster", \
                                                str(timealignraster - timephase2)]), "seconds"])


                    # Final integration
                    tifOutRasterNeighbors = os.path.join(inpath, str(idtile), "OutRasterNeighborsTemp.tif")
                    if not seaWater:
                        if float64:
                            tifOutRasterNeighborsTemp = os.path.join(inpath, str(idtile), "OutRasterNeighborsTemp.tif")
                            command = '/work/OT/theia/oso/OTB/otb_superbuild/iotaDouble/Exe/'\
                                      'iota2BandMath %s %s "%s" %s'%(tifRasterExtractNeighbors, \
                                                                     tifClumpIdBinNeighbors, \
                                                                     "im2b1==1?im1b2:0", \
                                                                     tifOutRasterNeighborsTemp)

                            os.system(command)

                            # encoding change
                            tifOutRasterNeighbors = os.path.join(inpath, str(idtile), "OutRasterNeighbors.tif")
                            command = "gdal_translate -q -ot Uint32 {} {}".format(tifOutRasterNeighborsTemp, tifOutRasterNeighbors)
                            os.system(command)
                            try:
                                os.remove(tifOutRasterNeighborsTemp)
                            except:
                                print "Final Integration : conversion format problem"
                        else:
                            BMARasterNeigh = OtbAppBank.CreateBandMathApplication({"il": [tifRasterExtractNeighbors,
                                                                                        tifClumpIdBinNeighbors],
                                                                                 "exp": 'im2b1==1?im1b2:0',
                                                                                 "ram": ram,
                                                                                 "pixType": 'uint32',
                                                                                 "out": tifOutRasterNeighbors})
                            BMARasterNeigh.ExecuteAndWriteOutput()

                    else:
                        tifOutRasterNeighborsTemp = os.path.join(inpath, str(idtile), "OutRasterNeighborsTemp.tif")
                        if float64:                          
                            command = '/work/OT/theia/oso/OTB/otb_superbuild/iotaDouble/Exe/'\
                                      'iota2BandMath %s %s %s "%s" %s'%(tifRasterExtractNeighbors, \
                                                                        tifClumpIdBinNeighbors,\
                                                                        tifClumpIdBinResample,\
                                                                        "(im2b1==1 && im3b1==0)?im1b2:0", \
                                                                        tifOutRasterNeighborsTemp)

                            os.system(command)
                            # encoding change
                            tifOutRasterNeighbors = os.path.join(inpath, str(idtile), "OutRasterNeighbors.tif")
                            command = "gdal_translate -q -ot Uint32 {} {}".format(tifOutRasterNeighborsTemp, tifOutRasterNeighbors)
                            try:
                                os.system(command)
                            except:
                                print "Final Integration : conversion format problem"
                                
                            if os.path.exists(tifOutRasterNeighborsTemp):os.remove(tifOutRasterNeighborsTemp)
                        else:
                            BMARasterNeigh = OtbAppBank.CreateBandMathApplication({"il": [tifRasterExtractNeighbors,
                                                                                        tifClumpIdBinNeighbors,
                                                                                        tifClumpIdBinResample],
                                                                                 "exp": '(im2b1==1 && im3b1==0)?im1b2:0',
                                                                                 "ram": ram,
                                                                                 "pixType": 'uint32',
                                                                                 "out": tifOutRasterNeighbors})
                            BMARasterNeigh.ExecuteAndWriteOutput()

                    # Final integration of tile (OSO code) and crown (Clump id) entities
                    outRasterTemp = os.path.join(inpath, str(idtile), "outRasterTemp.tif")
                    if float64:
                        outRasterBMA = os.path.join(inpath, str(idtile), "outRasterTemporaire.tif")
                        command = '/work/OT/theia/oso/OTB/otb_superbuild/iotaDouble/Exe/'\
                                  'iota2BandMath %s %s %s "%s" %s'%(tifRasterExtractNeighbors, \
                                                                    tifClumpIdBinResample,\
                                                                    tifOutRasterNeighbors,\
                                                                    '(im2b1==1 && im3b1==0)?im1b1:im3b1', \
                                                                    outRasterBMA)
                        os.system(command)

                        # encoding change
                        command = "gdal_translate -ot Uint32 {} {}".format(outRasterBMA, outRasterTemp)
                        os.system(command)
                        os.remove(outRasterBMA)
                    else:
                        BMARasterNeigh = OtbAppBank.CreateBandMathApplication({"il": [tifRasterExtractNeighbors,
                                                                                    tifClumpIdBinResample,
                                                                                    tifOutRasterNeighbors],
                                                                             "exp": '(im2b1==1 && im3b1==0)?im1b1:im3b1',
                                                                             "ram": ram,
                                                                             "pixType": 'uint32',
                                                                             "out": outRasterTemp})
                        BMARasterNeigh.ExecuteAndWriteOutput()

                # If no neighbors exist
                else:
                    print "\n"
                    print "############# Phase 3 - without neighbors #############\n"
                    outRasterTemp = os.path.join(inpath, str(idtile), "outRasterTemp.tif")
                    if float64:
                        outRasterBMA = os.path.join(inpath, str(idtile), "outRasterTemporaire.tif")
                        command = '/work/OT/theia/oso/OTB/otb_superbuild/iotaDouble/Exe/'\
                                  'iota2BandMath %s %s "%s" %s'%(tifRasterExtract, \
                                                                 tifClumpIdBin, \
                                                                 'im2b1==1?im1b1:0', \
                                                                 outRasterBMA)
                        os.system(command)

                        # encoding change

                        command = "gdal_translate -ot Uint32 {} {}".format(outRasterBMA, outRasterTemp)
                        os.system(command)
                        os.remove(outRasterBMA)
                    else:
                        BMARasterTmpFinal = OtbAppBank.CreateBandMathApplication({"il": [tifRasterExtract,
                                                                                       tifClumpIdBin],
                                                                                "exp": 'im2b1==1?im1b1:0',
                                                                                "ram": ram,
                                                                                "pixType": 'uint32',
                                                                                "out": outRasterTemp})
                        BMARasterTmpFinal.ExecuteAndWriteOutput()


                # raster final name
                outfile = os.path.join(inpath, str(idtile), "outfiles" , "tile_%s.tif"%(idtile))

                # No data management"
                command = "gdal_translate -q -a_nodata 0 -ot Uint32 %s %s"%(outRasterTemp, outfile)
                os.system(command)

                timeintegration = time.time()
                print " ".join([" : ".join(["Final integration", \
                                            str(timealignraster - timecrownentitieslist)]), "seconds"])

                if os.path.exists(os.path.join(inpath, str(idtile), "outfiles", "tile_%s.tif"%(idtile))):
                    shutil.copy(os.path.join(inpath, str(idtile), "outfiles", "tile_%s.tif"%(idtile)), \
                                os.path.join(outpath, "tile_%s.tif"%(idtile)))
            else:
                print "No entities in this tile. End"

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

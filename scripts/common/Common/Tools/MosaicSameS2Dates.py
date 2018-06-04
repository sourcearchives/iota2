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

#import random
import os
#from sys import argv
import argparse
import shutil
#from collections import defaultdict
import osr
import gdal
from osgeo.gdalconst import *
from Common import FileUtils as fu
from Common.Utils import run

def converCoord(inCoord, inEPSG, OutEPSG):
    lon = inCoord[0]
    lat = inCoord[1]
    inSpatialRef = osr.SpatialReference()
    inSpatialRef.ImportFromEPSG(inEPSG)
    outSpatialRef = osr.SpatialReference()
    outSpatialRef.ImportFromEPSG(OutEPSG)
    coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
    coord = coordTrans.TransformPoint(lon, lat)
    return (coord[0], coord[1])

def FileSearch_fast(PathToFolder, AllPath, *names):

    """
        search all files in a folder or sub folder which contains all names in their name

        IN :
            - PathToFolder : target folder
                ex : /xx/xxx/xx/xxx
            - *names : target names
                ex : "target1", "target2"
        OUT :
            - out : first element which contains all pattern
    """
    out = []
    for path, dirs, files in os.walk(PathToFolder):
        for i in range(len(files)):
            flag = 0
            for name in names:
                if files[i].count(name) != 0 and files[i].count(".aux.xml") == 0:
                    flag += 1
            if flag == len(names):
                #if not AllPath:
                #    return files[i].split(".")[0]
                #else:
                #    return path+'/'+files[i]
                retour = files[i].split(".")[0]
                if AllPath:
                    retour = path+'/'+files[i]
                return retour

def getRasterOrigin(raster_in):
    if not os.path.isfile(raster_in):
        return []
    raster = gdal.Open(raster_in, GA_ReadOnly)
    if raster is None:
        return []
    geotransform = raster.GetGeoTransform()
    originX = geotransform[0]
    originY = geotransform[3]
    return originX, originY

def getTileOrigin(tile, S2Folder):
    path = FileSearch_fast(S2Folder, True, tile)
    epsgCode = fu.getRasterProjectionEPSG(path)
    X, Y = getRasterOrigin(path)
    return X, Y, int(epsgCode)

def priorityOrigin(item):
    """
        IN :
            item [list of Tile object]
        OUT :
            return tile origin (upper left corner) in order to manage tile's priority
    """
    return(-item[2], item[1])#upper left priority

def sortTiles(paths):
    paths_sort = sorted(paths, key=priorityOrigin)
    return paths_sort

def getTileSameDate(folder):
    buf = []
    content = os.listdir(folder)
    for currentContent in content:
        date = currentContent.split("_")[2].split("-")[0]
        buf.append((date, folder+"/"+currentContent))
    buf = fu.sortByFirstElem(buf)
    out = [currentList for date, currentList in buf if len(currentList) > 1]
    return out

def addLineToFile(inputFile, line):
    svgFile = open(inputFile, "a")
    svgFile.write(line+"\n")
    svgFile.close()

def launchFit(noDataM, noDataR, tileFolder, currentTile, sensorName, S2Folder, S2Bands, masks):
    S2Bands = S2Bands+masks
    noDataM = dict(zip(masks, noDataM))
    try:
        workingDirectory = os.environ["TMPDIR"]
    except:
        workingDirectory = None

    content = os.listdir(tileFolder)
    AllCmd = []

    if os.path.isdir(tileFolder+"/"+currentTile):
        folder = tileFolder+"/"+currentTile
        sameDateFolder = getTileSameDate(folder)
    for currentSameDate in sameDateFolder:
        buf = []
        cpt = 0
        for currentBand in S2Bands:
            print "Current Band : "+currentBand
            buf.append([])
            AllTiles = []
            for currentFolder in currentSameDate:
                print currentFolder
                path = FileSearch_fast(currentFolder, True, currentBand, ".tif")
                tile = path.split("/")[-1].split("_")[-1].replace(".tif", "")
                X, Y, inEPSG = getTileOrigin(tile, S2Folder)
                X_conv, Y_conv = converCoord((X, Y), inEPSG, 2154)
                buf[cpt].append((path, X_conv, Y_conv))
                t = path.split("/")[-1].split("_")[-1].replace(".tif", "")# -> origin tile name in raster to fit
                currentDate = path.split("/")[-1].split("_")[1].split("-")[0]#-> current date in raster to fit
                currentDestTile = path.split("/")[-1].split("_")[3]#destination tile Name in raster name
                if t not in AllTiles:
                    AllTiles.append(t)

            outFolder = tileFolder+"/"+currentDestTile+"/"+sensorName+"_"+currentDestTile+"_"+currentDate+"_"+"_".join(AllTiles)
            initVal = noDataR
            if currentBand in masks:
                outFolder = outFolder+"/MASKS"
                initVal = noDataM[currentBand]
            outName = "_".join(buf[cpt][0][0].split("/")[-1].split("_")[0:-1])+"_"+"_".join(AllTiles)+".tif"
            #case 2 acquisitions same day -> remove hours information
            tmp = []
            tmpList = outName.split("_")
            for i in range(len(tmpList)):
                if i != rasterPosDate:
                    tmp.append(tmpList[i])
                else:
                    tmp.append(currentDate)
            outName = "_".join(tmp)
            #############################
            if not os.path.exists(outFolder):
                os.mkdir(outFolder)
            priorityPaths = " ".join([currentPath for currentPath, X, Y in sortTiles(buf[cpt])])
            if not os.path.exists(outFolder+"/"+outName):
                workingFolder = outFolder
                if workingDirectory:
                    workingFolder = workingDirectory
                cmd = "gdal_merge.py -init "+str(initVal)+" -n "+str(initVal)+" -o "+workingFolder+"/"+outName+" "+priorityPaths
                cmd2 = "gdal_merge.py -init "+str(initVal)+" -n "+str(initVal)+" -o "+workingFolder+"/"+outName+" "+priorityPaths+" | "+outFolder+"/"+outName
                AllCmd.append(cmd)
                addLineToFile(cmdPath, cmd2)

                run(cmd)
                if workingDirectory:
                    shutil.copy(workingFolder+"/"+outName, outFolder+"/"+outName)
                    os.remove(workingFolder+"/"+outName)
            cpt += 1
    #fu.writeCmds(cmdPath1, AllCmd, mode="w")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-tiles.folder", dest="tileFolder", help="path to the folder which contain all tile's folder", default=None, required=True)
    parser.add_argument("-current.tile", dest="currentTile", help="tile to be process (must refers to a folder)", default=None, required=True)
    parser.add_argument("-sensor.name", dest="sensorName", help="", default=None, required=True)
    parser.add_argument("-raw.folder", dest="S2Folder", help="folder which raw datas, before any process", default=None, required=True)
    parser.add_argument("-raster.bands", nargs='+', dest="S2Bands", help="all bands to be process without data's mask", default=None, required=True)
    parser.add_argument("-raster.masks", nargs='+', dest="masks", help="data's mask", default=None, required=True)
    parser.add_argument("-bands.noData", dest="noDataR", help="no data's value in bands raster", default=None, required=True)
    parser.add_argument("-masks.noData", nargs='+', dest="noDataM", help="no data's value in masks (respect raster.masks order)", default=None, required=True)
    parser.add_argument("-cmd.path", dest="cmdPath", help="path to a saving file", default=None, required=True)
    parser.add_argument("-date.position", dest="rasterPosDate", help="date position in raster name if split by '_' and start counting by 0", type=int, default=None, required=True)

    args = parser.parse_args()

    launchFit(args.noDataM, args.noDataR, args.tileFolder, args.currentTile, args.sensorName, args.S2Folder, args.S2Bands, args.masks)
    #python mosaicSameS2DatesL8.py -date.position 1 -cmd.path /cmd -masks.noData 0 1 0 -bands.noData -10000 -raster.masks CLM_R1 EDG_R1 SAT_R1 -raster.bands B2 B3 B4 B5 B6 B7 B8 B8A B11 -raw.folder raw -sensor.name S2 -current.tile D4H4 -tiles.folder here


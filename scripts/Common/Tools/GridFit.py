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


import os
import shutil
import argparse
from osgeo import ogr
from osgeo import osr
from osgeo import gdal
from osgeo.gdalconst import *
from Common import FileUtils as fu
from Common.Utils import run

def getDateFromRaster(raster):
    #return raster.split("/")[-1].split("_")[1].split("-")[0]
    return raster.split("/")[-1].split("_")[1]

def getTileNameFromRaster(raster):
    return raster.split("/")[-1].split("_")[-5]

def getPaths(TileFolder, pattern):
    Tiles = os.listdir(TileFolder)
    paths = []
    for currentS2Tile in Tiles:
        if os.path.isdir(TileFolder+"/"+currentS2Tile):
            stack = fu.FileSearch_AND(TileFolder+"/"+currentS2Tile, True, pattern)
            if stack:
                paths.append(stack[0])
    return paths

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

def GetGeoInfo(FileName):
    SourceDS = gdal.Open(FileName, GA_ReadOnly)
    GeoT = SourceDS.GetGeoTransform()
    Projection = osr.SpatialReference()
    Projection.ImportFromWkt(SourceDS.GetProjectionRef())
    ProjectionCode = Projection.GetAttrValue("AUTHORITY", 1)
    return GeoT, ProjectionCode

def addTileToGrid(UL, UR, LR, LL, newLayer, newLayerDef, tileNameField, TileName):

    feature = ogr.Feature(newLayerDef)
    feature.SetField(tileNameField, TileName)
    poly = ogr.Geometry(ogr.wkbPolygon)
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(UL[0], UL[1])
    ring.AddPoint(UR[0], UR[1])
    ring.AddPoint(LR[0], LR[1])
    ring.AddPoint(LL[0], LL[1])
    ring.AddPoint(UL[0], UL[1])
    poly.AddGeometry(ring)
    feature.SetGeometry(poly)
    newLayer.CreateFeature(feature)
    if newLayer.CreateFeature(feature) != 0:
        print "Failed to create feature in shapefile.\n"
    ring.Destroy()
    poly.Destroy()
    feature.Destroy()

def createOutGrid(TileFolder, pattern, outputProjection, tileNameField, outGridPath):
    paths = getPaths(TileFolder, pattern)
    #paths = ['/work/theia/oso/sensorsDatas/S2/20152016//T30TVT/SENTINEL2A_20160729-112407-023_L2A_T30TVT_D_V1-0/SENTINEL2A_20160729-112407-023_L2A_T30TVT_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30TWP/SENTINEL2A_20160726-111748-462_L2A_T30TWP_D_V1-0/SENTINEL2A_20160726-111748-462_L2A_T30TWP_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30TWS/SENTINEL2A_20160815-110803-010_L2A_T30TWS_D_V1-0/SENTINEL2A_20160815-110803-010_L2A_T30TWS_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30TWT/SENTINEL2A_20151229-111920-437_L2A_T30TWT_D_V1-0/SENTINEL2A_20151229-111920-437_L2A_T30TWT_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30TXN/SENTINEL2A_20160723-110712-857_L2A_T30TXN_D_V1-0/SENTINEL2A_20160723-110712-857_L2A_T30TXN_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30TXP/SENTINEL2A_20160623-105858-730_L2A_T30TXP_D_V1-0/SENTINEL2A_20160623-105858-730_L2A_T30TXP_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30TXQ/SENTINEL2A_20160815-110803-010_L2A_T30TXQ_D_V1-0/SENTINEL2A_20160815-110803-010_L2A_T30TXQ_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30TXR/SENTINEL2A_20160815-110803-010_L2A_T30TXR_D_V1-0/SENTINEL2A_20160815-110803-010_L2A_T30TXR_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30TXS/SENTINEL2A_20160716-110923-852_L2A_T30TXS_D_V1-0/SENTINEL2A_20160716-110923-852_L2A_T30TXS_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30TXT/SENTINEL2A_20151229-111920-437_L2A_T30TXT_D_V1-0/SENTINEL2A_20151229-111920-437_L2A_T30TXT_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30TYN/SENTINEL2A_20160125-111611-703_L2A_T30TYN_D_V1-0/SENTINEL2A_20160125-111611-703_L2A_T30TYN_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30TYP/SENTINEL2A_20160204-110240-456_L2A_T30TYP_D_V1-0/SENTINEL2A_20160204-110240-456_L2A_T30TYP_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30TYQ/SENTINEL2A_20160723-110712-857_L2A_T30TYQ_D_V1-0/SENTINEL2A_20160723-110712-857_L2A_T30TYQ_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30TYR/SENTINEL2A_20151226-111142-750_L2A_T30TYR_D_V1-0/SENTINEL2A_20151226-111142-750_L2A_T30TYR_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30TYS/SENTINEL2A_20160312-105037-460_L2A_T30TYS_D_V1-0/SENTINEL2A_20160312-105037-460_L2A_T30TYS_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30TYT/SENTINEL2A_20151206-110834-178_L2A_T30TYT_D_V1-0/SENTINEL2A_20151206-110834-178_L2A_T30TYT_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30UUU/SENTINEL2A_20160410-112358-413_L2A_T30UUU_D_V1-0/SENTINEL2A_20160410-112358-413_L2A_T30UUU_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30UVU/SENTINEL2A_20160719-112117-457_L2A_T30UVU_D_V1-0/SENTINEL2A_20160719-112117-457_L2A_T30UVU_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30UVV/SENTINEL2A_20160507-110656-458_L2A_T30UVV_D_V1-0/SENTINEL2A_20160507-110656-458_L2A_T30UVV_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30UWA/SENTINEL2A_20160121-113008-064_L2A_T30UWA_D_V1-0/SENTINEL2A_20160121-113008-064_L2A_T30UWA_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30UWU/SENTINEL2A_20151222-113332-762_L2A_T30UWU_D_V1-0/SENTINEL2A_20151222-113332-762_L2A_T30UWU_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30UWV/SENTINEL2A_20160709-112403-413_L2A_T30UWV_D_V1-0/SENTINEL2A_20160709-112403-413_L2A_T30UWV_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30UXA/SENTINEL2A_20160507-110656-458_L2A_T30UXA_D_V1-0/SENTINEL2A_20160507-110656-458_L2A_T30UXA_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30UXU/SENTINEL2A_20160417-111159-116_L2A_T30UXU_D_V1-0/SENTINEL2A_20160417-111159-116_L2A_T30UXU_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30UXV/SENTINEL2A_20160507-110656-458_L2A_T30UXV_D_V1-0/SENTINEL2A_20160507-110656-458_L2A_T30UXV_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30UYA/SENTINEL2A_20151129-112140-218_L2A_T30UYA_D_V1-0/SENTINEL2A_20151129-112140-218_L2A_T30UYA_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30UYU/SENTINEL2A_20151226-111142-750_L2A_T30UYU_D_V1-0/SENTINEL2A_20151226-111142-750_L2A_T30UYU_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T30UYV/SENTINEL2A_20160112-110648-877_L2A_T30UYV_D_V1-0/SENTINEL2A_20160112-110648-877_L2A_T30UYV_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TCH/SENTINEL2A_20160401-105759-039_L2A_T31TCH_D_V1-0/SENTINEL2A_20160401-105759-039_L2A_T31TCH_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TCJ/SENTINEL2A_20160727-104250-774_L2A_T31TCJ_D_V1-0/SENTINEL2A_20160727-104250-774_L2A_T31TCJ_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TCK/SENTINEL2A_20160312-105037-460_L2A_T31TCK_D_V1-0/SENTINEL2A_20160312-105037-460_L2A_T31TCK_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TCL/SENTINEL2A_20151203-110846-328_L2A_T31TCL_D_V1-0/SENTINEL2A_20151203-110846-328_L2A_T31TCL_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TCM/SENTINEL2A_20160102-110129-139_L2A_T31TCM_D_V1-0/SENTINEL2A_20160102-110129-139_L2A_T31TCM_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TCN/SENTINEL2A_20160501-105310-197_L2A_T31TCN_D_V1-0/SENTINEL2A_20160501-105310-197_L2A_T31TCN_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TDH/SENTINEL2A_20160816-104025-461_L2A_T31TDH_D_V1-0/SENTINEL2A_20160816-104025-461_L2A_T31TDH_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TDJ/SENTINEL2A_20160727-104250-774_L2A_T31TDJ_D_V1-0/SENTINEL2A_20160727-104250-774_L2A_T31TDJ_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TDK/SENTINEL2A_20160607-104026-455_L2A_T31TDK_D_V1-0/SENTINEL2A_20160607-104026-455_L2A_T31TDK_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TDL/SENTINEL2A_20151230-105153-392_L2A_T31TDL_D_V1-0/SENTINEL2A_20151230-105153-392_L2A_T31TDL_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TDM/SENTINEL2A_20160322-105248-343_L2A_T31TDM_D_V1-0/SENTINEL2A_20160322-105248-343_L2A_T31TDM_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TDN/SENTINEL2A_20160717-104026-462_L2A_T31TDN_D_V1-0/SENTINEL2A_20160717-104026-462_L2A_T31TDN_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TEH/SENTINEL2A_20160425-103025-458_L2A_T31TEH_D_V1-0/SENTINEL2A_20160425-103025-458_L2A_T31TEH_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TEJ/SENTINEL2A_20160806-104026-455_L2A_T31TEJ_D_V1-0/SENTINEL2A_20160806-104026-455_L2A_T31TEJ_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TEK/SENTINEL2A_20160816-104025-461_L2A_T31TEK_D_V1-0/SENTINEL2A_20160816-104025-461_L2A_T31TEK_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TEL/SENTINEL2A_20160806-104026-455_L2A_T31TEL_D_V1-0/SENTINEL2A_20160806-104026-455_L2A_T31TEL_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TEM/SENTINEL2A_20151230-105153-392_L2A_T31TEM_D_V1-0/SENTINEL2A_20151230-105153-392_L2A_T31TEM_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TEN/SENTINEL2A_20151203-105818-575_L2A_T31TEN_D_V1-0/SENTINEL2A_20151203-105818-575_L2A_T31TEN_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TFH/SENTINEL2A_20151217-103953-944_L2A_T31TFH_D_V1-0/SENTINEL2A_20151217-103953-944_L2A_T31TFH_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TFJ/SENTINEL2A_20160727-104250-774_L2A_T31TFJ_D_V1-0/SENTINEL2A_20160727-104250-774_L2A_T31TFJ_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TFK/SENTINEL2A_20160717-104833-511_L2A_T31TFK_D_V1-0/SENTINEL2A_20160717-104833-511_L2A_T31TFK_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TFL/SENTINEL2A_20160816-104025-461_L2A_T31TFL_D_V1-0/SENTINEL2A_20160816-104025-461_L2A_T31TFL_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TFM/SENTINEL2A_20160707-104025-456_L2A_T31TFM_D_V1-0/SENTINEL2A_20160707-104025-456_L2A_T31TFM_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TFN/SENTINEL2A_20151223-105843-962_L2A_T31TFN_D_V1-0/SENTINEL2A_20151223-105843-962_L2A_T31TFN_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TGH/SENTINEL2A_20160724-103229-121_L2A_T31TGH_D_V1-0/SENTINEL2A_20160724-103229-121_L2A_T31TGH_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TGJ/SENTINEL2A_20160415-103022-461_L2A_T31TGJ_D_V1-0/SENTINEL2A_20160415-103022-461_L2A_T31TGJ_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TGK/SENTINEL2A_20160408-104020-456_L2A_T31TGK_D_V1-0/SENTINEL2A_20160408-104020-456_L2A_T31TGK_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TGL/SENTINEL2A_20160205-103556-319_L2A_T31TGL_D_V1-0/SENTINEL2A_20160205-103556-319_L2A_T31TGL_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TGM/SENTINEL2A_20160528-104248-160_L2A_T31TGM_D_V1-0/SENTINEL2A_20160528-104248-160_L2A_T31TGM_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31TGN/SENTINEL2A_20160205-103556-319_L2A_T31TGN_D_V1-0/SENTINEL2A_20160205-103556-319_L2A_T31TGN_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31UCP/SENTINEL2A_20151203-105818-575_L2A_T31UCP_D_V1-0/SENTINEL2A_20151203-105818-575_L2A_T31UCP_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31UCQ/SENTINEL2A_20151206-110834-178_L2A_T31UCQ_D_V1-0/SENTINEL2A_20151206-110834-178_L2A_T31UCQ_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31UCR/SENTINEL2A_20151229-111920-437_L2A_T31UCR_D_V1-0/SENTINEL2A_20151229-111920-437_L2A_T31UCR_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31UCS/SENTINEL2A_20160125-111611-703_L2A_T31UCS_D_V1-0/SENTINEL2A_20160125-111611-703_L2A_T31UCS_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31UDP/SENTINEL2A_20160102-110129-139_L2A_T31UDP_D_V1-0/SENTINEL2A_20160102-110129-139_L2A_T31UDP_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31UDQ/SENTINEL2A_20160125-111611-703_L2A_T31UDQ_D_V1-0/SENTINEL2A_20160125-111611-703_L2A_T31UDQ_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31UDR/SENTINEL2A_20151226-111142-750_L2A_T31UDR_D_V1-0/SENTINEL2A_20151226-111142-750_L2A_T31UDR_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31UDS/SENTINEL2A_20160125-111611-703_L2A_T31UDS_D_V1-0/SENTINEL2A_20160125-111611-703_L2A_T31UDS_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31UEP/SENTINEL2A_20160717-104026-462_L2A_T31UEP_D_V1-0/SENTINEL2A_20160717-104026-462_L2A_T31UEP_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31UEQ/SENTINEL2A_20160720-105547-946_L2A_T31UEQ_D_V1-0/SENTINEL2A_20160720-105547-946_L2A_T31UEQ_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31UER/SENTINEL2A_20151206-110834-178_L2A_T31UER_D_V1-0/SENTINEL2A_20151206-110834-178_L2A_T31UER_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31UES/SENTINEL2A_20160305-110109-717_L2A_T31UES_D_V1-0/SENTINEL2A_20160305-110109-717_L2A_T31UES_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31UFP/SENTINEL2A_20160720-105547-946_L2A_T31UFP_D_V1-0/SENTINEL2A_20160720-105547-946_L2A_T31UFP_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31UFQ/SENTINEL2A_20160511-105343-672_L2A_T31UFQ_D_V1-0/SENTINEL2A_20160511-105343-672_L2A_T31UFQ_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31UFR/SENTINEL2A_20160607-104026-455_L2A_T31UFR_D_V1-0/SENTINEL2A_20160607-104026-455_L2A_T31UFR_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31UFS/SENTINEL2A_20160508-104027-456_L2A_T31UFS_D_V1-0/SENTINEL2A_20160508-104027-456_L2A_T31UFS_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31UGP/SENTINEL2A_20160408-104020-456_L2A_T31UGP_D_V1-0/SENTINEL2A_20160408-104020-456_L2A_T31UGP_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31UGQ/SENTINEL2A_20160816-104025-461_L2A_T31UGQ_D_V1-0/SENTINEL2A_20160816-104025-461_L2A_T31UGQ_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T31UGR/SENTINEL2A_20160119-105107-606_L2A_T31UGR_D_V1-0/SENTINEL2A_20160119-105107-606_L2A_T31UGR_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T32TLP/SENTINEL2A_20160405-103019-462_L2A_T32TLP_D_V1-0/SENTINEL2A_20160405-103019-462_L2A_T32TLP_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T32TLQ/SENTINEL2A_20160803-103724-960_L2A_T32TLQ_D_V1-0/SENTINEL2A_20160803-103724-960_L2A_T32TLQ_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T32TLR/SENTINEL2A_20160326-103406-538_L2A_T32TLR_D_V1-0/SENTINEL2A_20160326-103406-538_L2A_T32TLR_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T32TLS/SENTINEL2A_20160126-104630-775_L2A_T32TLS_D_V1-0/SENTINEL2A_20160126-104630-775_L2A_T32TLS_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T32TLT/SENTINEL2A_20160126-104630-775_L2A_T32TLT_D_V1-0/SENTINEL2A_20160126-104630-775_L2A_T32TLT_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T32TMM/SENTINEL2A_20160711-102030-066_L2A_T32TMM_D_V1-0/SENTINEL2A_20160711-102030-066_L2A_T32TMM_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T32TMN/SENTINEL2A_20160728-101603-978_L2A_T32TMN_D_V1-0/SENTINEL2A_20160728-101603-978_L2A_T32TMN_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T32TNL/SENTINEL2A_20160728-101603-978_L2A_T32TNL_D_V1-0/SENTINEL2A_20160728-101603-978_L2A_T32TNL_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T32TNM/SENTINEL2A_20160718-101028-464_L2A_T32TNM_D_V1-0/SENTINEL2A_20160718-101028-464_L2A_T32TNM_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T32TNN/SENTINEL2A_20160708-101602-980_L2A_T32TNN_D_V1-0/SENTINEL2A_20160708-101602-980_L2A_T32TNN_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T32ULU/SENTINEL2A_20160126-104630-775_L2A_T32ULU_D_V1-0/SENTINEL2A_20160126-104630-775_L2A_T32ULU_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T32ULV/SENTINEL2A_20151207-103733-673_L2A_T32ULV_D_V1-0/SENTINEL2A_20151207-103733-673_L2A_T32ULV_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T32UMU/SENTINEL2A_20151207-103733-673_L2A_T32UMU_D_V1-0/SENTINEL2A_20151207-103733-673_L2A_T32UMU_D_V1-0_FRE_B2.tif', '/work/theia/oso/sensorsDatas/S2/20152016//T32UMV/SENTINEL2A_20160714-103025-460_L2A_T32UMV_D_V1-0/SENTINEL2A_20160714-103025-460_L2A_T32UMV_D_V1-0_FRE_B2.tif']
    driver = ogr.GetDriverByName("ESRI Shapefile")
    try:
        if os.path.exists(outGridPath):
            driver.DeleteDataSource(outGridPath)
        output = driver.CreateDataSource(outGridPath)
    except ValueError:
        raise Exception("Could not create output datasource "+outGridPath)

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(int(outputProjection))
    layer = output.CreateLayer(outGridPath.split("/")[-1].replace(".shp", ""), geom_type=ogr.wkbPolygon, srs=srs)
    layer.CreateField(ogr.FieldDefn(tileNameField, ogr.OFTString))
    layerDef = layer.GetLayerDefn()
    if layer is None:
        raise Exception("Could not create output layer")

    for currentTile in paths:
        currentProjection = fu.getRasterProjectionEPSG(currentTile)
        minX, maxX, minY, maxY = fu.getRasterExtent(currentTile)
        upperL = (minX, maxY)
        upperR = (maxX, maxY)
        lowerL = (minX, minY)
        lowerR = (maxX, minY)
        upperL_out = converCoord(upperL, int(currentProjection), int(outputProjection))
        upperR_out = converCoord(upperR, int(currentProjection), int(outputProjection))
        lowerL_out = converCoord(lowerL, int(currentProjection), int(outputProjection))
        lowerR_out = converCoord(lowerR, int(currentProjection), int(outputProjection))
        TileName = getTileNameFromRaster(currentTile)
        addTileToGrid(upperL_out, upperR_out, lowerR_out, lowerL_out, layer, layerDef, tileNameField, TileName)

    output.Destroy()

def getIntersections(outGridPath, inGridPath, tileField_first, tileField_second):

    """
    OUT
    AllIntersections [list of tuple] : [(S2Tile, [L8Tile, L8Tile, L8Tile]), (...), ...]
    """
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataOut = driver.Open(outGridPath, 0)
    dataIn = driver.Open(inGridPath, 0)

    layerOut = dataOut.GetLayer()
    layerIn = dataIn.GetLayer()

    AllIntersections = []#Ex : [[S2, [L8, L8, ..., L8]], [], ...]

    outTiles = [(outTile.GetGeometryRef().Clone(), outTile.GetField(tileField_first)) for outTile in layerOut]
    inTiles = [(inTile.GetGeometryRef().Clone(), inTile.GetField(tileField_second)) for inTile in layerIn]

    for outTileGeom, outTile in outTiles:
        for inTileGeom, inTile in inTiles:
            intersection = outTileGeom.Intersection(inTileGeom)
            if intersection.GetArea() != 0.0 and (outTile, inTile) not in AllIntersections:
                AllIntersections.append((outTile, inTile))
    return fu.sortByFirstElem(AllIntersections)

def getTileEnvelope(inputGRID, fieldName, refTile):

    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataIn = driver.Open(inputGRID, 0)
    layerIn = dataIn.GetLayer()
    for feature in layerIn:
        if feature.GetField(fieldName) == refTile:
            geom = feature.GetGeometryRef()
            env = geom.GetEnvelope()
            return env[0], env[1], env[2], env[3]#minX, maxX, minY, maxY

def getAllDatasByDate(currentTile, rasterPatterns, masksPatterns, arboRaster, arboMask, TileFolder, rasterInitValue, masksInitValues):

    #get all raster into the current tile and store it with init value
    buf = []
    r = []
    for currentPattern in rasterPatterns:
        r += fu.fileSearchRegEx(TileFolder+currentTile+arboRaster+currentPattern)
    for currentR in r:
        buf.append((currentR, rasterInitValue))

    for currentPattern, currentMaskInit in zip(masksPatterns, masksInitValues):
        m = []
        m += fu.fileSearchRegEx(TileFolder+currentTile+arboMask+currentPattern)
        for currentM in m:
            buf.append((currentM, currentMaskInit))
    #sort it by date
    buff = [(getDateFromRaster(currentRaster[0]), currentRaster)for currentRaster in buf]
    buff = fu.sortByFirstElem(buff)
    allDates = []
    allRasters = []
    for date, rasters in buff:
        allDates.append(date)
        allRasters.append(rasters)
    return allRasters, allDates

def checkMaskFromRaster(raster, maskPatterns):
    for currentPattern in maskPatterns:
        if currentPattern in raster:
            return True
    return False

def launchFit(sensorName, cmdPath, workingDirectory, outDirectory, outGridPath, outputGrid_tileNameField, outPixRes, outputProjection, interpolator, inputGrid_tileNameField, inputGRID, arboMask, masksInitValues, masksPatterns, arboRaster, rasterInitValue, rasterPatterns, TileFolder):

    createOutGrid(TileFolder, rasterPatterns[0], outputProjection, outputGrid_tileNameField, outGridPath)
    intersections = getIntersections(inputGRID, outGridPath, inputGrid_tileNameField, outputGrid_tileNameField)
    allCmd = []
    for refTile, tiles in intersections:
        outFolder_tile = outDirectory+"/"+refTile
        if not os.path.exists(outFolder_tile):
            os.mkdir(outFolder_tile)
        minX_ref, maxX_ref, minY_ref, maxY_ref = getTileEnvelope(inputGRID, inputGrid_tileNameField, refTile)
        for currentTile in tiles:
            datas, dates = getAllDatasByDate(currentTile, rasterPatterns, masksPatterns, arboRaster, arboMask, TileFolder, rasterInitValue, masksInitValues)
            for currentDatas, currentDate in zip(datas, dates):
                outFolderDate = outFolder_tile+"/"+sensorName+"_"+refTile+"_"+currentDate+"_"+currentTile
                outFolderDateMask = outFolderDate+"/MASKS"
                if not os.path.exists(outFolderDate):
                    os.mkdir(outFolderDate)
                    os.mkdir(outFolderDateMask)
                for currentRaster in currentDatas:
                    folder = outFolderDate
                    print currentRaster
                    if checkMaskFromRaster(currentRaster[0], masksPatterns):
                        folder = outFolderDateMask
                    outFolder = folder
                    if workingDirectory:
                        folder = workingDirectory+"/"
                    outName = currentRaster[0].split("/")[-1].replace(currentTile, refTile).replace(".tif", "_"+currentTile+".tif")
                    out = folder+"/"+outName
                    cmd = "gdalwarp -t_srs EPSG:"+outputProjection+" -wo INIT_DEST="+currentRaster[1]+" -te "+str(minX_ref)+" "+str(minY_ref)+" "+str(maxX_ref)+" "+str(maxY_ref)+" -tr "+outPixRes+" -"+outPixRes+" -r "+interpolator+" "+currentRaster[0]+" "+out
                    if not os.path.exists(outFolder+"/"+outName):
                        allCmd.append(cmd)
                        run(cmd)
                        if workingDirectory:
                            shutil.copy(out, outFolder+"/"+outName)
                            os.remove(out)
    fu.writeCmds(cmdPath, allCmd)
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Change projection of a set of datas according to a spatial grid")

    parser.add_argument("-in.tileFolder", dest="TileFolder", help="", default=None, required=True)
    parser.add_argument("-in.sensorName", dest="sensorName", help="", default=None, required=True)
    parser.add_argument("-in.rasterPatterns", dest="rasterPatterns", help="", nargs='+', default=None, required=True)
    parser.add_argument("-in.rasterInitValue", dest="rasterInitValue", help="", default=None, required=True)
    parser.add_argument("-in.arboRaster", dest="arboRaster", help="", default=None, required=True)
    parser.add_argument("-in.masksPatterns", dest="masksPatterns", help="", nargs='+', default=None, required=True)
    parser.add_argument("-in.masksInitValues", dest="masksInitValues", help="", nargs='+', default=None, required=True)
    parser.add_argument("-in.arboMask", dest="arboMask", help="", default=None, required=True)
    parser.add_argument("-in.GRID", dest="inputGRID", help="", default=None, required=True)
    parser.add_argument("-in.field", dest="inputGrid_tileNameField", help="", default=None, required=True)
    parser.add_argument("-out.interpolator", dest="interpolator", help="", default=None, required=True)
    parser.add_argument("-out.projection", dest="outputProjection", help="", default=None, required=True)
    parser.add_argument("-out.resolution", dest="outPixRes", help="", default=None, required=True)
    parser.add_argument("-out.field", dest="outputGrid_tileNameField", help="", default=None, required=True)
    parser.add_argument("-out.GRID", dest="outGridPath", help="", default=None, required=True)
    parser.add_argument("-out.directory", dest="outDirectory", help="", default=None, required=True)
    parser.add_argument("-out.workingDirectory", dest="workingDirectory", help="", default=None)
    parser.add_argument("-out.cmdPath", dest="cmdPath", help="", default=None, required=True)

    args = parser.parse_args()

    launchFit(args.sensorName, args.cmdPath, args.workingDirectory, args.outDirectory, args.outGridPath, args.outputGrid_tileNameField, args.outPixRes, args.outputProjection, args.interpolator, args.inputGrid_tileNameField, args.inputGRID, args.arboMask, args.masksInitValues, args.masksPatterns, args.arboRaster, args.rasterInitValue, args.rasterPatterns, args.TileFolder)

    #python gridFit.py -in.tileFolder /work/S2/ -in.sensorName Sentinel2 -in.rasterPatterns FRE_B2.tif FRE_B3.tif FRE_B4.tif FRE_B5.tif FRE_B6.tif FRE_B7.tif FRE_B8.tif FRE_B8A.tif FRE_B11.tif FRE_B12.tif -in.rasterInitValue -10000 -in.arboRaster '/*/*' -in.masksPatterns CLM_R1.tif EDG_R1.tif SAT_R1.tif -in.masksInitValues 0 1 0 -in.arboMask '/*/MASKS/*' -in.GRID /L8_grid.shp -in.field Tile -out.interpolator cubic -out.projection 2154 -out.resolution 10 -out.field tile -out.GRID /S2_grid_V2.shp -out.directory /work/ -out.workingDirectory $TMPDIR -out.cmdPath /reprojection.txt



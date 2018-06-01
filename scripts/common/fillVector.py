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

import argparse
#import os
#import random
#from collections import defaultdict
#from osgeo import gdal
from osgeo import ogr
#from osgeo import osr
from Common import FileUtils as fu


def extraction(vectorFill, vectorSource, field, field_val, driversFill, driversSource):

    ogrDriversFill = [ogr.GetDriverByName(currentDriver) for currentDriver in driversFill]
    ogrDriversSource = ogr.GetDriverByName(driversSource)

    dataSourceFill = [currentDriver.Open(currentShape, 1) for currentDriver, currentShape in zip(ogrDriversFill, vectorFill)]
    dataSourceSource = ogrDriversSource.Open(vectorSource, 0)

    layerFill = [currentDataSource.GetLayer() for currentDataSource in dataSourceFill]
    layerSource = dataSourceSource.GetLayer()
    FIDColumn = layerSource.GetFIDColumn()
    if FIDColumn == "":
        FIDColumn = "FID"

    FIDMAX = [max([feat.GetFID() for feat in currentLayerToFill]) for currentLayerToFill in layerFill]

    listFieldSource = fu.getAllFieldsInShape(vectorSource, driversSource)

    All_FID = [(currentFeat.GetField(field), currentFeat.GetFID()) for currentFeat in layerSource if currentFeat.GetField(field) in field_val]
    layerSource.ResetReading()
    for layerToFill in layerFill:
        layerToFill.ResetReading()
    All_FID = fu.sortByFirstElem(All_FID)

    for currentClass, FID in All_FID:
        splits = fu.splitList(FID, len(vectorFill))
        i = 0
        for currentSplit, layerToFill, fidMax in zip(splits, layerFill, FIDMAX):

            chunkSublistFID = fu.splitList(currentSplit, 1+int(len(currentSplit)/1000))
            filterFID = "("+" OR ".join(["("+" OR ".join([FIDColumn+"="+str(currentFID) for currentFID in chunk])+")" for chunk in chunkSublistFID])+")"
            layerSource.SetAttributeFilter(filterFID)
            newfid = fidMax
            print "Ajout de "+str(currentClass)+" dans "+vectorFill[i]+" filter : "+filterFID
            for feature in layerSource:
                geom = feature.GetGeometryRef()
                print geom
                dstfeature = ogr.Feature(layerSource.GetLayerDefn())
                dstfeature.SetGeometry(geom)
                dstfeature.SetFID(newfid + 1)
                newfid += 1
                indIn = 0
                while indIn < len(listFieldSource):
                    dstfeature.SetField(listFieldSource[indIn], feature.GetField(listFieldSource[indIn]))
                    indIn += 1
                layerToFill.CreateFeature(dstfeature)

                dstfeature.Destroy()
            i += 1


    for layerToFill in layerFill:
        layerToFill = None
    layerSource = None

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="all vector must have the same fields")
    parser.add_argument("-vectorToFill", dest="vectorFill", help="vectors to fill up", default=None, required=True, nargs='+')
    parser.add_argument("-vectorSource", dest="vectorSource", help="source vector", default=None, required=True)
    parser.add_argument("-field", dest="field", help="data's field", default=None, required=True)
    parser.add_argument("-field.value", dest="field_val", help="field's value", default=None, type=int, required=True, nargs='+')
    parser.add_argument("-vectorToFill.driver", dest="driversFill", help="source's drivers", default=None, required=True, nargs='+')
    parser.add_argument("-vectorSource.driver", dest="driversSource", help="source's drivers", default=None, required=True)

    args = parser.parse_args()

    extraction(args.vectorFill, args.vectorSource, args.field, args.field_val, args.driversFill, args.driversSource)

#python fillVector.py -vectorSource.driver "ESRI Shapefile" -vectorToFill.driver "ESRI Shapefile" "ESRI Shapefile" -field.value 1 -field code -vectorSource /mnt/sdb1/Data/corse/test_sansForet.shp -vectorToFill /mnt/sdb1/Data/corse/test_avecForet_1.shp /mnt/sdb1/Data/corse/test_avecForet_2.shp













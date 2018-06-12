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
import os
import random
from collections import defaultdict
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from Common import FileUtils as fu

def extraction(shapeE, DriverE, field, field_val, nb_extrac, shapeS, fieldo, DriverS):

    driver = ogr.GetDriverByName(DriverE)
    dataSource = driver.Open(shapeE, 0)
    layer = dataSource.GetLayer()

    driver = ogr.GetDriverByName(DriverS)
    dataSourceS = driver.Open(shapeS, 1)
    layerS = dataSourceS.GetLayer()

    print "checking FID"
    All_FID = [(currentFeat.GetField(field), currentFeat.GetFID()) for currentFeat in layer if currentFeat.GetField(field) in field_val]
    All_FID = fu.sortByFirstElem(All_FID)
    print "FIDs found"
    # get Fieldo index

    featureDefnS = layerS.GetLayerDefn()
    indfieldo = featureDefnS.GetFieldIndex(fieldo)

    # Fields Lists
    listFieldIn = fu.getAllFieldsInShape(shapeE, DriverE)
    listFieldOut = fu.getAllFieldsInShape(shapeS, DriverS)

    numberOfFeatures = layerS.GetFIDColumn()

    # in case of not closed layers

    layerS.ResetReading()
    layer.ResetReading()

    i = 0
    fid_ind = layerS
    for val in field_val:
        print "fill up "+str(val)+" values"
        # list of Fid of the current landcover type (val)
        listFid = [x[1] for x in All_FID if x[0] == val][0]
        # Random selection
        print len(listFid)
        nbExtraction = nb_extrac[i]
        if nbExtraction > len(listFid):
            nbExtraction = len(listFid)
            print "Warning : class "+str(val)+" extraction set to "+str(nbExtraction)
            sublistFid = random.sample(listFid, nbExtraction)

        chunkSublistFID = fu.splitList(sublistFid, 1+int(len(sublistFid)/1000))
        filterFID = []
        for chunk in chunkSublistFID:
            # Filter input shapefile
            filterFID.append("("+" OR ".join([layer.GetFIDColumn()+"="+str(currentFID) for currentFID in chunk])+")")

        ffilter = " OR ".join(filterFID)
        layer.SetAttributeFilter(ffilter)
        newfid = max([feat.GetFID() for feat in layerS])
        # filtered input features into output shapefile
        for feature in layer:
            geom = feature.GetGeometryRef()
            dstfeature = ogr.Feature(layerS.GetLayerDefn())
            dstfeature.SetGeometry(geom)
            dstfeature.SetFID(newfid + 1)
            newfid += 1
            indIn = 0
            while indIn < len(listFieldIn):
                dstfeature.SetField(listFieldOut[indIn], feature.GetField(listFieldIn[indIn]))
                indIn += 1
            layerS.CreateFeature(dstfeature)
            dstfeature.Destroy()
        i += 1

        layerS = layer = None

    print "DONE"

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-in.extract", dest="shapeE", help="path to the folder which contains samples", default=None, required=True)
    parser.add_argument("-in.extractDriver", dest="DriverE", help="driver", default=None, required=True)
    parser.add_argument("-in.field", dest="field", help="data's field", default=None, required=True)
    parser.add_argument("-in.field.value", dest="field_val", help="field's value", default=None, type=int, required=True, nargs='+')
    parser.add_argument("-in.field.value.nbExtract", dest="nbextract", help="field's value", default=None, type=int, required=True, nargs='+')
    parser.add_argument("-in.extract.select", dest="shapeS", help="path to the shapefile in which store samples", default=None, required=True)
    parser.add_argument("-in.field.pop", dest="fieldo", help="Field of the storage shapefile to populate", default=None, required=True)
    parser.add_argument("-in.PopDriver", dest="DriverS", help="driver", default=None, required=True)
    args = parser.parse_args()

    extraction(args.shapeE, args.DriverE, args.field, args.field_val, args.nbextract, args.shapeS, args.fieldo, args.DriverS)

#python extractSample.py -in.PopDriver SQLite -in.field.value.nbExtract 100 -in.field.value 42 -in.field CODE -in.extract /mnt/data/home/vincenta/tmp/testSampleExtraction/France_2014_1CA_T31TCJ_SamplesSel_5p.sqlite -in.extractDriver SQLite -in.extract.select /mnt/data/home/vincenta/tmp/testSampleExtraction/France_2014_1CA_T31TCJ_SamplesSel_20p.sqlite -in.field.pop code

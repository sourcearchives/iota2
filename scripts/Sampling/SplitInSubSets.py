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

import logging
import argparse
import random
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from osgeo.gdalconst import *

from Common import FileUtils as fut

logger = logging.getLogger(__name__)


def get_randomPoly(layer, field, classes, ratio, regionField, regions):
    """
    usage : use to randomly split samples in learning and validation considering
            classes in regions
    """
    sample_id_learn = []
    sample_id_valid = []
    layer.ResetReading()
    for region in regions:
        for cl in classes:
            listid = []
            layer.SetAttributeFilter(None)
            attrib_filter = "{}={} AND {}='{}'".format(field, cl, regionField, region)
            layer.SetAttributeFilter(attrib_filter)
            featureCount = float(layer.GetFeatureCount())
            if featureCount == 1:
                for feat in layer:
                    _id = feat.GetFID()
                    sample_id_learn.append(_id)
                    feature_clone = feat.Clone()
                    layer.CreateFeature(feature_clone)
                    sample_id_valid.append(feature_clone.GetFID())
                    break

            elif featureCount > 1:
                polbysel = round(featureCount * float(ratio))
                if polbysel <= 1:
                    polbysel = 1
                for feat in layer:
                    _id = feat.GetFID()
                    listid.append(_id)
                    listid.sort()

                sample_id_learn += [fid for fid in random.sample(listid, int(polbysel))]
                sample_id_valid += [currentFid for currentFid in listid if currentFid not in sample_id_learn]

    sample_id_learn.sort()
    sample_id_valid.sort()

    layer.SetAttributeFilter(None)
    return sample_id_learn, sample_id_valid


def splitInSubSets(vectoFile, dataField, regionField, 
                   ratio=0.5, seeds=1, driver_name="SQLite", 
                   learning_flag="learn", validation_flag="validation"):
    """
    usage :
    This function is dedicated to split a shape into N subsets\
    of training and validations samples by adding a new field\
    by subsets (seed_X) containing 'learn' or 'validation

    IN
    vectorFile [string] : path to the vector file
    ratio [float] : ratio = learning/validation (0 < ratio < 1
    seeds [int] : numbers of random samples

    OUT
    vectoFile is alerate by adding seeds_X columns
    """

    driver = ogr.GetDriverByName(driver_name)
    source = driver.Open(vectoFile, 1)
    layer = source.GetLayer(0)

    class_avail = fut.getFieldElement(vectoFile, driverName=driver_name,
                                      field=dataField, mode="unique", elemType="int")
    region_avail = fut.getFieldElement(vectoFile, driverName=driver_name,
                                       field=regionField, mode="unique", elemType="str")
    all_fields = fut.getAllFieldsInShape(vectoFile, driver=driver_name)
    for seed in range(seeds):
        source = driver.Open(vectoFile, 1)
        layer = source.GetLayer(0)

        seed_field_name = "seed_" + str(seed)
        seed_field = ogr.FieldDefn(seed_field_name, ogr.OFTString)
        if seed_field_name not in all_fields:
            layer.CreateField(seed_field)
        id_learn, id_val = get_randomPoly(layer, dataField,
                                          class_avail, ratio,
                                          regionField, region_avail)

        fid = [f.GetFID() for f in layer]

        for i in fid:
            flag = None
            if i in id_learn:
                flag = learning_flag
            elif i in id_val:
                flag = validation_flag
            feat = layer.GetFeature(i)
            feat.SetField(seed_field_name, flag)
            layer.SetFeature(feat)
        i = layer = None


if __name__ == "__main__":
    func_description = "This function is dedicated to split a shape into N subsets\
                        of training and validations samples by adding a new field\
                        by subsets (seed_X) containing 'learn' or 'validation'"

    parser = argparse.ArgumentParser(description=func_description)
    parser.add_argument("-vector", dest="vectoFile",
                        help="path to the vector file",
                        required=True)
    parser.add_argument("-dataField", dest="dataField",
                        help="field in vector file to consider",
                        required=True)
    parser.add_argument("-ratio", dest="ratio",
                        help="ratio = learning/validation (0 < ratio < 1)",
                        required=False,
                        type=float,
                        default=0.5)
    parser.add_argument("-seeds", dest="seeds",
                        help="number of subsets",
                        required=False,
                        type=int,
                        default=1)

    args = parser.parse_args()
    splitInSubSets(args.vectoFile, args.dataField, args.ratio, args.seeds)

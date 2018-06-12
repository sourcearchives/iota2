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
#import random
#from collections import defaultdict
#from osgeo import gdal
from osgeo import ogr
#from osgeo import osr
from Common import FileUtils as fu


def extraction(vectorFill, vectorSource, field, field_val, driversFill, driversSource):

    ogrDriversSource = ogr.GetDriverByName(driversSource)
    dataSourceSource = ogrDriversSource.Open(vectorSource, 0)

    layerSource = dataSourceSource.GetLayer()

    print "RECHERCHE DES FIDs"
    All_FID = [(currentFeat.GetField(field), str(currentFeat.GetFID())) for currentFeat in layerSource if currentFeat.GetField(field) in field_val]
    print "FIDs trouvée"
    layerSource.ResetReading()

    All_FID = fu.sortByFirstElem(All_FID)

    for currentClass, FID in All_FID:
        splits = fu.splitList(FID, len(vectorFill))
        for currentSplit, currentVectorFill in zip(splits, vectorFill):
            cmd = "ogr2ogr -append "+currentVectorFill+" "+vectorSource+" -where \" fid in ("+",".join(currentSplit)+")\""
            print cmd
            print "Ajout de "+str(currentClass)+" dans "+currentVectorFill.split("/")[-1]
            os.system(cmd)

#-where "fid in (2, 0)"
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

#python fillVector.py -vectorSource.driver "ESRI Shapefile" -vectorToFill.driver "ESRI Shapefile" "ESRI Shapefile" -field.value 1 44 -field code -vectorSource /mnt/sdb1/Data/corse/test_sansForet.shp -vectorToFill /mnt/sdb1/Data/corse/test_avecForet_1.shp /mnt/sdb1/Data/corse/test_avecForet_2.shp












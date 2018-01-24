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
import sys,os,random,shutil
from osgeo import gdal, ogr,osr
import vector_functions as vf

def get_randomPolyAreaThresh(shapefile, field, classe, thresh, outShapefile):

    # Get Id and Area of all features
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(shapefile, 0)
    layer = dataSource.GetLayer()

    # Field type
    fieldList = vf.getFields(layer)
    try:
        indfield = fieldList.index(field)
    except:
        print "The field {} does not exist in the input shapefile".format(field)
        print "You must choose one of these existing fields : {}".format(' / '.join(fieldList))
        sys.exit(-1)
        
    inLayerDefn = layer.GetLayerDefn()
    fieldTypeCode = inLayerDefn.GetFieldDefn(indfield).GetType()
    fieldType = inLayerDefn.GetFieldDefn(indfield).GetFieldTypeName(fieldTypeCode)

    # Filter on given class
    if fieldType != "String":
        layer.SetAttributeFilter(field + "=" + str(classe))
    else:
        layer.SetAttributeFilter(field + '=\"' + classe + '\"')        

    print "Get FID and Area values"    
    listid = []
    for feat in layer:
        geom = feat.GetGeometryRef()
        listid.append([feat.GetFID(), geom.GetArea()])

    print "Random selection"
    # random selection based on area sum threshold        
    sumarea = 0
    listToChoice = []
    while float(sumarea) <= float(thresh) and len(listid) != 0:
        elt = random.sample(listid, 1)
        listToChoice.append(elt[0][0])
        listid.remove(elt[0])
        sumarea += float(elt[0][1])

    strCondglob = ",".join([str(x) for x in listToChoice])    
    f = open('/datalocal/tmp/listfid.txt','w')
    f.write(strCondglob)
    f.close()
    
    #listdict = split_dict_equally(listToChoice, 20)
    listdict = [listToChoice[i::20] for i in xrange(20)]
    
    print "Write shapefiles"
    i = 0
    for block in listdict:
        # Extract selected features
        strCond = " OR ".join(["FID="+str(x) for x in block])
        dataSource = driver.Open(shapefile, 0)    
        layer = dataSource.GetLayer()
        layer.SetAttributeFilter(strCond)
        outShapefileblock = os.path.splitext(outShapefile)[0] + '_' + str(i) + '.shp'
        vf.CreateNewLayer(layer, outShapefileblock)
        layer = dataSource = None
        i += 1
        
        print "Random Selection of polygons with value '{}' of field '{}' done and stored in '{}'".format(classe, field, outShapefileblock)

                                  
def split_dict_equally(input_dict, chunks=2):
    "Splits dict by keys. Returns a list of dictionaries."
    # prep with empty dicts
    return_list = [dict() for idx in xrange(chunks)]
    idx = 0
    for k, v in input_dict.iteritems():
        return_list[idx][k] = v
        if idx < chunks-1:  # indexes start at 0
            idx += 1
        else:
            idx = 0
    return return_list
                                  
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allows to randomnly extract polygons from input shapefile given a sum of areas threshold")

	parser.add_argument("-shape",help ="path to a shapeFile (mandatory)", dest = "path", required=True)
	parser.add_argument("-field",help ="data's field into shapeFile (mandatory)", dest = "field", required=True)
	parser.add_argument("-class", dest = "classe", help ="class name to extrac", required=True)
	parser.add_argument("-thresh",dest = "thresh", help ="Area threshold", required=True)
	parser.add_argument("-out",dest = "output", help ="Output shapefile", required=True)
	args = parser.parse_args()

	get_randomPolyAreaThresh(args.path, args.field, args.classe, args.thresh,args.output)    

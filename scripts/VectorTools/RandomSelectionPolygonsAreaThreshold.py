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
import sys, os, random, shutil
import math
from osgeo import gdal, ogr, osr
import pickle
from VectorTools import vector_functions as vf
from Common import FileUtils as fut

def get_randomPolyAreaThresh(shapefile, field, classe, thresh, outlistfid = "", split = 1, outShapefile = None, nolistid = None):

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
    #listid = []
    listiddic = {}
    for feat in layer:
        geom = feat.GetGeometryRef()
        if geom is not None:
            listiddic[feat.GetFID()] = geom.GetArea()

    if nolistid is not None:
        f = open(nolistid,'r')
        nolistidstr = f.readline()
        nolistidtab = nolistidstr.split(',')
        nofid = set([int(y) for y in nolistidtab])
        listidtokeep = set(list(listiddic.keys())).difference(nofid)
        listidfinal = [(x, listiddic[x]) for x in list(listidtokeep)]
        #listidfinal = [x for x in listid if x[0] in listidtokeep]
        #print listid
        #listid = [x for x in listid if x[0] not in [int(y) for y in nolistidtab]]
        #print listid
    else:
        listidfinal = listiddic.items()
        
    print "Random selection"
    # random selection based on area sum threshold        
    sumarea = 0
    listToChoice = []
    while float(sumarea) <= float(thresh) and len(listidfinal) != 0:
        elt = random.sample(listidfinal, 1)
        listToChoice.append(elt[0][0])
        listidfinal.remove(elt[0])
        sumarea += float(elt[0][1])

    strCondglob = ",".join([str(x) for x in listToChoice])
    if outlistfid != None:
        print "Listid"
        f = open(outlistfid, 'w')
        f.write(strCondglob)
        f.close()
    
    sqlite3_query_limit = 1000.0
    if outShapefile is not None:
        print "Write shapefiles"
        lyrname = os.path.splitext(os.path.basename(shapefile))[0]
        nb_sub_split_SQLITE = int(math.ceil(len(listToChoice)/sqlite3_query_limit))
        sub_FID_sqlite = fut.splitList(listToChoice, nb_sub_split_SQLITE)

        subFid_clause = []
        for subFID in sub_FID_sqlite:
            subFid_clause.append("(FID in ({}))".format(", ".join(map(str, subFID))))
        fid_clause = " OR ".join(subFid_clause)
        sql_clause = "ogr2ogr -sql 'SELECT * FROM {} WHERE {}' {} {}".format(lyrname, fid_clause, outShapefile, shapefile)
        with open("/work/OT/theia/oso/vincent/RPG2017/samples/tmp/sqlclause11", 'wb') as fp:
            pickle.dump(sql_clause, fp)
        os.system(sql_clause)
        print "Done"
        ''' 
        
        listdict = [listToChoice[i::split] for i in xrange(split)]
        
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
        '''                          
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allows to randomnly extract polygons from input shapefile given a sum of areas threshold")

	parser.add_argument("-shape", help = "path to a shapeFile (mandatory)", dest = "path", required=True)
	parser.add_argument("-field", help = "data's field into shapeFile (mandatory)", dest = "field", required=True)
	parser.add_argument("-class", dest = "classe", help = "class name to extrac", required=True)
	parser.add_argument("-thresh", dest = "thresh", help = "Area threshold", required=True)
	parser.add_argument("-out", dest = "output", help = "Output shapefile")
	parser.add_argument("-nolistid", dest = "nolistid", help = "list of field's values to not select (text file with values separated with comma)")
	parser.add_argument("-outlist", dest = "outputlist", help = "Output file for fid list storage")
	parser.add_argument("-split", dest = "split", help = "Split output shapefile storage", default = 1, type = int)                
	args = parser.parse_args()

	get_randomPolyAreaThresh(args.path, args.field, args.classe, args.thresh, args.outputlist, args.split, args.output, args.nolistid)    

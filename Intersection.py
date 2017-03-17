#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys, os
from osgeo import ogr
import argparse
import vector_functions as vf

def intersection(file1, file2, outfile):
    
    ds1 = vf.openToRead(file1)
    ds2 = vf.openToRead(file2)

    layer1 = ds1.GetLayer()
    layer2 = ds2.GetLayer()   

    if layer1.GetSpatialRef().GetAttrValue("AUTHORITY", 1) == layer2.GetSpatialRef().GetAttrValue("AUTHORITY", 1):
        srsObj = layer1.GetSpatialRef()
    else:
        print "second shapefile must have the same projection than the first shapefile (EPSG:{} vs. EPSG:{})"\
            .format(layer1.GetSpatialRef().GetAttrValue("AUTHORITY", 1), layer2.GetSpatialRef().GetAttrValue("AUTHORITY", 1))
        sys.exit(-1)
    
    outDriver = ogr.GetDriverByName("ESRI Shapefile")

    # Find geometry of the intersection
    if defineIntersectGeometry(layer1, layer2) in ['POLYGON', 'MULTIPOLYGON']:
        #if exists, delete it
        if os.path.exists(outfile):
            outDriver.DeleteDataSource(outfile)
        outDataSource = outDriver.CreateDataSource(outfile)

        #Creates the spatial reference of the output layer
        outLayer = outDataSource.CreateLayer("intersect", srsObj, geom_type = ogr.wkbPolygon)
    else:
        print "This program only produces POLYGONS intersection"

  
    # gestion des champs du premier layer
    inLayerDefn = layer1.GetLayerDefn()
    for i in range(0, inLayerDefn.GetFieldCount()):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        outLayer.CreateField(fieldDefn)
   
    # gestion des champs du second layer
    inLayerDefn = layer2.GetLayerDefn()
    for i in range(0, inLayerDefn.GetFieldCount()):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        outLayer.CreateField(fieldDefn)

    # Liste des champs de trois entités
    listfieldin1 = vf.getFields(layer1)
    listfieldin2 = vf.getFields(layer2)
    listfieldout = vf.getFields(outLayer)        

    layer1.ResetReading() 
    layer2.ResetReading()
    for feature1 in layer1:
        geom1 = feature1.GetGeometryRef()            
        for feature2 in layer2:
            geom2 = feature2.GetGeometryRef()
            # select only the intersections
            if geom2.Intersects(geom1): 
                intersection = geom2.Intersection(geom1)
                dstfeature = ogr.Feature(outLayer.GetLayerDefn())
                dstfeature.SetGeometry(intersection)               
                #gestion des champs
                i = 0
                j = 0
                k = 0
                while i < len(listfieldout):
                    while j < len(listfieldin1):
                        dstfeature.SetField(listfieldout[i], feature1.GetField(listfieldin1[j]))                      
                        i += 1
                        j += 1          
                    while k < len(listfieldin2):
                        dstfeature.SetField(listfieldout[i], feature2.GetField(listfieldin2[k]))                      
                        i += 1
                        k += 1
                outLayer.CreateFeature(dstfeature)
                dstfeature.Destroy()
        layer2.ResetReading()
    outLayer = None
    outDataSource = None

                
def defineIntersectGeometry(layer1, layer2):
    
    union1 = ogr.Geometry(layer1.GetGeomType())
    # union all the geometrical features of layer 1
    for feat in layer1:
        geom =feat.GetGeometryRef()
        union1 = union1.Union(geom)

    # same for layer2
    union2=ogr.Geometry(layer2.GetGeomType())
    for feat in layer2:
        geom =feat.GetGeometryRef()  
        union2 = union2.Union(geom)

    # intersection
    intersection = union1.Intersection(union2)

    # retunr geometryName of the intersection
    return intersection.GetGeometryName()

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Intersection of two shapefiles")
        parser.add_argument("-s1", dest ="first", action="store", \
                            help="First shapefile path")
        parser.add_argument("-s2", dest="second", action="store", \
                            help="Second shapefile path")        
        parser.add_argument("-o", dest="outshapefile", action="store", \
                            help="ESRI Shapefile output filename and path", required = True)
	args = parser.parse_args()
        intersection(args.first, args.second, args.outshapefile)

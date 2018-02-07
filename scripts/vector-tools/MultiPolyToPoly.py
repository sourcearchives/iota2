#!/usr/bin/python

import os
import argparse
from osgeo import ogr, gdal
import sys
import vector_functions as vf
gdal.UseExceptions()

def addPolygon(feat, simplePolygon, in_lyr, out_lyr, field_name_list):
    featureDefn = in_lyr.GetLayerDefn()
    polygon = ogr.CreateGeometryFromWkb(simplePolygon)
    out_feat = ogr.Feature(featureDefn)
    for field in field_name_list:
	inValue = feat.GetField(field)
	out_feat.SetField(field, inValue)

    out_feat.SetGeometry(polygon)
    out_lyr.CreateFeature(out_feat)
    out_lyr.SetFeature(out_feat)


def manageMultiPoly2Poly(in_lyr, out_lyr, field_name_list):
    for in_feat in in_lyr:
        geom = in_feat.GetGeometryRef()
        if geom is not None:
            if geom.GetGeometryName() == 'MULTIPOLYGON':
                for geom_part in geom:
                    addPolygon(in_feat, geom_part.ExportToWkb(), in_lyr, out_lyr, field_name_list)
            else:
                addPolygon(in_feat, geom.ExportToWkb(), in_lyr, out_lyr, field_name_list)


def multipoly2poly(inshape, outshape):

    # Get field list
    field_name_list = vf.getFields(inshape)
    
    # Open input and output shapefile
    driver = ogr.GetDriverByName('ESRI Shapefile')
    in_ds = driver.Open(inshape, 0)
    in_lyr = in_ds.GetLayer()
    inLayerDefn = in_lyr.GetLayerDefn()
    srsObj = in_lyr.GetSpatialRef()
    if os.path.exists(outshape):
        driver.DeleteDataSource(outshape)

    out_ds = driver.CreateDataSource(outshape)
    out_lyr = out_ds.CreateLayer('poly', srsObj, geom_type = ogr.wkbPolygon)

    for i in range(0, len(field_name_list)):
	fieldDefn = inLayerDefn.GetFieldDefn(i)
	fieldName = fieldDefn.GetName()
	if fieldName not in field_name_list:
		continue
	out_lyr.CreateField(fieldDefn)

    manageMultiPoly2Poly(in_lyr, out_lyr, field_name_list)

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Transform multipolygons shapefile" \
        "in single polygons shapefile")
        parser.add_argument("-s", dest="inshapefile", action="store", \
                            help="Input shapefile", required = True) 
        parser.add_argument("-o", dest="outshapefile", action="store", \
                            help="Output shapefile without multipolygons", required = True)
	args = parser.parse_args()
        multipoly2poly(args.inshapefile, args.outshapefile)

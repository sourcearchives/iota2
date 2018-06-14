#!/usr/bin/python

import os
import glob
import sys
import vector_functions as vf
import os.path
import osgeo.ogr
import argparse

def FileByClass(vectorlayer, field, value, opath):
#def FileByClass(vectorlayer, expression, opath):

        if not isinstance(vectorlayer, osgeo.ogr.Layer):
                ds = vf.openToRead(vectorlayer)
                lyr = ds.GetLayer()
        else:
	        lyr = vectorlayer

        if os.path.splitext(opath)[1] != ".shp":
                print "ESRI Shapefile required for output, output name will be replaced to {}.shp".format(os.path.splitext(opath)[0])
                opath = os.path.splitext(opath)[0] + '.shp'
        
	lyr_dfn = lyr.GetLayerDefn()
	inLayerDefn = lyr.GetLayerDefn()
	field_name_list = []

	if not isinstance(vectorlayer, osgeo.ogr.Layer):
                lyr = ds.GetLayer()
        else:
	        lyr = vectorlayer
      
	fieldList = vf.getFields(lyr)
	if field in fieldList:
		i = fieldList.index(field)
		fieldTypeCode = inLayerDefn.GetFieldDefn(i).GetType()
		fieldType = inLayerDefn.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode)
		values = vf.ListValueFields(vectorlayer, field)
                if fieldType != "String":
			for v in values:
                                if isinstance(value, float) or isinstance(value, int) or isinstance(value, str): 
                                        value = [float(value)]
                                else:
                                        value = list(map(float, value))                                
                                if float(v) in value:
				        lyr.SetAttributeFilter(field + "=" + str(v))
				        vf.CreateNewLayer(lyr, opath)
				        lyr.SetAttributeFilter(None)
                                else:
                                        print "the value {} does not exist, vector file not created".format(v)
		else:
			for v in values:
                                if v in value:
				        lyr.SetAttributeFilter(field + "=\'" + v + "\'")
                                        print opath
				        vf.CreateNewLayer(lyr, opath)
				        lyr.SetAttributeFilter(None)
                                else:
                                        print "the value {} does not exist, vector file not created".format(v)                                        
	else:
		print "Field %s does not exist" %field
		sys.exit(-1)
                

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Create polygon file" \
        "for each field value of an input shapefile")
        parser.add_argument("-s", dest="shapefile", action="store", \
                            help="Input shapefile", required = True)
        parser.add_argument("-f", dest="field", action="store", \
                            help="Field to explore", required = True)
        parser.add_argument("-v", dest="value", action="store", \
                            help="list of values of the given field", required = True)        
        parser.add_argument("-o", dest="outpath", action="store", \
                            help="ESRI Shapefile output filename and path", required = True)
	args = parser.parse_args()
        FileByClass(args.shapefile, args.field, args.value, args.outpath)


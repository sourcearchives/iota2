#!/usr/bin/python

import gdal, ogr, osr, numpy
import sys
from sys import argv
import os
import argparse

def deleteField(shapefile, field):
        shp = ogr.Open(shapefile, 1)
        lyr = shp.GetLayer()
        lyr_defn = lyr.GetLayerDefn()
        field_names = [lyr_defn.GetFieldDefn(i).GetName() for i in range(lyr_defn.GetFieldCount())]
        if field in field_names:
	        i = field_names.index(field)
	        lyr.DeleteField(i)

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Delete a field " \
        "of an input shapefile")
        parser.add_argument("-s", dest="shapefile", action="store", \
                            help="Input shapefile", required = True)
        parser.add_argument("-f", dest="field", action="store", \
                            help="Field to delete", required = True)
	args = parser.parse_args()
        deleteField(args.shapefile, args.field)

#!/usr/bin/python

from osgeo import ogr
import sys
import argparse

def addFieldArea(filein, sizepix):
	source = ogr.Open(filein, 1)
	layer = source.GetLayer()
	layer_defn = layer.GetLayerDefn()
	field_names = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]
	if 'Area' in field_names or 'area' in field_names:
                if 'Area' in field_names:
		        i = field_names.index('Area')
		        layer.DeleteField(i)
                if 'area' in field_names:
		        i = field_names.index('area')
		        layer.DeleteField(i)                        
	new_field1 = ogr.FieldDefn('Area', ogr.OFTReal)
	layer.CreateField(new_field1)

	for feat in layer:
		if feat.GetGeometryRef():
			geom = feat.GetGeometryRef()
			area = geom.GetArea()
			size = area/int(sizepix)
 		        layer.SetFeature(feat)
    		        feat.SetField("Area", size)
    		        layer.SetFeature(feat)                        

	return 0


if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Add a area field " \
        "of an input shapefile")
        parser.add_argument("-s", dest="shapefile", action="store", \
                            help="Input shapefile", required = True)
        parser.add_argument("-spix", dest="spix", action="store", \
                            help="Pixel size in m2", required = True)
	args = parser.parse_args()
        if addFieldArea(args.shapefile, args.spix) == 0:
                print 'Add of field succeeded!'
                sys.exit(0)

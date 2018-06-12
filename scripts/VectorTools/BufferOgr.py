#!/usr/bin/python


import sys,os
import argparse
from osgeo import ogr
import vector_functions as vf

def bufferPoly(inputfn, outputBufferfn, bufferDist):

    try :
        bufferDist=float(bufferDist)
        inputds = ogr.Open(inputfn)
        inputlyr = inputds.GetLayer()

        shpdriver = ogr.GetDriverByName('ESRI Shapefile')
        if os.path.exists(outputBufferfn):
            shpdriver.DeleteDataSource(outputBufferfn)
        outputBufferds = shpdriver.CreateDataSource(outputBufferfn)
        bufferlyr = outputBufferds.CreateLayer(outputBufferfn, srs = inputlyr.GetSpatialRef(), geom_type=ogr.wkbPolygon)
        featureDefn = bufferlyr.GetLayerDefn()

        # Copy input field
        inLayerDefn = inputlyr.GetLayerDefn()
        for i in range(0, inLayerDefn.GetFieldCount()):
            fieldDefn = inLayerDefn.GetFieldDefn(i)
            bufferlyr.CreateField(fieldDefn)

        for feature in inputlyr:
            ingeom = feature.GetGeometryRef()
            geomBuffer = ingeom.Buffer(bufferDist)
            if geomBuffer.GetArea() != 0:
                outFeature = ogr.Feature(featureDefn)
                outFeature.SetGeometry(geomBuffer)                
                # copy input value
                for i in range(0, featureDefn.GetFieldCount()):
                    outFeature.SetField(featureDefn.GetFieldDefn(i).GetNameRef(), feature.GetField(i))

                bufferlyr.CreateFeature(outFeature)

    except : return False    
    return True

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Apply a buffer of a defined distance"\
        "on features of an input shapefile and create a new shapefile with same attributes")
        parser.add_argument("-s", dest="inshapefile", action="store", \
                            help="Input shapefile", required = True)
        parser.add_argument("-o", dest="outshapefile", action="store", \
                            help="Ouput shapefile", required = True)        
        parser.add_argument("-b", dest="buff", action="store", \
                            help="Buffer size (m)", required = True)
	args = parser.parse_args()
        bufferPoly(args.inshapefile, args.outshapefile, args.buff)

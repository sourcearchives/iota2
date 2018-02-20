#!/usr/bin/python

import os
import glob
import sys
from sys import argv
import vector_functions as vf
from osgeo import ogr

def simplify(infile, outfile, tolerance):

	try:
	        ds=ogr.Open(infile)
	        drv=ds.GetDriver()
	        if os.path.exists(outfile):
	        	drv.DeleteDataSource(outfile)
	        drv.CopyDataSource(ds,outfile)
	        ds.Destroy()
        
	        ds=ogr.Open(outfile,1)
	        lyr=ds.GetLayer(0)
                cpt = 0
	        for i in range(0,lyr.GetFeatureCount()):
	        	feat=lyr.GetFeature(i)
	        	lyr.DeleteFeature(i)
	        	geom=feat.GetGeometryRef()
                        if geom.Simplify(float(tolerance)).GetEnvelope() != (0.0, 0.0, 0.0, 0.0):
	        	        feat.SetGeometry(geom.Simplify(float(tolerance)))
	        	        lyr.CreateFeature(feat)
                        else:
                                cpt += 1
	        ds.Destroy()

                print "Simplification process created %s empty geometry. All these geometries have been deleted"%(cpt)
	except:return False
	return True
 
if __name__=='__main__':
    usage='usage: simplify <infile> <outfile> <tolerance>'
    if len(sys.argv) == 4:
        if simplify(sys.argv[1],sys.argv[2], sys.argv[3]):
            print 'Simplify succeeded!'
            sys.exit(0)
        else:
            print 'Simplify failed!'
            sys.exit(1)
    else:
        print usage
        sys.exit(1)

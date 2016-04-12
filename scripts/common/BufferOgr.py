#!/usr/bin/python

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

import sys,os
from osgeo import ogr
 
def buffer(infile,outfile,buffdist):
    try:
        ds=ogr.Open(infile)
        drv=ds.GetDriver()
        if os.path.exists(outfile):
            drv.DeleteDataSource(outfile)
        drv.CopyDataSource(ds,outfile)
        ds.Destroy()
        
        ds=ogr.Open(outfile,1)
        lyr=ds.GetLayer(0)
        for i in range(0,lyr.GetFeatureCount()):
            feat=lyr.GetFeature(i)
            lyr.DeleteFeature(i)
            geom=feat.GetGeometryRef()
            feat.SetGeometry(geom.Buffer(float(buffdist)))
            lyr.CreateFeature(feat)
        ds.Destroy()
    except:return False
    return True
 
if __name__=='__main__':
    usage='usage: buffer <infile> <outfile> <distance>'
    if len(sys.argv) == 4:
        if buffer(sys.argv[1],sys.argv[2],sys.argv[3]):
            print 'Buffer succeeded!'
            sys.exit(0)
        else:
            print 'Buffer failed!'
            sys.exit(1)
    else:
        print usage
        sys.exit(1)

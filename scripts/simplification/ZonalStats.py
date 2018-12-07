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

import os, sys, argparse
import datetime
import time
import csv
from itertools import groupby
import ogr
import gdal
from skimage.measure import label
from skimage.measure import regionprops
import numpy as np

try:
    from VectorTools import vector_functions as vf
    from Common import Utils
except ImportError:
    raise ImportError('Iota2 not well configured / installed')

def getFidList(vect):
    
    shape = vf.openToRead(vect)
    lyr = shape.GetLayer()
    fidlist = []
    for feat in lyr:
        fidlist.append(feat.GetFID())
        
    return fidlist

def getVectorsList(path):

    listfiles = []
    for root, dirs, files in os.walk(path):
        for filein in files:
            if ".shp" in filein:
                listfiles.append(os.path.join(root, filein))    

    return listfiles

def zonalstats(path, rasters, params, gdalpath = ""):
    
    vector, idval, csvstore = params

    # vector open
    vectorname = os.path.splitext(os.path.basename(vector))[0]
    ds = vf.openToRead(vector)
    lyr = ds.GetLayer()
    lyr.SetAttributeFilter("FID=" + str(idval))
    for feat in lyr:
        geom = feat.GetGeometryRef()
        area = geom.GetArea()
        
    # rasters  creation
    if gdalpath != "" and gdalpath is not None:
        gdalpath = gdalpath + "/"
    else:
        gdalpath = ""

    bands = []
    success = False

    for idx, raster in enumerate(rasters):
        tmpfile = os.path.join(path, 'rast_%s_%s_%s'%(vectorname, str(idval), idx))
        bands.append(tmpfile)
        
        try:
            cmd = '%sgdalwarp -q -overwrite -cutline %s -crop_to_cutline --config GDAL_CACHEMAX 9000 -wm 9000 -wo NUM_THREADS=ALL_CPUS -cwhere "FID=%s" %s %s'%(gdalpath, vector, idval, raster, tmpfile)        
            Utils.run(cmd)
            success = True
        except:
            success = False            
            pass
    
    results_final = []
    if success:
        # analyze raster
        idxband  = 0
        for band in bands:
            if os.path.exists(band):
                idxband += 1
                rastertmp = gdal.Open(band, 0)
                data = rastertmp.ReadAsArray()
                img = label(data)
                listlab = []

                if idxband == 1:
                    res = rastertmp.GetGeoTransform()[1]
                    try:
                        for reg in regionprops(img, data):
                            listlab.append([[x for x in np.unique(reg.intensity_image) if x != 0][0], reg.area])
                    except:
                        elts, cptElts = np.unique(data, return_counts=True)
                        for idx, elts in enumerate(elts):
                            if elts != 0:
                                listlab.append([elts, cptElts[idx]])


                    if len(listlab) != 0:                
                        classmaj = [y for y in listlab if y[1] == max([x[1] for x in listlab])][0][0]
                        posclassmaj = np.where(data==classmaj)
                        results = []

                        for i, g in groupby(sorted(listlab), key = lambda x: x[0]):
                            results.append([i, sum(v[1] for v in g)])

                        sumpix = sum([x[1] for x in results])
                        for elt in [[int(w), round(((float(z) * float(res) * float(res)) /float(sumpix)), 2)] for w, z in results]:
                            results_final.append([idval, 'classif', 'part'] + elt)

                if idxband != 1:
                    if idxband == 2:
                        results_final.append([idval, 'confidence', 'mean', int(classmaj), round(np.mean(data[posclassmaj]), 2)])
                    elif idxband == 3:
                        results_final.append([idval, 'validity', 'mean', int(classmaj), round(np.mean(data[posclassmaj]), 2)])
                        results_final.append([idval, 'validity', 'std', int(classmaj), round(np.std(data[posclassmaj]), 2)])                

                data = img = None

            Utils.run("rm %s"%(band))

            rastertmp = None

        with open(csvstore, 'a') as myfile:
            writer = csv.writer(myfile)
            writer.writerows(results_final)

    else:
        results_final.append([[idval, 'classif', 'part', 0, 0], [idval, 'confidence', 'mean', 0, 0], [idval, 'validity', 'mean', 0, 0],[idval, 'validity', 'std', 0, 0]])
        with open(csvstore, 'a') as myfile:
            writer = csv.writer(myfile)
            writer.writerows(results_final[0])                             
        print "Feature with FID = %s of shapefile %s not treated (maybe its size is too small)"%(idval, vector)
        

def getParameters(vectorpath, csvstorepath):
    
    listvectors = getVectorsList(vectorpath)
    params = []
    if os.path.isdir(vectorpath):
        for vect in listvectors:
            listfid = getFidList(vect)

            csvstore = os.path.join(csvstorepath, "stats_%s"%(os.path.splitext(os.path.basename(vect))[0]))
            if os.path.exists(csvstore):
                os.remove(csvstore)

            for fid in listfid:        
                params.append((vect, fid, csvstore))
    else:
        listfid = getFidList(vectorpath)
        csvstore = os.path.join(csvstorepath, "stats_%s"%(os.path.splitext(os.path.basename(vectorpath))[0]))
        for fid in listfid:        
            params.append((vectorpath, fid, csvstore))

    return params

def computZonalStats(path, inr, shape, csvstore, gdal):

    params = getParameters(shape, csvstore)

    for parameters in params:
        zonalstats(path, inr, parameters, gdal)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        PROG = os.path.basename(sys.argv[0])
        print '      '+sys.argv[0]+' [options]'
        print "     Help : ", PROG, " --help"
        print "        or : ", PROG, " -h"
        sys.exit(-1)
    else:
        USAGE = "usage: %prog [options] "
        PARSER = argparse.ArgumentParser(description="Extract shapefile records")
        PARSER.add_argument("-wd", dest="path", action="store",\
                            help="working dir",\
                            required=True)
        PARSER.add_argument("-inr", dest="inr", nargs ='+',\
                            help="input rasters list (classification, validity and confidence)",\
                            required=True)
        PARSER.add_argument("-shape", dest="shape", action="store",\
                            help="shapefiles path",\
                            required=True)
        PARSER.add_argument("-csvpath", dest="csvpath", action="store",\
                            help="stats output path",\
                            required=True)        
        PARSER.add_argument("-gdal", dest="gdal", action="store",\
                            help="gdal 2.2.4 binaries path (problem of very small features with lower gdal version)", default = "")
        
        args = PARSER.parse_args()

        computZonalStats(args.path, args.inr, args.shape, args.csvpath, args.gdal)

#!/usr/bin/python
#-*- coding: utf-8 -*-

import sys
import os
import argparse
import random
import ogr
from VectorTools import vector_functions as vf
from VectorTools import MergeFiles as mf
from Common import FileUtils as fu

def splitByArea(Areas, folds):
    """function use to split a list and each split tend to the same sum...
    
    Parameters
    ----------
    Areas : list
        contains a list of tuple (int, int)
    folds : int
        number of splits

    Return
    ------
    list
        list of list
    """

    outputfolds = [[] for i in range(folds)]
    Areas = sorted(Areas, key=lambda x: x[1])[::-1]
    while Areas:
        index_rand = random.sample(xrange(folds), folds)
        #to manage the end...
        if len(Areas) <= folds:
            index_rand = random.sample(xrange(len(Areas)), len(Areas))
        for ind in index_rand:
            outputfolds[ind].append(Areas[ind])
        Areas = Areas[folds::]

    totares = []
    for idx, fold in enumerate(outputfolds):
        totares.append((idx + 1, sum([x[1] for x in fold])))

    return outputfolds, totares

def getFidArea(shapefile, classf):

    driver = ogr.GetDriverByName("ESRI Shapefile")
    datasource = driver.Open(shapefile, 0)
    layer = datasource.GetLayer()

    fieldlist = vf.getFields(layer)
    try:
        fieldlist.index(classf)
    except:
        print "The field {} does not exist in the input shapefile".format(classf)
        print "You must choose one of these existing fields : {}".format(' / '.join(fieldlist))
        sys.exit(-1)

    listid = []
    for feat in layer:
        geom = feat.GetGeometryRef()
        if geom is not None:
            listid.append([feat.GetFID(), feat.GetField(classf), geom.GetArea()])

    layer = datasource = None
    return listid

def getFeaturesFolds(features, folds):

    classes = set([y for x, y, z in features])
    statsclasses = []
    for classval in classes:
        areas = [(x, z) for x, y, z in features if y == classval]
        outputfolds, totares = splitByArea(areas, folds)
        statsclasses.append((classval, outputfolds, totares))

    return statsclasses

def extractFeatureFromShape(shapefile, folds, classf, outpath):

    listid = getFidArea(shapefile, classf)
    statsclasses = getFeaturesFolds(listid, folds)
    lyr = os.path.splitext(os.path.basename(shapefile))[0]
    tomerge = []
    for statsclass in statsclasses:
        for idx, fold in enumerate(statsclass[1]):
            outshape = os.path.join(outpath, \
                                    os.path.splitext(os.path.basename(shapefile))[0] \
                                    +  str(statsclass[0]) + str(idx) + '.shp')

            if len(fold) != 0:
                sublistfid = fu.splitList(fold, 1 + int(len(fold) / 1000))
                filterfid = []
                exp = "FID in "
                for chunk in sublistfid:
                    filterfid.append("(" + ",".join([str(currentFID[0]) for currentFID in chunk]) + ")")

                exp += " OR FID in ".join(filterfid)

                os.system('ogr2ogr -overwrite -sql "select * from %s where %s" %s %s '%(lyr, \
                                                                                        exp, \
                                                                                        outshape, \
                                                                                        shapefile))
                tomerge.append([idx, outshape])
                print "subfile %s of classe %s has been produced with an total area of %s"%(outshape,
                                                                                            statsclass[0],
                                                                                            statsclass[2][idx][1])

    listfolds = set(map(lambda x: x[0], tomerge))
    listfilesbyfold = [[x, [y[1] for y in tomerge if y[0] == x]] for x in listfolds]
    for listfiles in listfilesbyfold:
        finalfile = os.path.join(outpath, \
                                 os.path.splitext(os.path.basename(shapefile))[0] \
                                 + str(listfiles[0]) + '.shp')
        mf.mergeVectors(listfiles[1], finalfile)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        PROG = os.path.basename(sys.argv[0])
        print '      '+sys.argv[0]+' [options]'
        print "     Help : ", PROG, " --help"
        print "        or : ", PROG, " -h"
        sys.exit(-1)
    else:
        USAGE = "usage: %prog [options] "
        PARSER = argparse.ArgumentParser(description=\
                                         "Split polygons of each class of a shapefile in n folds")
        PARSER.add_argument("-shape", dest="shape", action="store", \
                            help="Shapefile", required=True)
        PARSER.add_argument("-folds", dest="folds", action="store", type=int, \
                            help="folds number")
        PARSER.add_argument("-field", dest="field", action="store", \
                            help="class field")
        PARSER.add_argument("-outpath", dest="outpath", action="store", \
                            help="outpath to store subsets")

        ARGS = PARSER.parse_args()
        extractFeatureFromShape(ARGS.shape, ARGS.folds, ARGS.field, ARGS.outpath)

#!/usr/bin/python

import os
import glob
import sys
import vector_functions as vf


def modifID(shapefile, fieldID):
	ds = vf.openToWrite(shapefile)
	layer = ds.GetLayer()
	nbFeat = vf.getNbFeat(shapefile)
	i = 1
	for feat in layer:
		feat.SetField(fieldID, i)
		layer.SetFeature(feat)
		i += 1


if __name__=='__main__':
    usage='usage: <infile> <fieldID>'
    if len(sys.argv) == 3:
        if modifID(sys.argv[1],sys.argv[2]) == 0:
            print 'Update of field succeeded!'
            sys.exit(0)
    else:
        print usage
        sys.exit(1)

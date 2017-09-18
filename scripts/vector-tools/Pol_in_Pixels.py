#!/usr/bin/python

import os
import glob
import sys
from sys import argv
import vector_functions as vf


def totalArea(shapefile, sizepix):
	ds = vf.openToRead(shapefile)
	lyr = ds.GetLayer()
	sizeT = 0
	for feat in lyr:
		if feat.GetGeometryRef():
			geom = feat.GetGeometryRef()
			area = geom.GetArea()
			size = (area/int(sizepix))
			sizeT = sizeT + size
	return sizeT

if __name__=='__main__':
	usage= 'usage: <shapefile> <size of pixel>'
	if len(sys.argv) == 3:
		print totalArea(argv[1], argv[2])
	else:
	        print usage
        	sys.exit(1)   

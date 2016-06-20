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

import argparse,os
from collections import defaultdict
import fileUtils as fu

def getModel(pathShapes):

	sort = []
	pathAppVal = fu.FileSearch_AND(pathShapes,True,"seed0",".shp","learn")
	for path in pathAppVal:
		try:
			ind = sort.index((int(path.split("/")[-1].split("_")[-3]),path.split("/")[-1].split("_")[0]))
		except ValueError :
			sort.append((path.split("/")[-1].split("_")[-3],path.split("/")[-1].split("_")[0]))
	
	d = defaultdict(list)
	for k, v in sort:
   		d[k].append(v)
	sort = list(d.items())
	
	return sort #[(RegionNumber,[tile1,tile2,...]),(...),...]

if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(description = "This function link models and their tiles")
	parser.add_argument("-shapesIn",help ="path to the folder which ONLY contains shapes for the classification (learning and validation) (mandatory)",dest = "pathShapes",required=True)
	args = parser.parse_args()

	print getModel(args.pathShapes)



























































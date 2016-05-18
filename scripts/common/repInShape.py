#!/usr/bin/python
#-*- coding: utf-8 -*-
import os,argparse
from config import Config
from osgeo import ogr
from osgeo.gdalconst import *
from collections import Counter
from collections import defaultdict
import numpy as np

def getSeconde(item):
	return item[1]

def getShapeSurface(ShapeF):
	surf = 0.0
	driver = ogr.GetDriverByName("ESRI Shapefile")
	dataSource = driver.Open(shape, 0)
	layer = dataSource.GetLayer()
	for feature in layer:
		geom = feature.GetGeometryRef()
		surf+=geom.GetArea()
	return surf

def repartitionInShape(ShapeF,dataField,resol):
	
	"""
	
	"""
	driver = ogr.GetDriverByName("ESRI Shapefile")
	buff = []#[(class,Area)...]
	buff_statTMP = []
	AllClass = []

	print ShapeF
	dataSource = driver.Open(ShapeF, 0)
	layer = dataSource.GetLayer()
	#get all class in the current shape
	for feature in layer:
		try :
			ind = AllClass.index(feature.GetField(dataField))
		except ValueError:
			AllClass.append(int(feature.GetField(dataField)))

	AllClass.sort()
	for currentClass in AllClass:
		buff.append([currentClass,0.0])

	dataSource = driver.Open(ShapeF, 0)
	layer = dataSource.GetLayer()
	for feature in layer:
		feat = feature.GetField(dataField)
		geom = feature.GetGeometryRef()
		Area = geom.GetArea()
		try:
			ind = AllClass.index(feat)
			if resol != None:
				buff[ind][1]+=float(Area)/(float(resol)*float(resol))
				buff_statTMP.append([feat,float(Area)/(float(resol)*float(resol))])
			else:
				buff[ind][1]+=float(Area)
				buff_statTMP.append([feat,Area])
		except ValueError:
			print "Problem in repartitionClassByTile"

	buff = sorted(buff,key=getSeconde)
	#print "pour chaque classe, sa surface en pixels ou en metre carre"
	#print buff
	
	Allsurf = 0
	for cl, surf in buff:
		Allsurf+=surf
	genStat = []
	for cl, surf in buff:
		genStat.append([cl,float(surf)/float(Allsurf)])
	#print "Stats générales"
	#print genStat

	d = defaultdict(list)
	for k, v in buff_statTMP:
   		 d[k].append(v)

	buff_statTMP = list(d.items())
	buff_stat = []
	for cla, listP in buff_statTMP:
		tmpL = np.asarray(listP)
		sumA = np.sum(tmpL)
		mini=tmpL.min()
		maxi=tmpL.max()
		mean=np.mean(tmpL)
		med=np.median(tmpL)
		
		buff_stat.append([cla,"min : "+str(mini),"max : "+str(maxi),"mean : "+str(mean),"med : "+str(med),"sum : "+str(sumA)])
	#print "stats"
	#print buff_stat
	return buff

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function try to rearrange the repartition tile by model, considering class repartition")

	parser.add_argument("-path.shape",dest = "shape",help ="shape (mandatory)",nargs='+',required=True)
	parser.add_argument("-dataField",dest = "dataField",help ="field of datas (mandatory)",required=True)
	parser.add_argument("--resol",dest = "resol",type = int,help ="resolution",required=False,default=None)
	args = parser.parse_args()

	repartitionInShape(args.shape,args.dataField,args.resol)





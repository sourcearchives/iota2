#!/usr/bin/python

import sys
from sys import argv
import os
import osr
from osgeo import ogr
import random
import string
import vector_functions as vf



#This script is used to select learning and validation polygons taking into account a wanted number of polygons. For example, if one 
#wants 2000 polygons and the original file had 3000 polygons, it will produce a learn file with 2000 polygons keeping the class 
#proportions and a validation file with the other 1000 polygons. It was used for large scale classification as the otb application
#crashed up when the number of polygons is very high


def RandomInSitu(vectorFile, field, nbdraws, opath, perc_learn):

   classes = []
   shapefile = vectorFile
   field = field
   dicoprop = {}
   allFID = []
   nbtirage = nbdraws
   nameshp = shapefile.split('.')
   namefile = nameshp[0].split('/')

   driver = ogr.GetDriverByName("ESRI Shapefile")
   dataSource = driver.Open(shapefile, 0)
   layer = dataSource.GetLayer()

# Count the total features of cropland
   count = float(layer.GetFeatureCount())
   print count
   
# Find the number of polygons by class
   for feature in layer:
       pid = feature.GetFID()
       allFID.append(pid)
       cl =  feature.GetField(field)
       if cl not in classes:
          classes.append(cl)

   for tirage in range(0,nbtirage):
      listallid = []
      for cl in classes:
         listid = []
         layer = dataSource.GetLayer()
         layer.SetAttributeFilter(field+" = "+str(cl))
         featureCount = float(layer.GetFeatureCount())
         polbysel = round(featureCount / (100/float(perc_learn)))
         if polbysel <= 1:
	    polbysel = 1
         #print polbysel
         prop = float((featureCount/count)*100)
         dicoprop[cl] = prop
         for feat in layer:
            _id = feat.GetFID()
            listid.append(_id)
            listid.sort()
         listToChoice = random.sample(listid, int(polbysel))
         #print listToChoice
         for fid in listToChoice:
            listallid.append(fid)  
         #print _id
      listallid.sort()
      #print listallid
      ch = ""
      listFid = []
      for fid in listallid:
         listFid.append("FID="+str(fid))

   #print listFid
      resultA = []
      for e in listFid:
          resultA.append(e)
          resultA.append(' OR ')
      resultA.pop()

      chA =  ''.join(resultA)
      layer.SetAttributeFilter(chA)
      outShapefile = opath+"/"+namefile[-1]+"_seed"+str(tirage)+"_learn.shp"
      vf.CreateNewLayer(layer, outShapefile)

      listValid = []
      for i in allFID:
         if i not in listallid:
            listValid.append(i)

      chV = ""
      listFidV = []
      for fid in listValid:
         listFidV.append("FID="+str(fid))

      resultV = []
      for e in listFidV:
          resultV.append(e)
          resultV.append(' OR ')
      resultV.pop()

      chV =  ''.join(resultV)
      layer.SetAttributeFilter(chV)
      outShapefile2 = opath+"/"+namefile[-1]+"_seed"+str(tirage)+"_val.shp"
      vf.CreateNewLayer(layer, outShapefile2)


if __name__=='__main__':
    usage= 'usage: <infile> <field_containing_class> <opath> <out_nb_polygons> '
    if len(sys.argv) != 6:
    	print usage
	sys.exit(1)
    else:
	infile = argv[1]
	field = argv[2]
        draws = int(argv[3])
	outpath = argv[4]
	outpol = int(argv[5])
	nbfeat = vf.getNbFeat(argv[1])
	if nbfeat < outpol:
		print "WARNING:Number of polygons wanted higher than total of polygons.90-10 percentages will be used"
		perc = 90
	else:
		perc = int((100*float(argv[5]))/nbfeat)
	RandomInSitu(infile, field, draws, outpath, perc)

